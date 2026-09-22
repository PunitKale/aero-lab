"""Typed domain objects. All unspecified vehicle parameters are assumptions."""
from dataclasses import dataclass, asdict
import numpy as np
from .config import CONFIG

@dataclass(frozen=True)
class Setup:
    front_wing_deg: float = 17.5
    rear_wing_deg: float = 20.0
    front_height_m: float = 0.040
    rear_height_m: float = 0.060
    package: str = "standard"

    def validate(self) -> None:
        for key, bounds in CONFIG["bounds"].items():
            v = getattr(self, key)
            if not np.isfinite(v) or not bounds[0] <= v <= bounds[1]:
                raise ValueError(f"{key}={v} outside {bounds}")
        if self.package not in {"standard", "efficient", "high_load"}:
            raise ValueError("Unknown aero package")

    def vector(self) -> list[float]:
        return [getattr(self, k) for k in CONFIG["bounds"]]

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class Weather:
    name: str = "Dry"
    pressure_pa: float = 101325.0
    temperature_k: float = 288.15
    grip: float = 1.0
    headwind_mps: float = 0.0
    crosswind_mps: float = 0.0
    aero_multiplier: float = 1.0
    density_multiplier: float = 1.0
    height_offset_m: float = 0.0

    def validate(self) -> None:
        for k in ("pressure_pa", "temperature_k", "grip", "aero_multiplier", "density_multiplier"):
            if not np.isfinite(getattr(self,k)) or getattr(self,k) <= 0:
                raise ValueError(f"Invalid weather {k}")
        for k in ("headwind_mps","crosswind_mps","height_offset_m"):
            if not np.isfinite(getattr(self,k)):
                raise ValueError(f"Invalid weather {k}")

@dataclass(frozen=True)
class Tyre:
    name: str = "Medium"
    mu: float = 1.60
    wear_per_m: float = 0.000002
    optimal_temp_c: float = 90.0
    load_exponent: float = 0.09
    reference_load_n: float = 2500.0

@dataclass(frozen=True)
class VehicleState:
    speed_mps: float = 0.0
    fuel_kg: float = 10.0
    tyre_wear: float = 0.0
    tyre_temperature_c: float = 85.0
