"""Spatial forward/backward lap solver with periodic flying-lap boundaries."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .config import CONFIG
from .physics import G
from .schemas import VehicleState
from .circuit_model import discretize

@dataclass
class LapResult:
    trace: pd.DataFrame
    segments: pd.DataFrame
    sectors: pd.DataFrame
    summary: dict
    final_state: VehicleState
    warnings: list[str]

def drs_allowed(zone,speed,braking,available=True,eligible=True,yaw=0.,ay=0.):
    """Policy state at a cell; braking always overrides activation."""
    p=CONFIG["drs_policy"]
    return np.asarray(zone,dtype=bool)&available&eligible&(np.asarray(speed)>=p["min_speed_mps"])&~np.asarray(braking,dtype=bool)&(np.abs(yaw)<=p["max_yaw_deg"])&(np.abs(ay)<=p["max_lateral_accel_mps2"])

def simulate_lap(car,track,state=None,step_m=None,drs_available=True,eligible=True,flying=True) -> LapResult:
    """Solve a continuous speed envelope then evolve tyre/fuel state to convergence.

    Quasi-static forces are evaluated at cell-entry speed. Integration is spatial;
    step_m controls accuracy. Standalone segments default through CarModel to a
    fixed initial speed, while flying laps use a periodic velocity condition.
    """
    state=state or VehicleState(speed_mps=40.)
    if state.speed_mps<0 or state.tyre_wear<0 or state.tyre_wear>.65:
        raise ValueError("Invalid initial state")
    cfg=CONFIG["simulation"]
    c=discretize(track,step_m or cfg["step_m"]); n=len(c["dx"]); dx=c["dx"]
    length=dx.sum(); car.update_fuel_state(state.fuel_kg,length)
    fuel=state.fuel_kg-c["distance_m"]*cfg["fuel_kg_per_m"]
    mass=car.calculate_mass(fuel)
    wear=np.full(n,state.tyre_wear); temp=np.full(n,state.tyre_temperature_c)
    v=np.full(n+1,45.); ax=np.zeros(n); previous=np.zeros(n+1)
    drs=np.zeros(n,dtype=bool); converged=False
    for iteration in range(cfg["max_iterations"]):
        limits=car.calculate_corner_speed(c["radius_m"],mass,c["surface_grip"],c["banking_rad"],wear,temp)
        # Reserve lateral capacity for sustaining speed against drag through a corner.
        # This explicit 5% speed reserve avoids assuming full lateral and drive force together.
        limits=np.where(c["radius_m"]>0,limits*.95,limits)
        node_limit=np.r_[np.minimum(limits,np.roll(limits,1)),min(limits[-1],limits[0])]
        if not flying:
            node_limit[0]=state.speed_mps
            node_limit[-1]=limits[-1]
        v=np.minimum(v,node_limit)
        ay=v[:-1]**2*c["curvature"]
        yaw=np.degrees(np.arctan2(car.weather.crosswind_mps,np.maximum(v[:-1]+car.weather.headwind_mps,15)))
        # Use the previous envelope's net deceleration to close DRS before braking.
        drs=drs_allowed(c["zone"],v[:-1],ax<-.05,drs_available,eligible,yaw,ay)
        aero=car.calculate_aero_forces(v[:-1],drs,ax,ay)
        loads=car.wheel_loads(mass,aero,ax,ay,c["banking_rad"])
        cap=car.grip_capacity(loads,wear,temp,c["surface_grip"])
        lateral=mass*np.maximum(ay*np.cos(c["banking_rad"])-G*np.sin(c["banking_rad"]),0)
        # Conservative common friction-circle utilization; axle-aware corner limit above.
        utilization=np.minimum(lateral/np.maximum(cap.sum(-1),1),1.)
        combined=np.sqrt(np.maximum(0.,1-utilization**2))
        engine,gear=car.calculate_engine_force(v[:-1])
        traction=car.calculate_traction_limit(loads,wear,temp,c["surface_grip"])*combined
        rolling=car.p["rolling_coefficient"]*loads.sum(-1)
        resistance=aero["drag_longitudinal_n"]+rolling+mass*G*np.sin(c["grade_rad"])
        acceleration=np.maximum((np.minimum(engine,traction)-resistance)/mass,-4.)
        # Braking capacity evaluated with a self-consistent quasi-static transfer estimate.
        decel=np.full(n,12.)
        for _ in range(5):
            bl=car.wheel_loads(mass,aero,-decel,ay,c["banking_rad"])
            brakes=car.calculate_braking_force(bl,wear,temp,c["surface_grip"])*combined
            decel=(brakes+resistance)/mass
        new=node_limit.copy()
        # Multiple sweeps communicate constraints around the start/finish boundary.
        for _ in range(3):
            if flying: new[0]=min(new[0],new[-1])
            else: new[0]=state.speed_mps
            for i in range(n):
                new[i+1]=min(new[i+1],np.sqrt(max(0.,new[i]**2+2*acceleration[i]*dx[i])))
            if flying: new[-1]=min(new[-1],new[0])
            for i in range(n-1,-1,-1):
                new[i]=min(new[i],np.sqrt(max(0.,new[i+1]**2+2*decel[i]*dx[i])))
        if not flying and new[0]<state.speed_mps-1e-5:
            raise ValueError("Initial speed cannot meet braking/corner constraint")
        if np.any(new[:-1]+new[1:]<.01):
            raise ValueError("Vehicle cannot progress through track")
        new_ax=np.diff(new**2)/(2*dx)
        # Update state in spatial order; slip is an effort proxy, not a calibrated slip model.
        w,t=state.tyre_wear,state.tyre_temperature_c
        new_wear=np.zeros(n); new_temp=np.zeros(n)
        for i in range(n):
            new_wear[i]=w; new_temp[i]=t
            w,t=car.update_tyre_state(dx[i],w,t,loads[i].sum()/(mass[i]*G),abs(new_ax[i])/20,ay[i]/30)
        error=float(np.max(abs(new-v)))
        if error<cfg["speed_tolerance_mps"] and np.max(abs(new_wear-wear))<1e-5:
            v=new; ax=new_ax; wear=new_wear; temp=new_temp; converged=True; break
        # Damp coupled load/DRS changes to prevent alternate-envelope oscillation.
        previous=v.copy(); v=.55*new+.45*v; ax=.55*new_ax+.45*ax
        wear=new_wear; temp=new_temp
    if not converged:
        raise ValueError(f"Lap solver did not converge after {cfg['max_iterations']} iterations (dv={error:.5f})")
    ay=v[:-1]**2*c["curvature"]
    yaw=np.degrees(np.arctan2(car.weather.crosswind_mps,np.maximum(v[:-1]+car.weather.headwind_mps,15)))
    drs=drs_allowed(c["zone"],v[:-1],ax<-.05,drs_available,eligible,yaw,ay)
    aero=car.calculate_aero_forces(v[:-1],drs,ax,ay)
    loads=car.wheel_loads(mass,aero,ax,ay,c["banking_rad"])
    engine,gear=car.calculate_engine_force(v[:-1])
    rolling=car.p["rolling_coefficient"]*loads.sum(-1)
    resist=aero["drag_longitudinal_n"]+rolling+mass*G*np.sin(c["grade_rad"])
    demand=mass*ax+resist
    dt=2*dx/(v[:-1]+v[1:])
    shifts=np.r_[False,gear[1:]!=gear[:-1]]
    # Lumped shift-time loss is reported separately; it is not a resolved clutch transient.
    shift_loss=shifts*cfg["shift_time_s"]
    time=np.cumsum(dt+shift_loss)-(dt+shift_loss)
    warnings=[]
    if np.any(loads<0): warnings.append("wheel_unloading")
    if np.any(loads>CONFIG["constraints"]["max_tyre_load_n"]): warnings.append("maximum_tyre_load")
    if np.max(v)>=cfg["speed_cap_mps"]-.01: warnings.append("speed_cap_reached")
    trace=pd.DataFrame({"sample_index":np.arange(n),"distance_m":c["distance_m"],"step_m":dx,"time_s":time,
        "dt_s":dt+shift_loss,"shift_loss_s":shift_loss,"speed_mps":v[:-1],"exit_speed_mps":v[1:],
        "acceleration_mps2":ax,"lateral_acceleration_mps2":ay,"gear":gear,"drs":drs.astype(int),
        "drs_zone":c["zone"].astype(int),"fuel_kg":fuel,"mass_kg":mass,"tyre_wear":wear,"tyre_temperature_c":temp,
        "engine_force_n":np.maximum(demand,0),"available_engine_force_n":engine,"brake_force_n":np.maximum(-demand,0),
        "rolling_force_n":rolling,"front_tyre_load_n":loads[:,:2].sum(-1),"rear_tyre_load_n":loads[:,2:].sum(-1),
        "max_wheel_load_n":loads.max(-1),"tyre_mu":car.grip_capacity(loads,wear,temp,c["surface_grip"]).sum(-1)/loads.sum(-1),
        "segment_id":c["segment_id"],"sector_id":c["sector_id"],"radius_m":c["radius_m"],**aero})
    trace["front_aero_fraction"]=trace.front_downforce_n/trace.downforce_n
    agg={"dt_s":"sum","speed_mps":"max","step_m":"sum"}
    segments=trace.groupby(["segment_id","sector_id"],as_index=False).agg(agg).rename(columns={"dt_s":"segment_time_s","speed_mps":"top_speed_mps","step_m":"length_m"})
    sectors=segments.groupby("sector_id",as_index=False).agg(sector_time_s=("segment_time_s","sum"))
    summary={"lap_time_s":float(trace.dt_s.sum()),"top_speed_mps":float(v.max()),"fuel_used_kg":float(length*cfg["fuel_kg_per_m"]),
        "tyre_wear_end":float(w),"tyre_wear_delta":float(w-state.tyre_wear),"distance_m":float(length),
        "high_speed_corner_mps":float(trace.loc[trace.radius_m>=90,"speed_mps"].mean()) if (trace.radius_m>=90).any() else 0.,
        "braking_distance_m":float(trace.loc[trace.brake_force_n>1,"step_m"].sum()),
        "mean_downforce_n":float(np.average(trace.downforce_n,weights=trace.dt_s)),"mean_drag_n":float(np.average(trace.drag_n,weights=trace.dt_s)),
        "max_tyre_load_n":float(loads.max()),"solver_iterations":iteration+1,"shift_loss_s":float(shift_loss.sum())}
    return LapResult(trace,segments,sectors,summary,VehicleState(float(v[-1]),car.update_fuel_state(state.fuel_kg,length),float(w),float(t)),warnings)

def simulate_stint(car,track,laps=10,state=None,**kwargs):
    """Carry fuel, wear and temperature from lap to lap."""
    state=state or VehicleState(40.,60.,0.,85.)
    results=[]
    for _ in range(laps):
        result=simulate_lap(car,track,state=state,**kwargs)
        results.append(result); state=result.final_state
    return results

def braking_test(car,initial_speed=80.,target_speed=30.,fuel_kg=10.,dt=.005):
    """Time-domain straight braking reference with axle/bias constraints."""
    if not 0<=target_speed<initial_speed or dt<=0: raise ValueError("Invalid braking test")
    speed=initial_speed; distance=time=0.; mass=car.calculate_mass(fuel_kg); decel=10.
    while speed>target_speed:
        aero=car.calculate_aero_forces(speed,False,ax=-decel)
        loads=car.wheel_loads(mass,aero,-decel)
        brake=car.calculate_braking_force(loads)
        decel=float((brake+aero["drag_n"]+car.p["rolling_coefficient"]*loads.sum())/mass)
        step=min(dt,(speed-target_speed)/decel)
        distance+=speed*step-.5*decel*step*step; time+=step; speed-=decel*step
    return {"braking_distance_m":distance,"braking_time_s":time}
