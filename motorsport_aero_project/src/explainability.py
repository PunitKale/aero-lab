"""Matched sector explanations and finite-difference sensitivity."""
from dataclasses import replace
import pandas as pd
from .schemas import Setup
from .vehicle_model import CarModel
from .config import CONFIG

def sector_comparison(baseline,candidate):
    df=baseline.sectors.merge(candidate.sectors,on="sector_id",suffixes=("_baseline","_candidate"))
    df["delta_s"]=df.sector_time_s_candidate-df.sector_time_s_baseline
    return df

def sensitivity(track,setup):
    """One-at-a-time full-model perturbations; rank absolute lap effect."""
    base=CarModel(setup).simulate_lap(track).summary["lap_time_s"]; rows=[]
    for k,b in CONFIG["bounds"].items():
        span=(b[1]-b[0])*.05
        for sign in [-1,1]:
            value=max(b[0],min(b[1],getattr(setup,k)+sign*span))
            try:
                r=CarModel(replace(setup,**{k:value})).simulate_lap(track)
                rows.append(dict(parameter=k,direction=sign,change=value-getattr(setup,k),delta_s=r.summary["lap_time_s"]-base,status="simulated"))
            except ValueError as e: rows.append(dict(parameter=k,direction=sign,change=value-getattr(setup,k),delta_s=None,status=str(e)))
    return pd.DataFrame(rows)
