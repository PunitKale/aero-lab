"""Independent invariants on the delivered public-geometry/simulation dataset."""
import json
import numpy as np
import pandas as pd
from src.config import ROOT
from src.realtrack.geometry import to_local
from src.realtrack.ingest import load_route

FOLDER=ROOT/'data/processed/realtrack'
CONFIG=json.loads((ROOT/'config/realtrack.json').read_text())

def read(name):return pd.read_csv(FOLDER/f'{name}.csv')

def test_geographic_projection_units_and_axes():
    p=to_local(np.array([[0.,0.],[.001,0.],[0.,.001]]))
    assert np.allclose(p[0],0)
    assert abs(p[1,0]-111.31949)<.001
    assert abs(p[2,1]-110.57428)<.001
    assert abs(p[1,1])<1e-9 and abs(p[2,0])<1e-9

def test_osm_route_is_closed_and_duplicates_removed():
    coords,source=load_route(ROOT/'data/raw/silverstone',CONFIG['circuits'][0])
    assert np.array_equal(coords[0],coords[-1])
    assert source['duplicate_members_removed']>0
    assert 227902927 not in source['ordered_way_ids']
    assert len(source['ordered_way_ids'])==len(set(source['ordered_way_ids']))
    assert source['source_license']=='ODbL-1.0'

def test_geometry_spacing_sector_partition_and_flags():
    t=read('track_points');c=read('circuits').iloc[0];s=read('sectors')
    assert t.track_point_id.is_unique
    assert not t.is_synthetic.any() and t.is_derived.all()
    assert np.allclose(np.diff(t.distance_m),5)
    assert abs(t.step_m.sum()-c.length_m)<1e-8
    assert 0<t.step_m.iloc[-1]<=5
    assert np.isfinite(t.select_dtypes('number')).all().all()
    assert np.allclose(s.start_distance_m.iloc[1:],s.end_distance_m.iloc[:-1])
    assert abs((s.end_distance_m-s.start_distance_m).sum()-c.length_m)<1e-8
    assert set(t.sector_id)==set(s.sector_id)

def test_all_run_kinematics_forces_and_lap_totals():
    f=read('fact_telemetry');runs=read('simulation_runs');setups=read('aero_setups').set_index('setup_id');v=CONFIG['vehicle'];m=v['mass_kg'];q=.5*v['rho_kg_m3']*v['area_m2'];rr=v['rolling_coefficient']*m*9.81
    assert not f.duplicated(['run_id','track_point_id']).any()
    for run in runs.itertuples():
        t=f[f.run_id==run.run_id].sort_values('sample_index');setup=setups.loc[run.setup_id];speed=t.speed_mps.to_numpy();ex=t.exit_speed_mps.to_numpy();v2=(speed**2+ex**2)/2
        assert len(t)==len(read('track_points')) and t.is_synthetic.all()
        assert np.allclose(ex,np.roll(speed,-1),atol=1e-9)
        assert np.allclose(t.dt_s,2*t.step_m/(speed+ex),atol=1e-10)
        assert np.allclose(t.acceleration_mps2,(ex**2-speed**2)/(2*t.step_m),atol=1e-9)
        assert abs(t.dt_s.sum()-run.lap_time_s)<1e-8
        assert np.allclose(t.downforce_n,q*setup.cl_down*v2,atol=1e-8)
        assert np.allclose(t.drag_n,q*setup.cd*v2,atol=1e-8)
        assert np.allclose(t.front_downforce_n+t.rear_downforce_n,t.downforce_n,atol=1e-8)
        assert abs((t.tyre_wear_end-t.tyre_wear).sum()-run.tyre_wear_change)<1e-12
        assert np.all(t.acceleration_mps2>=-v['max_brake_mps2']-1e-6)
        assert np.all(speed**2*abs(t.curvature_1pm)<=v['max_lateral_mps2']+1e-6)
        longitudinal=m*t.acceleration_mps2+t.drag_n+rr
        lateral=m*v2*np.maximum(abs(t.curvature_1pm),np.roll(abs(t.curvature_1pm),-1))
        assert np.all(np.hypot(longitudinal,lateral)<=v['mu']*(m*9.81+t.downforce_n)+1e-3)
        assert np.all(np.maximum(longitudinal,0)*np.maximum(speed,ex)<=v['power_w']+1e-3)

def test_replay_and_powerbi_projection_share_all_paired_samples():
    data=json.loads((FOLDER/'replay.json').read_text());fact=read('fact_telemetry')
    for name,w in data['recommendations'].items():
        for role in ['baseline','candidate']:
            t=data['traces'][name][role];f=fact[fact.run_id==w[role]['run_id']].sort_values('sample_index')
            for key in ['x_m','y_m','distance_m','time_s','dt_s','speed_mps','downforce_n','drag_n','sector_id','tyre_wear']:
                assert np.allclose(t[key],f[key],rtol=0,atol=1e-9)
        assert abs(sum(s['delta_s'] for s in w['sector_comparison'])-w['lap_delta_s'])<1e-9
        grid=[r for r in w['search'] if r['comparison_role']!='baseline']
        assert w['candidate']['lap_time_s']==min(r['lap_time_s'] for r in grid)
