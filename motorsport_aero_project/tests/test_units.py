import numpy as np
import pytest
from src.units import kmh_to_mps,mps_to_kmh,celsius_to_kelvin

def test_round_trip():
    assert float(kmh_to_mps(180))==50
    assert float(mps_to_kmh(50))==180
    assert celsius_to_kelvin(0)==273.15

@pytest.mark.parametrize('value',[-1,np.nan,np.inf])
def test_invalid_speed(value):
    with pytest.raises(ValueError): kmh_to_mps(value)

def test_absolute_zero():
    with pytest.raises(ValueError): celsius_to_kelvin(-273.15)
