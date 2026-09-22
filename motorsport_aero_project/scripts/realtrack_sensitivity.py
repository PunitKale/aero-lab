"""Fixed-setup 5 m vs 2.5 m comparison; no refitting or measured validation."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.realtrack.geometry import process_geometry
from src.realtrack.ingest import load_route
from src.realtrack.model import simulate
c=json.loads((ROOT/'config/realtrack.json').read_text());r=json.loads((ROOT/'data/processed/realtrack/replay.json').read_text());results=[]
for circuit in c['circuits']:
    name=circuit['name'];ll,source=load_route(ROOT/'data/raw'/circuit['slug'],circuit)
    t,s,m=process_geometry(ll,circuit,c['sample_spacing_m']/2,c['smoothing_sigma_m']);runs=[]
    for role,setup in [('baseline',c['baseline']),('candidate',r['recommendations'][name]['setup'])]:
        trace,result=simulate(t,setup,c['vehicle']);runs.append({'role':role,'production_s':r['recommendations'][name][role]['lap_time_s'],'finer_mesh_s':result['lap_time_s']})
    results.append({'circuit':name,'dataset_id':r['recommendations'][name]['dataset_id'],'production_spacing_m':c['sample_spacing_m'],'finer_spacing_m':c['sample_spacing_m']/2,'runs':runs,'production_delta_s':r['recommendations'][name]['lap_delta_s'],'finer_delta_s':runs[1]['finer_mesh_s']-runs[0]['finer_mesh_s']})
result={'circuits':results,'note':'Same baseline/candidate, no retuning. Numerical sensitivity only, not measured validation or a confidence interval.'}
(ROOT/'data/processed/realtrack/mesh_sensitivity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
from src.realtrack.dashboard import build_dashboard
build_dashboard(r)
