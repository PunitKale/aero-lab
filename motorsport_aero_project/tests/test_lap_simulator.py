import numpy as np
import pytest
from src.vehicle_model import CarModel
from src.circuit_model import circuits
from src.schemas import VehicleState,Weather
from src.lap_simulator import drs_allowed,simulate_stint,braking_test
from src.validation import validate_trace

@pytest.fixture(scope='module')
def lap(): return CarModel().simulate_lap(circuits()['Apex Ring'])

def test_invariants(lap):
    assert all(c['passed'] for c in validate_trace(lap))
    assert abs(lap.trace.speed_mps.iloc[0]-lap.trace.exit_speed_mps.iloc[-1])<1e-6

def test_drs_policy():
    assert not drs_allowed(False,80,False)
    assert not drs_allowed(True,80,True)
    assert not drs_allowed(True,80,False,False)
    assert drs_allowed(True,80,False)
    assert not drs_allowed(True,80,False,yaw=9)

def test_repeated_results(lap):
    again=CarModel().simulate_lap(circuits()['Apex Ring'])
    assert lap.summary==again.summary

def test_drs_gain_and_unavailable(lap):
    off=CarModel().simulate_lap(circuits()['Apex Ring'],drs_available=False)
    ineligible=CarModel().simulate_lap(circuits()['Apex Ring'],eligible=False)
    assert off.summary==ineligible.summary
    assert off.summary['lap_time_s']>lap.summary['lap_time_s']

def test_stint_state():
    rs=simulate_stint(CarModel(),circuits()['Apex Ring'],laps=2)
    assert rs[1].trace.fuel_kg.iloc[0]==rs[0].final_state.fuel_kg
    assert rs[1].trace.tyre_wear.iloc[0]==rs[0].final_state.tyre_wear
    assert rs[1].final_state.tyre_wear>rs[0].final_state.tyre_wear

def test_fuel_exhaustion():
    with pytest.raises(ValueError): CarModel().simulate_lap(circuits()['Apex Ring'],state=VehicleState(fuel_kg=.1))

def test_mesh_convergence(lap):
    fine=CarModel().simulate_lap(circuits()['Apex Ring'],step_m=5)
    assert abs(fine.summary['lap_time_s']/lap.summary['lap_time_s']-1)<.002
    assert abs(fine.summary['top_speed_mps']/lap.summary['top_speed_mps']-1)<.005

def test_braking_convergence():
    a=braking_test(CarModel(),dt=.01); b=braking_test(CarModel(),dt=.005)
    assert a['braking_distance_m']==pytest.approx(b['braking_distance_m'],rel=.002)

def test_wet_slower(lap):
    wet=CarModel(weather=Weather(grip=.68)).simulate_lap(circuits()['Apex Ring'])
    assert wet.summary['lap_time_s']>lap.summary['lap_time_s']

def test_engine_force_capacity(lap):
    assert np.max(lap.trace.engine_force_n-lap.trace.available_engine_force_n)<25
