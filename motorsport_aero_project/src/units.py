"""Explicit SI conversion. Signed speeds are not accepted."""
import numpy as np

def nonnegative(value, name: str):
    """Reject missing, infinite and negative physical magnitudes."""
    a = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(a)) or np.any(a < 0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return a

def kmh_to_mps(value):
    return nonnegative(value, "speed") / 3.6

def mps_to_kmh(value):
    return nonnegative(value, "speed") * 3.6

def celsius_to_kelvin(value: float) -> float:
    result = float(value) + 273.15
    if not np.isfinite(result) or result <= 0:
        raise ValueError("Temperature must exceed absolute zero")
    return result
