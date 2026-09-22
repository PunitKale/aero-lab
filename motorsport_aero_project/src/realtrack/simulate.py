"""Extended simulation with full parameter control for the interactive API.

All force equations are simplified quasi-static estimates:
- Downforce = 0.5 * rho * v^2 * area * Cl
- Drag = 0.5 * rho * v^2 * area * Cd
- Cl derived from wing angles, ride height, and diffuser efficiency
- Cd derived from wing angles
- Corner speed from lateral grip, downforce, and curvature

Not CFD or official telemetry. All values are model estimates.
"""
from typing import Dict, Any, List, Tuple
from . import model

def validate_params(setup: Dict[str, float], vehicle: Dict[str, Any], weather: Dict[str, float]) -> List[str]:
    errors = []
    if not (10 <= setup.get('front_wing_deg', 0) <= 25): errors.append("front_wing_deg must be between 10 and 25")
    if not (10 <= setup.get('rear_wing_deg', 0) <= 30): errors.append("rear_wing_deg must be between 10 and 30")
    if not (0.025 <= setup.get('front_height_m', 0) <= 0.055): errors.append("front_height_m must be between 0.025 and 0.055")
    if not (0.04 <= setup.get('rear_height_m', 0) <= 0.085): errors.append("rear_height_m must be between 0.04 and 0.085")
    if not (0.5 <= setup.get('diffuser_efficiency', 0) <= 1.0): errors.append("diffuser_efficiency must be between 0.5 and 1.0")

    if not (700 <= vehicle.get('mass_kg', 0) <= 900): errors.append("mass_kg must be between 700 and 900")
    if not (5 <= vehicle.get('fuel_kg', 0) <= 110): errors.append("fuel_kg must be between 5 and 110")
    if vehicle.get('tyre_compound') not in ['soft', 'medium', 'hard']: errors.append("tyre_compound must be soft, medium, or hard")

    if not (-10 <= weather.get('air_temperature_c', 0) <= 50): errors.append("air_temperature_c must be between -10 and 50")
    if not (0 <= weather.get('track_temperature_c', 0) <= 70): errors.append("track_temperature_c must be between 0 and 70")
    if not (0 <= weather.get('wind_speed_mps', 0) <= 40): errors.append("wind_speed_mps must be between 0 and 40")
    if not (0 <= weather.get('wind_direction_deg', 0) <= 360): errors.append("wind_direction_deg must be between 0 and 360")

    return errors

def simulate_interactive(track, setup_params: Dict[str, float], vehicle_params: Dict[str, Any], weather_params: Dict[str, float]) -> Tuple[Any, Any]:
    v_total_mass = vehicle_params.get('mass_kg', 820) + vehicle_params.get('fuel_kg', 10)
    tyre = vehicle_params.get('tyre_compound', 'medium')
    mu = {'soft': 1.68, 'medium': 1.55, 'hard': 1.52}.get(tyre, 1.55)
    
    temp_k = weather_params.get('air_temperature_c', 15) + 273.15
    pressure_pa = 101325
    rho = pressure_pa / (287.05 * temp_k)

    vehicle = {
        'mass_kg': v_total_mass,
        'mu': mu,
        'rho_kg_m3': rho,
        'area_m2': 1.5,
        'rolling_coefficient': 0.015,
        'max_speed_mps': 100.0,
        'power_w': 750000.0,
        'max_lateral_mps2': 50.0,
        'max_brake_mps2': 50.0
    }
    
    cand_df, cand_metrics = model.simulate(track, setup_params, vehicle)
    
    base_setup = {
        'front_wing_deg': 16.0,
        'rear_wing_deg': 20.0,
        'front_height_m': 0.04,
        'rear_height_m': 0.06,
        'diffuser_efficiency': 0.85
    }
    base_df, base_metrics = model.simulate(track, base_setup, vehicle)

    return (cand_df, cand_metrics), (base_df, base_metrics)
