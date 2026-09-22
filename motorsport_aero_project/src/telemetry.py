"""DRS event extraction and trace checks."""
import pandas as pd

def drs_events(trace: pd.DataFrame) -> pd.DataFrame:
    """One row per contiguous activation; all values originate in simulation."""
    rows=[]; group=(trace.drs!=trace.drs.shift()).cumsum()
    for _,g in trace.groupby(group):
        if not g.drs.iloc[0]: continue
        rows.append(dict(start_time_s=float(g.time_s.iloc[0]),end_time_s=float(g.time_s.iloc[-1]+g.dt_s.iloc[-1]),
            start_distance_m=float(g.distance_m.iloc[0]),end_distance_m=float(g.distance_m.iloc[-1]+g.step_m.iloc[-1]),
            entry_speed_mps=float(g.speed_mps.iloc[0]),exit_speed_mps=float(g.exit_speed_mps.iloc[-1])))
    return pd.DataFrame(rows,columns=["start_time_s","end_time_s","start_distance_m","end_distance_m","entry_speed_mps","exit_speed_mps"])
