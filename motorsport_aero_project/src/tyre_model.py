"""Simplified load-sensitive tyre model; no measured calibration."""
import numpy as np

def friction(tyre, vertical_load, wear=0., temperature_c=90., surface_grip=1.):
    """Per-tyre friction with explicit load, temperature and degradation multipliers."""
    load = np.asarray(vertical_load)
    thermal = np.exp(-((np.asarray(temperature_c)-tyre.optimal_temp_c)/65)**2)
    return tyre.mu * (np.maximum(load,1.)/tyre.reference_load_n)**(-tyre.load_exponent)*thermal*(1-np.minimum(wear,.65))*surface_grip

def evolve(tyre, distance_m, wear, temperature_c, load_ratio=1., slip_ratio=0., lateral_ratio=0.):
    """Distance-based state update; thermal target is an assumed energy proxy."""
    work = max(float(load_ratio),.1)**1.15*(1+.3*abs(slip_ratio)+.15*abs(lateral_ratio))
    new_wear = min(.65,wear+tyre.wear_per_m*distance_m*work)
    target = tyre.optimal_temp_c + 10*(work-1)
    temp = temperature_c+(target-temperature_c)*(1-np.exp(-distance_m/3000))
    return new_wear,float(temp)
