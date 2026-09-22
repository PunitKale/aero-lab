"""Local same-origin dashboard + JSON API: python -m src.realtrack.api --port 8765."""
import re
import copy
import gzip
import time
import argparse
import hashlib
import json
import math
import threading
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import numpy as np
from ..config import ROOT
from .geometry import process_geometry
from .dynamic_model import simulate
from .dashboard_view import render_dashboard
from .comparison import enrich

CATALOGUE=json.loads((ROOT/'config/circuits.json').read_text(encoding='utf-8'))
DEFAULTS={'front_wing_deg':16.,'rear_wing_deg':20.,'front_height_m':.04,'rear_height_m':.06,'diffuser_efficiency':1.,'mass_kg':820.,'tyre_compound':'medium','fuel_load_kg':30.,'air_temperature_c':20.,'track_temperature_c':30.,'wind_speed_mps':0.,'wind_direction_deg':0.}
# All ranges are educational model bounds, not engineering operating limits.
FIELDS={'front_wing_deg':(0,40,.5,'Front wing (°)'), 'rear_wing_deg':(0,40,.5,'Rear wing (°)'),
 'front_height_m':(.02,.10,.001,'Front ride height (m)'), 'rear_height_m':(.02,.12,.001,'Rear ride height (m)'),
 'diffuser_efficiency':(.5,1.3,.01,'Diffuser efficiency'), 'mass_kg':(600,1100,1,'Vehicle mass, excluding fuel (kg)'),
 'fuel_load_kg':(0,110,1,'Fuel load (kg)'), 'air_temperature_c':(-10,45,1,'Air temperature (°C)'),
 'track_temperature_c':(0,65,1,'Track temperature (°C)'), 'wind_speed_mps':(0,20,.5,'Wind speed (m/s)'),
 'wind_direction_deg':(0,360,1,'Wind from (° clockwise from north)')}
COMPOUNDS={'soft':(1.65,1.3),'medium':(1.55,1.),'hard':(1.45,.75)}
WEATHER=('air_temperature_c','track_temperature_c','wind_speed_mps','wind_direction_deg')

def validate_parameters(values):
    if not isinstance(values,dict):raise ValueError('parameters must be an object')
    unknown=set(values)-set(DEFAULTS)
    if unknown:raise ValueError('Unknown parameters: '+', '.join(sorted(unknown)))
    result={**DEFAULTS,**values}
    for key,(lo,hi,_,_) in FIELDS.items():
        v=result[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
            raise ValueError(f'{key} must be a finite number between {lo} and {hi}')
        result[key]=float(v)
    if not isinstance(result['tyre_compound'],str) or result['tyre_compound'] not in COMPOUNDS:raise ValueError('tyre_compound must be soft, medium or hard')
    return result

@lru_cache(maxsize=8)
def geometry(circuit_id,spacing=5.):
    circuit=next((c for c in CATALOGUE['circuits'] if c['id']==circuit_id),None)
    if circuit is None:raise ValueError('Unknown circuit_id; use GET /api/circuits')
    track,sectors,meta=process_geometry(np.array(circuit['centerline_lonlat']),{k:v for k,v in circuit.items() if k!='sector_boundaries'},spacing=spacing)
    return circuit,track,sectors,meta

@lru_cache(maxsize=16)
def cached_lap(cid,parameters_json,revision,spacing):
    """Bounded exact-input cache. Revision includes source and solver code hashes.

    Never hand mutable cached objects to callers: run_request copies them.
    """
    circuit,track,_,_=geometry(cid,spacing)
    track=track.copy();track['data_source']=circuit['source']['data_source']+'; smoothed derived geometry'
    params=json.loads(parameters_json)
    grip,wear=COMPOUNDS[params['tyre_compound']]
    vehicle={'mass_kg':params['mass_kg']+params['fuel_load_kg'],'power_w':480000.,'mu':grip*max(.75,1-.00025*(params['track_temperature_c']-30)**2),
      'rho_kg_m3':101325/(287.05*(params['air_temperature_c']+273.15)), 'area_m2':1.5,'rolling_coefficient':.015,
      'max_brake_mps2':28.,'max_lateral_mps2':39.24,'max_speed_mps':95.,'wear_multiplier':wear*(1+.01*abs(params['track_temperature_c']-30)),
      'wind_speed_mps':params['wind_speed_mps'],'wind_direction_deg':params['wind_direction_deg']}
    telemetry,summary=simulate(track,params,vehicle)
    trace=telemetry.merge(track.drop(columns=['is_synthetic','data_source']),on='track_point_id',validate='one_to_one')
    return trace.to_dict('list'),summary,vehicle

def run_request(body,spacing=5.):
    started=time.perf_counter();hits_before=cached_lap.cache_info().hits
    if not isinstance(body,dict) or set(body)-{'circuit_id','parameters','centerline_lonlat'}:raise ValueError('Expected circuit_id, parameters and optional centerline_lonlat')
    cid=body.get('circuit_id','silverstone')
    if not isinstance(cid,str):raise ValueError('circuit_id must be a string')
    circuit,track,sectors,meta=geometry(cid,spacing)
    track=track.copy();track['data_source']=circuit['source']['data_source']+'; smoothed derived geometry'
    # Optional geometry is checked against the attributed catalogue. This prevents
    # arbitrary unbounded paths and accidental loss of real-source attribution.
    if 'centerline_lonlat' in body and body['centerline_lonlat']!=circuit['centerline_lonlat']:
        raise ValueError('centerline_lonlat must match the selected catalogue circuit; add new geometry through the catalogue builder')
    candidate=validate_parameters(body.get('parameters',{}))
    baseline={**DEFAULTS,**{k:candidate[k] for k in WEATHER}}
    model_code=''.join((ROOT/'src/realtrack'/file).read_text(encoding='utf-8') for file in ['api.py','dynamic_model.py','geometry.py'])
    revision=hashlib.sha256((model_code+circuit['source']['snapshot_sha256']).encode()).hexdigest()
    digest=hashlib.sha256((json.dumps([cid,candidate,circuit['source'],spacing],sort_keys=True)+model_code).encode()).hexdigest()
    traces={};summaries={};name=circuit['name']
    for role,params in [('baseline',baseline),('candidate',candidate)]:
        trace_values,summary,vehicle=cached_lap(cid,json.dumps(params,sort_keys=True),revision,spacing)
        traces[role]=copy.deepcopy(trace_values)
        summary=copy.deepcopy(summary);vehicle=copy.deepcopy(vehicle)
        summaries[role]={**summary,'run_id':digest[:10]+'-'+role,'comparison_role':role,'parameters':params,'vehicle_assumptions':vehicle,'model_version':'interactive-2.0','is_synthetic':True}
    comparisons=[]
    for sid in sectors.sector_id:
        times={r:sum(dt for dt,s in zip(t['dt_s'],t['sector_id']) if s==sid) for r,t in traces.items()}
        comparisons.append({'sector_id':int(sid),'sector_time_s_baseline':times['baseline'],'sector_time_s_candidate':times['candidate'],'delta_s':times['candidate']-times['baseline']})
    result=enrich({'baseline_setup':baseline,'numerical_sensitivity':{},'recommendations':{name:{'setup':candidate,**summaries,
      'lap_delta_s':summaries['candidate']['lap_time_s']-summaries['baseline']['lap_time_s'],'sector_comparison':comparisons,'search':list(summaries.values()),'dataset_id':digest}},
      'traces':{name:traces},'geometry':{name:{'points':track[['distance_m','x_m','y_m']].values.tolist(),'length_m':meta['length_m'],'source':circuit['source'],'metadata':meta,'sectors':sectors.to_dict('records')}},
      'disclaimer':'Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.'})
    result['metadata']['execution']={'elapsed_ms':round((time.perf_counter()-started)*1000,1),'reused_laps':cached_lap.cache_info().hits-hits_before,'cache_capacity_laps':16}
    return result

def verify_request(body):
    """Two-resolution consistency check, never a measured accuracy interval."""
    coarse=run_request(body,5.);fine=run_request(body,2.5)
    name=next(iter(coarse['recommendations']));a=coarse['recommendations'][name];b=fine['recommendations'][name]
    classify=lambda delta:0 if abs(delta)<.0005 else (-1 if delta<0 else 1)
    shifts={role:b[role]['lap_time_s']-a[role]['lap_time_s'] for role in ['baseline','candidate']}
    agrees=classify(a['lap_delta_s'])==classify(b['lap_delta_s'])
    swing=abs(b['lap_delta_s']-a['lap_delta_s'])
    resolved=agrees and min(abs(a['lap_delta_s']),abs(b['lap_delta_s']))>swing+.0005
    same=not a['comparison']['changes']
    return {'dataset_id':a['dataset_id'],'production_spacing_m':5.,'finer_spacing_m':2.5,
      'production_delta_s':a['lap_delta_s'],'finer_delta_s':b['lap_delta_s'],'lap_shift_s':shifts,
      'production_laps_s':{r:a[r]['lap_time_s'] for r in shifts},'finer_laps_s':{r:b[r]['lap_time_s'] for r in shifts},
      'winner_agrees':agrees,'ranking_resolved':resolved,'identical_setups':same,
      'assessment':'Identical setups' if same else ('Ranking consistent in this check' if resolved else 'Inconclusive: ranking or gain is sensitive to spacing'),
      'disclaimer':'A two-resolution numerical check only. Not experimental validation, a confidence interval, or proof of convergence. Aero, grip and vehicle assumptions remain uncalibrated.'}

SIMULATION_LOCK=threading.BoundedSemaphore(1)
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'reports'),**kwargs)
    def list_directory(self,path):self.send_error(403,'Directory listing disabled')
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
    def respond(self,status,data):
        payload=json.dumps(data,allow_nan=False,separators=(',',':')).encode()
        accepts=self.headers.get('Accept-Encoding','')
        use_gzip=any(part.strip().split(';')[0]=='gzip' and not re.search(r'(?:^|;)\s*q\s*=\s*0(?:\.0*)?\s*(?:;|$)',part) for part in accepts.split(','))
        if use_gzip:payload=gzip.compress(payload,compresslevel=1)
        self.send_response(status);self.send_header('Content-Type','application/json')
        self.send_header('Vary','Accept-Encoding')
        if use_gzip:self.send_header('Content-Encoding','gzip')
        self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path in ('/','/reports/dashboard','/reports/dashboard.html','/dashboard.html'):
            # Python owns the dashboard view. Retain the old URL as a compatible
            # route so existing links and relative browser assets keep working.
            if path=='/':
                self.send_response(302);self.send_header('Location','/reports/dashboard');self.end_headers();return
            payload=render_dashboard().encode('utf-8')
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
        if path=='/api/circuits':return self.respond(200,{**CATALOGUE,'defaults':DEFAULTS,'fields':FIELDS,'compounds':list(COMPOUNDS)})
        if path.startswith('/api/'):return self.respond(404,{'error':'Unknown API endpoint'})
        # Serve only browser assets. Never expose .env or private project files.
        if path.startswith('/reports/'):self.path=self.path[len('/reports'):]
        if path=='/':self.path='/dashboard.html'
        super().do_GET()
    def do_POST(self):
        if urlsplit(self.path).path not in ('/api/simulate','/api/verify'):return self.respond(404,{'error':'Unknown API endpoint'})
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=self.headers.get('Host'):return self.respond(403,{'error':'Use the same-origin local dashboard'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1000000:raise ValueError('JSON body must be between 1 and 1000000 bytes')
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Content-Type must be application/json')
            body=json.loads(self.rfile.read(length))
            if not SIMULATION_LOCK.acquire(blocking=False):return self.respond(429,{'error':'A simulation is running. Please retry shortly.'})
            try:result=verify_request(body) if urlsplit(self.path).path=='/api/verify' else run_request(body)
            finally:SIMULATION_LOCK.release()
            self.respond(200,result)
        except (ValueError,TypeError,KeyError) as e:self.respond(400,{'error':str(e)})
        except Exception as e:
            self.log_error('Simulation failed: %r',e);self.respond(500,{'error':'Simulation failed; inspect the local server log.'})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    print(f'Aero Lab http://127.0.0.1:{args.port}/reports/dashboard.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
