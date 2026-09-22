"""Reconcile each supported circuit and test independent physical/input invariants."""
import json
import math
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.realtrack.api import run_request,validate_parameters,CATALOGUE,DEFAULTS,FIELDS

@pytest.mark.parametrize('cid',[c['id'] for c in CATALOGUE['circuits']])
def test_all_circuits(cid):
    result=run_request({'circuit_id':cid});name=next(iter(result['traces']))
    rec=result['recommendations'][name];g=result['geometry'][name];t=result['traces'][name]['candidate']
    assert rec['lap_delta_s']==0
    assert sum(t['step_m'])==pytest.approx(g['length_m'])
    assert all(ds==5 for ds in t['step_m'][:-1]) and 0<t['step_m'][-1]<=5
    assert sum(t['dt_s'])==pytest.approx(rec['candidate']['lap_time_s'])
    assert sum(s['sector_time_s_candidate'] for s in rec['sector_comparison'])==pytest.approx(rec['candidate']['lap_time_s'])
    v=np.array(t['speed_mps']);out=np.array(t['exit_speed_mps']);ds=np.array(t['step_m'])
    assert np.allclose(out,np.roll(v,-1))
    assert np.allclose((out*out-v*v)/(2*ds),t['acceleration_mps2'])
    params=rec['candidate']['vehicle_assumptions'];mass=params['mass_kg'];v2=(v*v+out*out)/2
    assert np.allclose(t['downforce_n'],.5*params['rho_kg_m3']*params['area_m2']*rec['candidate']['cl_down']*v2)
    fy=mass*v2*np.abs(t['curvature_1pm']);fx=mass*np.array(t['acceleration_mps2'])+np.array(t['drag_n'])+.015*mass*9.81
    assert np.all(np.hypot(fx,fy)<=params['mu']*(mass*9.81+np.array(t['downforce_n']))*1.001)
    json.dumps(result,allow_nan=False)

@pytest.mark.parametrize('key',list(FIELDS))
def test_numeric_validation(key):
    for value in [float('nan'),float('inf'),True,'20',None,FIELDS[key][0]-1,FIELDS[key][1]+1]:
        with pytest.raises(ValueError):validate_parameters({key:value})

@pytest.mark.parametrize('params',[{'front_wing_deg':24},{'rear_wing_deg':30},{'front_height_m':.07},{'rear_height_m':.1},{'diffuser_efficiency':.6},{'mass_kg':1000},{'fuel_load_kg':100},{'tyre_compound':'hard'},{'air_temperature_c':40},{'track_temperature_c':60},{'wind_speed_mps':10,'wind_direction_deg':90}])
def test_controls_have_model_effect(params):
    r=run_request({'circuit_id':'monza','parameters':params});rec=r['recommendations']['Monza']
    if any(k in params for k in ('air_temperature_c','track_temperature_c','wind_speed_mps')):
        ref=run_request({'circuit_id':'monza'})['recommendations']['Monza']['candidate']['lap_time_s']
    else:ref=rec['baseline']['lap_time_s']
    assert abs(rec['candidate']['lap_time_s']-ref)>1e-5

def test_wind_direction_and_bad_geometry():
    laps=[run_request({'circuit_id':'monaco','parameters':{'wind_speed_mps':12,'wind_direction_deg':d}})['recommendations']['Monaco']['candidate']['lap_time_s'] for d in [0,180]]
    assert abs(laps[0]-laps[1])>1e-5
    for body in [{'circuit_id':'missing'},{'centerline_lonlat':[[0,0]]},{'parameters':{'tyre_compound':'wet'}},{'parameters':{'surprise':1}},[]]:
        with pytest.raises(ValueError):run_request(body)

def test_http_contract():
    import threading
    import urllib.request
    import urllib.error
    from http.server import ThreadingHTTPServer
    from src.realtrack.api import Handler
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        with urllib.request.urlopen(base+'/api/circuits') as r:assert len(json.load(r)['circuits'])==5
        for body in [b'{',b'[]',b'{"parameters":{"mass_kg":0}}',b'{"parameters":{"tyre_compound":[]}}']:
            request=urllib.request.Request(base+'/api/simulate',data=body,headers={'Content-Type':'application/json'})
            with pytest.raises(urllib.error.HTTPError) as exc:urllib.request.urlopen(request)
            assert exc.value.code==400 and json.load(exc.value)['error']
        request=urllib.request.Request(base+'/api/simulate',data=b'{"circuit_id":"monza"}',headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request) as r:assert 'Monza' in json.load(r)['traces']
        with pytest.raises(urllib.error.HTTPError) as exc:urllib.request.urlopen(base+'/.env')
        assert exc.value.code==404
    finally:server.shutdown();server.server_close();thread.join()
