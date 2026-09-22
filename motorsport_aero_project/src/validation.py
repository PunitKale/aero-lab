"""Reusable quality and physical-invariant checks."""
import numpy as np
import pandas as pd

def validate_trace(result) -> list[dict]:
    t=result.trace
    checks={"positive_time":bool((t.dt_s>0).all()),"nonnegative_fuel":bool((t.fuel_kg>=0).all()),
        "aero_sum":bool(np.allclose(t.downforce_n,t.front_downforce_n+t.rear_downforce_n,atol=1e-8)),
        "sector_lap_sum":abs(result.sectors.sector_time_s.sum()-result.summary["lap_time_s"])<1e-6,
        "drs_legal_zone":bool(((t.drs==0)|(t.drs_zone==1)).all()),
        "drs_braking_closed":bool(((t.drs==0)|(t.acceleration_mps2>=-.05)).all()),
        "continuous_speed":bool(np.allclose(t.exit_speed_mps.iloc[:-1],t.speed_mps.iloc[1:],atol=1e-6)),
        "finite_trace":bool(np.isfinite(t.select_dtypes(include="number").to_numpy()).all())}
    return [{"test_name":k,"passed":bool(v),"validation_scope":"synthetic_invariant"} for k,v in checks.items()]

def quality_report(tables):
    rows=[]
    for name,df in tables.items():
        rows.append(dict(table_name=name,row_count=len(df),duplicate_rows=int(df.duplicated().sum()),missing_cells=int(df.isna().sum().sum()),synthetic_percentage=100. if len(df) else None))
    return pd.DataFrame(rows)
