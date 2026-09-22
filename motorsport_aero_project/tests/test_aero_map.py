import pytest
import numpy as np
from src.aero_map import AeroMap,coefficients
from src.schemas import Setup

def test_grid_interpolation():
    setup=Setup(); m=AeroMap(setup)
    assert np.allclose(m.evaluate(.04,.06,0),coefficients(setup,.04,.06,0))

def test_no_extrapolation():
    with pytest.raises(ValueError): AeroMap(Setup()).evaluate(.1,.06)
    with pytest.raises(ValueError): coefficients(Setup(),yaw_deg=25)

def test_drs_changes_rear_and_drag():
    a=coefficients(Setup()); b=coefficients(Setup(),drs=True)
    assert a[0]==b[0] and b[1]<a[1] and b[2]<a[2]
