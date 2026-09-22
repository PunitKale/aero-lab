"""Matched interventions, solver convergence and robust candidate selection."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.config import ROOT
from src.schemas import Setup,VehicleState
from src.circuit_model import circuits
from src.vehicle_model import CarModel
from src.uncertainty import paired_uncertainty

track=circuits()['Apex Ring'];recommendations=json.loads((ROOT/'reports/recommendations.json').read_text());candidate=Setup(**recommendations['Apex Ring']['setup'])
rows=[]
for label,state in [('reference',VehicleState(40,10,0,85)),('heavy_fuel',VehicleState(40,60,0,85)),('worn_tyre',VehicleState(40,10,.15,85))]:
    result=CarModel(candidate).simulate_lap(track,state=state)
    rows.append(dict(scenario=label,initial_fuel_kg=state.fuel_kg,initial_wear=state.tyre_wear,lap_time_s=result.summary['lap_time_s'],circuit_id=2,setup_id=recommendations['Apex Ring']['setup_id']))
frame=pd.DataFrame(rows);frame['delta_from_reference_s']=frame.lap_time_s-frame.lap_time_s.iloc[0];frame.to_csv(ROOT/'data/processed/interventions.csv',index=False)
rows=[]
for step in [40,20,10,5]:
    for label,setup in [('baseline',Setup()),('recommended',candidate)]:
        result=CarModel(setup).simulate_lap(track,step_m=step)
        rows.append(dict(step_m=step,setup=label,lap_time_s=result.summary['lap_time_s'],top_speed_mps=result.summary['top_speed_mps']))
pd.DataFrame(rows).to_csv(ROOT/'reports/convergence.csv',index=False)
robust=[]
for label,setup in [('baseline',Setup()),('qualifying',candidate),('moderate',Setup(19,23,.04,.065))]:
    trials,summary=paired_uncertainty(track,setup,draws=30,seed=242)
    valid=trials.loc[trials.feasible]
    robust.append(dict(candidate=label,**setup.to_dict(),valid_draws=len(valid),draws=30,
        mean_lap_s=valid.candidate_lap_s.mean(),sd_lap_s=valid.candidate_lap_s.std(),robust_objective_s=valid.candidate_lap_s.mean()+valid.candidate_lap_s.std(),feasible_fraction=len(valid)/30))
pd.DataFrame(robust).sort_values(['feasible_fraction','robust_objective_s'],ascending=[False,True]).to_csv(ROOT/'data/processed/robust_selection.csv',index=False)
print('Matched interventions, mesh convergence and 30-draw robust candidate selection complete.')
