import pytest
from src.realtrack.api import cached_lap,run_request,verify_request

def test_exact_cache_reuses_baseline_without_aliasing():
    cached_lap.cache_clear()
    a=run_request({'circuit_id':'monza'})
    assert a['metadata']['execution']['reused_laps']==1
    name='Monza';a['traces'][name]['baseline']['speed_mps'][0]=-100
    b=run_request({'circuit_id':'monza','parameters':{'rear_wing_deg':24}})
    assert b['metadata']['execution']['reused_laps']==1
    c=run_request({'circuit_id':'monza','parameters':{'rear_wing_deg':24}})
    assert c['metadata']['execution']['reused_laps']==2
    assert b['traces']==c['traces']
    assert c['traces'][name]['baseline']['speed_mps'][0]>0
    d=run_request({'circuit_id':'monza','parameters':{'rear_wing_deg':24,'wind_speed_mps':3}})
    assert d['metadata']['execution']['reused_laps']==0

def test_verification_uses_distinct_mesh_and_same_setups():
    check=verify_request({'parameters':{'rear_wing_deg':24}})
    assert check['production_spacing_m']==5 and check['finer_spacing_m']==2.5
    assert check['finer_delta_s']==pytest.approx(check['finer_laps_s']['candidate']-check['finer_laps_s']['baseline'])
    assert abs(check['lap_shift_s']['baseline'])>1e-6
    tie=verify_request({})
    assert tie['identical_setups'] and tie['finer_delta_s']==0
    assert 'Not experimental validation' in tie['disclaimer']
