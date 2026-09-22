"""Scalar and vector force equations; positive Cl means downforce."""
import numpy as np
from .units import nonnegative
G = 9.80665

def air_density(pressure_pa: float, temperature_k: float) -> float:
    """Dry ideal gas density from LOCAL pressure; no second altitude correction."""
    if not np.isfinite(pressure_pa) or not np.isfinite(temperature_k) or pressure_pa <= 0 or temperature_k <= 0:
        raise ValueError("Pressure and Kelvin temperature must be positive")
    return pressure_pa / (287.05 * temperature_k)

def dynamic_pressure(rho: float, speed):
    if not np.isfinite(rho) or rho <= 0:
        raise ValueError("Density must be positive")
    return 0.5 * rho * nonnegative(speed, "air speed") ** 2

def aero_forces(rho: float, speed, area: float, cl_down, cd):
    """Return downforce N and drag N on one consistent reference area."""
    if not np.isfinite(area) or area <= 0:
        raise ValueError("Area must be positive")
    q = dynamic_pressure(rho, speed)
    return q * area * nonnegative(cl_down, "cl_down"), q * area * nonnegative(cd, "cd")

def balance(front, rear):
    front, rear = nonnegative(front,"front load"), nonnegative(rear,"rear load")
    return np.divide(front,front+rear,out=np.full(np.broadcast(front,rear).shape,np.nan),where=(front+rear)>0)

def static_axle_loads(mass: float, front_fraction: float):
    if mass <= 0 or not 0 < front_fraction < 1:
        raise ValueError("Invalid mass or distribution")
    return mass*G*front_fraction, mass*G*(1-front_fraction)

def longitudinal_transfer(mass, acceleration, cg_height, wheelbase):
    return mass * acceleration * cg_height / wheelbase
