"""Simulation-driven constrained search, including Pareto filtering."""
import itertools
from dataclasses import replace
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
from .config import CONFIG
from .schemas import Setup,Weather
from .vehicle_model import CarModel
from .lap_simulator import simulate_stint,braking_test

def constraint_reasons(car,result,baseline_braking=None) -> list[str]:
    """Hard physical/model bounds; all violations are explicit."""
    c=CONFIG["constraints"]; t=result.trace
    reasons=list(result.warnings)
    if min(t.front_height_m.min(),t.rear_height_m.min())<c["min_clearance_m"]: reasons.append("clearance")
    if (t.front_aero_fraction<c["balance_min"]).any() or (t.front_aero_fraction>c["balance_max"]).any(): reasons.append("balance")
    # Matched-state baseline isolates setup-induced balance shift, including DRS.
    base=CarModel(Setup(),car.weather,car.tyre,car.p)
    a=base.calculate_aero_forces(t.speed_mps.to_numpy(),t.drs.to_numpy().astype(bool),t.acceleration_mps2.to_numpy(),t.lateral_acceleration_mps2.to_numpy())
    bal=a["front_downforce_n"]/np.maximum(a["downforce_n"],1e-12)
    if np.max(abs(t.front_aero_fraction.to_numpy()-bal))>c["max_balance_shift"]: reasons.append("balance_shift")
    if float(car.calculate_aero_forces(70.)["drag_n"])>c["max_drag_n_at_70"]: reasons.append("drag_limit")
    if baseline_braking and braking_test(car)["braking_distance_m"]>baseline_braking*c["max_braking_ratio"]: reasons.append("braking_limit")
    return sorted(set(reasons))

def pareto_mask(values: np.ndarray) -> np.ndarray:
    """Non-dominated rows for minimization; equal rows both remain non-dominated."""
    values=np.asarray(values,dtype=float)
    return np.array([not np.any(np.all(values<=v,axis=1)&np.any(values<v,axis=1)) for v in values])

class Evaluator:
    """Cache feasible full-model evaluations and persist rejected candidates."""
    def __init__(self,track,weather=None,objective="qualifying",step_m=25.):
        self.track=track; self.weather=weather or Weather(); self.objective=objective; self.step=step_m
        self.cache={}; self.rows=[]
        self.base_brake=braking_test(CarModel(weather=self.weather))["braking_distance_m"]

    def __call__(self,x,method="search"):
        key=tuple(np.round(x,8))
        if key in self.cache: return self.cache[key]
        setup=Setup(*map(float,x)); row={**setup.to_dict(),"method":method,"objective":self.objective}
        try:
            car=CarModel(setup,self.weather); r=car.simulate_lap(self.track,step_m=self.step)
            reasons=constraint_reasons(car,r,self.base_brake)
            if self.objective=="race":
                stint=simulate_stint(car,self.track,step_m=self.step)
                score=sum(a.summary["lap_time_s"] for a in stint)
                if stint[-1].final_state.tyre_wear>.4: reasons.append("stint_wear")
            elif self.objective=="overtaking": score=-r.summary["top_speed_mps"]
            elif self.objective=="high_downforce": score=-r.summary["high_speed_corner_mps"]
            elif self.objective=="wet":
                scenarios=[CarModel(setup,replace(self.weather,grip=self.weather.grip*g)).simulate_lap(self.track,step_m=self.step).summary["lap_time_s"] for g in [.95,1.,1.05]]
                score=float(np.mean(scenarios)+np.std(scenarios))
            else: score=r.summary["lap_time_s"]
            row.update(r.summary,feasible=not reasons,constraint_reasons=";".join(reasons),objective_value=score)
            cost=score if not reasons else 1e6+len(reasons)*1000
        except ValueError as e:
            row.update(feasible=False,constraint_reasons=str(e),objective_value=None); cost=1e9
        self.rows.append(row); self.cache[key]=cost
        return cost

def optimize(track,seed=42,budget=32,objective="qualifying",weather=None):
    """Baseline, grid, random, differential evolution and bounded local refinement.

    Algorithm budgets are logged as actual unique evaluations; population-based
    DE has its own minimum population and is not falsely reported equal-cost.
    """
    ev=Evaluator(track,weather,objective); bounds=list(CONFIG["bounds"].values())
    ev(Setup().vector(),"baseline")
    grid=list(itertools.product(*[[b[0]+.25*(b[1]-b[0]),b[0]+.75*(b[1]-b[0])] for b in bounds]))
    for x in grid: ev(x,"grid")
    rng=np.random.default_rng(seed)
    for x in rng.uniform(np.array(bounds)[:,0],np.array(bounds)[:,1],size=(budget,4)): ev(x,"random")
    differential_evolution(lambda x:ev(x,"differential_evolution"),bounds,seed=seed,popsize=4,maxiter=2,polish=False,workers=1)
    feasible=[r for r in ev.rows if r["feasible"]]
    if not feasible: raise ValueError("No feasible setup; inspect evaluation log")
    best=min(feasible,key=lambda r:r["objective_value"])
    minimize(lambda x:ev(x,"local"),[best[k] for k in CONFIG["bounds"]],method="Powell",bounds=bounds,options={"maxfev":budget,"xtol":.01,"ftol":.001})
    df=pd.DataFrame(ev.rows); df["pareto"]=False
    ok=df.feasible
    df.loc[ok,"pareto"]=pareto_mask(df.loc[ok,["lap_time_s","tyre_wear_delta","mean_drag_n"]].to_numpy())
    return df.sort_values(["feasible","objective_value"],ascending=[False,True]).reset_index(drop=True)
