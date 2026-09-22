"""Paired scenario uncertainty. Intervals are model-conditional, not calibrated."""
from dataclasses import replace
import numpy as np
import pandas as pd
from .config import CONFIG
from .schemas import Setup,Weather
from .vehicle_model import CarModel
from .optimization import constraint_reasons

def paired_uncertainty(track,candidate,draws=200,seed=142,step_m=25.):
    """Common random inputs for each candidate/baseline pair; invalid draws counted."""
    rng=np.random.default_rng(seed); c=CONFIG["uncertainty"]; rows=[]
    for i in range(draws):
        w=Weather(density_multiplier=rng.uniform(*c["density_range"]),grip=rng.uniform(*c["grip_range"]),
            aero_multiplier=rng.uniform(*c["aero_range"]),headwind_mps=rng.uniform(*c["headwind_range_mps"]),
            crosswind_mps=rng.uniform(*c["crosswind_range_mps"]),height_offset_m=rng.uniform(*c["height_range_m"]))
        row={"scenario_id":i+1,**w.__dict__}
        try:
            rb=CarModel(Setup(),w).simulate_lap(track,step_m=step_m)
            car=CarModel(candidate,w); rc=car.simulate_lap(track,step_m=step_m)
            reasons=constraint_reasons(car,rc)
            row.update(baseline_lap_s=rb.summary["lap_time_s"],candidate_lap_s=rc.summary["lap_time_s"],
                delta_s=rc.summary["lap_time_s"]-rb.summary["lap_time_s"],feasible=not reasons,error=";".join(reasons))
        except ValueError as e: row.update(feasible=False,error=str(e))
        rows.append(row)
    df=pd.DataFrame(rows); valid=df.loc[df.feasible & df.delta_s.notna()] if "delta_s" in df else pd.DataFrame()
    if valid.empty: return df,{"draws":draws,"valid_draws":0,"feasible_fraction":0.}
    delta=valid.delta_s.to_numpy(); half=delta[:len(delta)//2]
    summary={"draws":draws,"valid_draws":len(valid),"feasible_fraction":len(valid)/draws,"mean_delta_s":float(delta.mean()),
        "median_delta_s":float(np.median(delta)),"std_delta_s":float(delta.std(ddof=1)),"p025_delta_s":float(np.quantile(delta,.025)),
        "p975_delta_s":float(np.quantile(delta,.975)),"observed_best_delta_s":float(delta.min()),"observed_worst_delta_s":float(delta.max()),
        "probability_improvement_conditional":float((delta<0).mean()),"probability_feasible_improvement":float((delta<0).sum()/draws),
        "mean_monte_carlo_se_s":float(delta.std(ddof=1)/np.sqrt(len(delta))),"half_full_mean_change_s":float(abs(half.mean()-delta.mean()))}
    return df,summary
