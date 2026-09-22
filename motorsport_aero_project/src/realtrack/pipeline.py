"""python -m src.realtrack.pipeline [--download] [--mysql]"""
import argparse,hashlib,itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from ..config import ROOT
from .ingest import load_route
from .geometry import process_geometry
from .model import simulate,aero_coefficients
from .database import seed_sql,load_mysql,ORDER

def build(download=False,mysql=False):
    config=json.loads((ROOT/'config/realtrack.json').read_text());out=ROOT/'data/processed/realtrack';out.mkdir(parents=True,exist_ok=True)
    accumulated={k:[] for k in ORDER};replay={'recommendations':{},'traces':{},'geometry':{},'baseline_setup':config['baseline']};quality=[]
    for circuit in config['circuits']:
        cid=circuit['circuit_id'];geo,source=load_route(ROOT/'data/raw'/circuit['slug'],circuit,download)
        np.savetxt(ROOT/'data/raw'/circuit['slug']/'centreline_lonlat.csv',geo,delimiter=',',header='longitude,latitude',comments='')
        track,sectors,metadata=process_geometry(geo,circuit,config['sample_spacing_m'],config['smoothing_sigma_m'])
        model_source=''.join((Path(__file__).parent/file).read_text(encoding='utf-8') for file in ['ingest.py','geometry.py','model.py'])
        dataset=hashlib.sha256((source['snapshot_sha256']+json.dumps(config,sort_keys=True)+model_source).encode()).hexdigest()
        circuit_row={k:circuit[k] for k in ['circuit_id','name','slug']};circuit_row.update({k:metadata[k] for k in ['length_m','origin_lon','origin_lat','projection']})
        circuit_row.update({k:source[k] for k in ['source_url','source_license','snapshot_sha256','data_source','is_synthetic']});circuit_row['geometry_version']=f"OSM-v{source['relation_version']}-sigma{config['smoothing_sigma_m']}-ds{config['sample_spacing_m']}"
        accumulated['circuits'].append(pd.DataFrame([circuit_row]));accumulated['track_points'].append(track);accumulated['sectors'].append(sectors)
        setups=[config['baseline']]+[{**config['baseline'],'front_wing_deg':f,'rear_wing_deg':r} for f,r in itertools.product(config['search']['front_wing_deg'],config['search']['rear_wing_deg'])]
        runrows=[];setuprows=[];traces=[]
        for i,setup in enumerate(setups):
            sid=cid*100+i+1;rid=cid*100+i+1;telemetry,summary=simulate(track,setup,config['vehicle'])
            cl,cd=aero_coefficients(setup)
            setuprows.append({'setup_id':sid,'name':'Baseline' if i==0 else f'Grid F{setup["front_wing_deg"]:g} R{setup["rear_wing_deg"]:g}',**setup,'cl_down':cl,'cd':cd,
                'vehicle_parameters':json.dumps(config['vehicle'],sort_keys=True),'data_source':'Assumed parameters; transparent rule-based aero formula','is_synthetic':True})
            runrows.append({'run_id':rid,'circuit_id':cid,'setup_id':sid,'comparison_role':'baseline' if i==0 else 'grid',
                'model_version':config['model_version'],'dataset_id':dataset,**{k:summary[k] for k in ['lap_time_s','max_speed_mps','tyre_wear_change','solver_iterations']},
                'data_source':'Aero Lab model-generated simulation outputs','is_synthetic':True})
            telemetry.insert(0,'run_id',rid);telemetry.insert(2,'circuit_id',cid);traces.append(telemetry)
        best=min(range(1,len(runrows)),key=lambda i:runrows[i]['lap_time_s']);runrows[best]['comparison_role']='candidate'
        accumulated['aero_setups'].append(pd.DataFrame(setuprows));accumulated['simulation_runs'].append(pd.DataFrame(runrows));accumulated['telemetry_points'].extend(traces)
        name=circuit['name'];paired={}
        for role,i in [('baseline',0),('candidate',best)]:
            t=traces[i].merge(track.drop(columns=['circuit_id','is_synthetic','data_source']),on='track_point_id',validate='one_to_one')
            paired[role]=t.to_dict('list')
        comparisons=[]
        for s in sectors.sector_id:
            b=sum(dt for dt,sec in zip(paired['baseline']['dt_s'],paired['baseline']['sector_id']) if sec==s)
            a=sum(dt for dt,sec in zip(paired['candidate']['dt_s'],paired['candidate']['sector_id']) if sec==s)
            comparisons.append({'sector_id':int(s),'sector_time_s_baseline':b,'sector_time_s_candidate':a,'delta_s':a-b})
        replay['recommendations'][name]={'setup':setups[best],'baseline':runrows[0],'candidate':runrows[best],'lap_delta_s':runrows[best]['lap_time_s']-runrows[0]['lap_time_s'],'sector_comparison':comparisons,'search':runrows,'dataset_id':dataset}
        replay['traces'][name]=paired
        replay['geometry'][name]={'points':track[['distance_m','x_m','y_m']].values.tolist(),'length_m':metadata['length_m'],'source':source,'metadata':metadata,'sectors':sectors.to_dict('records')}
        quality.append({'circuit':name,**metadata,'dataset_id':dataset,'source_sha256':source['snapshot_sha256'],'source_warnings':source['source_warnings'],
            'baseline_s':runrows[0]['lap_time_s'],'candidate_s':runrows[best]['lap_time_s'],'delta_s':runrows[best]['lap_time_s']-runrows[0]['lap_time_s']})
    tables={k:pd.concat(v,ignore_index=True) for k,v in accumulated.items()}
    for k,df in tables.items():df.to_csv(out/f'{k}.csv',index=False)
    fact=tables['telemetry_points'].merge(tables['track_points'].drop(columns=['circuit_id','is_synthetic','data_source']),on='track_point_id',validate='many_to_one').merge(tables['simulation_runs'][['run_id','setup_id']],on='run_id',validate='many_to_one')
    fact['speed_kmh']=fact.speed_mps*3.6;fact.to_csv(out/'fact_telemetry.csv',index=False)
    sectors=fact.groupby(['run_id','circuit_id','setup_id','sector_id'],as_index=False).agg(sector_time_s=('dt_s','sum'),sector_distance_m=('step_m','sum'))
    sectors['average_speed_kmh']=sectors.sector_distance_m/sectors.sector_time_s*3.6;sectors.to_csv(out/'fact_sector.csv',index=False)
    for name,df in {'dim_circuit':tables['circuits'],'dim_setup':tables['aero_setups'],'dim_sector':tables['sectors'],
        'dim_run':tables['simulation_runs'][['run_id','comparison_role','model_version','dataset_id']],'fact_lap':tables['simulation_runs']}.items():df.to_csv(out/f'{name}.csv',index=False)
    (out/'replay.json').write_text(json.dumps(replay,allow_nan=False),encoding='utf-8')
    (ROOT/'sql/realtrack_seed.sql').write_text(seed_sql(tables),encoding='utf-8')
    evidence={'geometry':quality,'rows':{k:len(v) for k,v in tables.items()},'mysql':'not executed in this run'}
    # Save current local evidence before an optional external database operation.
    # If MySQL is unavailable, do not leave a stale successful validation record.
    (out/'validation.json').write_text(json.dumps(evidence,indent=2))
    from .dashboard import build_dashboard
    build_dashboard(replay)
    if mysql:
        try:evidence['mysql']=load_mysql(tables)
        except Exception:
            evidence['mysql']='failed: check MySQL service, port, credentials and privileges; local exports are current'
            (out/'validation.json').write_text(json.dumps(evidence,indent=2))
            raise
        (out/'validation.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps({'circuits':quality,'rows':evidence['rows'],'mysql_checks':len(evidence['mysql']) if isinstance(evidence['mysql'],list) else evidence['mysql']},indent=2))
    return tables,replay

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--download',action='store_true');parser.add_argument('--mysql',action='store_true');args=parser.parse_args();build(args.download,args.mysql)
