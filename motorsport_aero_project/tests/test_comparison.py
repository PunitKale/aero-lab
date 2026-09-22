import pytest
from src.realtrack.api import run_request

@pytest.mark.parametrize('params',[{}, {'rear_wing_deg':24,'fuel_load_kg':25,'tyre_compound':'soft'}])
def test_comparison_reconciles(params):
    result=run_request({'circuit_id':'silverstone','parameters':params})
    rec=result['recommendations']['Silverstone Grand Prix'];comp=rec['comparison']
    assert comp['cumulative_delta_s'][0]==0
    assert comp['cumulative_delta_s'][-1]==pytest.approx(rec['lap_delta_s'])
    assert sum(comp['classification_delta_s'].values())==pytest.approx(rec['lap_delta_s'])
    assert sum(s['delta_s'] for s in rec['sector_comparison'])==pytest.approx(rec['lap_delta_s'])
    for role in ['baseline','candidate']:
        t=result['traces']['Silverstone Grand Prix'][role];r=rec[role]
        assert r['average_speed_kmh']==pytest.approx(sum(t['step_m'])/sum(t['dt_s'])*3.6)
        assert r['mean_downforce_n']*r['lap_time_s']==pytest.approx(r['downforce_impulse_ns'])
        assert r['drag_work_j']==pytest.approx(sum(d*s for d,s in zip(t['drag_n'],t['step_m'])))
    if not params:
        assert comp['insights']==['No setup changes detected. Candidate matches baseline.']
        assert comp['winner']=='Tie at displayed precision'
    else:assert set(comp['changes'])==set(params)
    assert result['metadata']['baseline_setup']==result['baseline_setup']
    assert result['metadata']['candidate_setup']==rec['setup']
    assert result['metadata']['timestamp_utc'].endswith('+00:00')
