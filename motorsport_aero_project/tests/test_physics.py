import numpy as np
import pytest
from src.physics import *
from src.vehicle_model import CarModel
from src.schemas import Setup,Weather

def test_analytical_force():
    down,drag=aero_forces(1.225,50,1.5,3,.9)
    assert down==pytest.approx(6890.625,abs=1e-9)
    assert drag==pytest.approx(2067.1875,abs=1e-9)
    assert dynamic_pressure(1.225,50)==1531.25

def test_zero_and_scaling():
    assert aero_forces(1.225,0,1.5,3,.9)==(0,0)
    f1=aero_forces(1.225,30,1.5,3,.9);f2=aero_forces(1.225,60,1.5,3,.9)
    assert np.allclose(np.array(f2),4*np.array(f1))
    assert f2[1]*60==pytest.approx(8*f1[1]*30)

def test_balance_and_static_loads():
    assert float(balance(400,600))==.4
    assert np.isnan(balance(0,0))
    assert sum(static_axle_loads(800,.45))==pytest.approx(800*G)

@pytest.mark.parametrize('rho,area,cl,cd',[(-1,1,1,1),(1,0,1,1),(1,1,-1,1),(1,1,1,np.nan)])
def test_invalid_aero(rho,area,cl,cd):
    with pytest.raises(ValueError): aero_forces(rho,20,area,cl,cd)

def test_load_transfer_conservation():
    car=CarModel(); a=car.calculate_aero_forces(50); l0=car.wheel_loads(810,a); lb=car.wheel_loads(810,a,-10)
    assert lb.sum()==pytest.approx(l0.sum())
    assert lb[:2].sum()>l0[:2].sum()
    assert car.calculate_traction_limit(lb)<car.calculate_traction_limit(l0)

def test_mass_and_drag_acceleration_direction():
    car=CarModel(); f,_=car.calculate_engine_force(70)
    drag=float(car.calculate_aero_forces(70)['drag_n'])
    assert (f-drag)/860<(f-drag)/810
    assert (f-1.1*drag)/810<(f-drag)/810
    assert (f-drag)/car.calculate_mass(5)>(f-drag)/car.calculate_mass(50)

def test_corner_grip_and_downforce():
    base=CarModel(); wet=CarModel(weather=Weather(grip=.65)); high=CarModel(Setup(23,28,.04,.06))
    assert wet.calculate_corner_speed(150)<base.calculate_corner_speed(150)
    assert high.calculate_corner_speed(150)>base.calculate_corner_speed(150)

def test_density_and_invalid_weather():
    assert air_density(101325,288.15)==pytest.approx(1.225,rel=1e-4)
    with pytest.raises(ValueError): air_density(0,288)
    with pytest.raises(ValueError): CarModel(weather=Weather(grip=-1))
