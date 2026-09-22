"""Integrated digital car force interface. Quasi-static wheel loads."""
import numpy as np
from .config import CONFIG
from .physics import G,air_density,aero_forces
from .aero_map import coefficients
from .tyre_model import friction,evolve
from .schemas import Setup,Weather,Tyre

class CarModel:
    """Configurable rear-wheel-drive synthetic vehicle."""
    def __init__(self,setup=None,weather=None,tyre=None,parameters=None):
        self.setup=setup or Setup(); self.setup.validate()
        self.weather=weather or Weather(); self.weather.validate()
        self.tyre=tyre or Tyre(); self.p=parameters or CONFIG["car"].copy()

    def calculate_mass(self,fuel_kg=10.):
        fuel=np.asarray(fuel_kg)
        if np.any(fuel<0) or not np.all(np.isfinite(fuel)):
            raise ValueError("Invalid fuel")
        return self.p["dry_mass_kg"]+fuel

    def calculate_aero_forces(self,speed,drs=False,ax=0.,ay=0.):
        """Two-pass quasi-static heave/pitch, with yaw and roll sensitivity."""
        p,w=self.p,self.weather
        speed=np.asarray(speed)
        if np.any(speed<0) or not np.all(np.isfinite(speed)):
            raise ValueError("Invalid speed")
        air=np.maximum(speed+w.headwind_mps,0.)
        # Low-speed crosswind force not resolved: yaw regularization below 15 m/s.
        yaw=np.degrees(np.arctan2(w.crosswind_mps,np.maximum(air,15.)))
        va=np.hypot(air,w.crosswind_mps)
        rho=air_density(w.pressure_pa,w.temperature_k)*w.density_multiplier
        roll=4*np.tanh(np.asarray(ay)*.025/4)  # assumed progressive roll stiffness
        transfer=(p["dry_mass_kg"]+10)*np.asarray(ax)*p["cg_height_m"]/p["wheelbase_m"]
        hf=self.setup.front_height_m+w.height_offset_m
        hr=self.setup.rear_height_m+w.height_offset_m
        cf,cr,cd=coefficients(self.setup,hf,hr,yaw,roll,drs)
        df,_=aero_forces(rho,va,p["area_m2"],cf*w.aero_multiplier,cd*w.aero_multiplier)
        dr,_=aero_forces(rho,va,p["area_m2"],cr*w.aero_multiplier,cd*w.aero_multiplier)
        hf=hf-(df-transfer)/p["axle_heave_stiffness_n_m"]
        hr=hr-(dr+transfer)/p["axle_heave_stiffness_n_m"]
        cf,cr,cd=coefficients(self.setup,hf,hr,yaw,roll,drs)
        df,drag=aero_forces(rho,va,p["area_m2"],cf*w.aero_multiplier,cd*w.aero_multiplier)
        dr,_=aero_forces(rho,va,p["area_m2"],cr*w.aero_multiplier,cd*w.aero_multiplier)
        return {"front_downforce_n":df,"rear_downforce_n":dr,"downforce_n":df+dr,"drag_n":drag,
                "drag_longitudinal_n":drag*np.cos(np.radians(yaw)),"front_height_m":hf,"rear_height_m":hr,
                "yaw_deg":yaw,"roll_deg":roll,"cl_down":cf+cr,"cd":cd}

    def calculate_engine_force(self,speed):
        """Maximum valid-gear torque with power cap and simple RPM torque curve."""
        v=np.asarray(speed); p=self.p
        ratios=np.asarray(p["gear_ratios"])*p["final_drive"]
        rpm=np.expand_dims(v,-1)/p["wheel_radius_m"]*ratios*60/(2*np.pi)
        torque=p["torque_nm"]*(.75+.25*np.exp(-((rpm-8000)/4000)**2))
        force=torque*ratios*p["efficiency"]/p["wheel_radius_m"]
        force=np.where(rpm<=p["max_rpm"],force,0.)
        gear=np.argmax(force,axis=-1)+1
        f=np.minimum(np.max(force,axis=-1),p["power_w"]*p["efficiency"]/np.maximum(v,1.))
        return f,gear

    def wheel_loads(self,mass,aero,ax=0.,ay=0.,bank=0.):
        """Front left/right, rear left/right normal loads; positive ax moves load rearward."""
        p=self.p
        transfer=mass*np.asarray(ax)*p["cg_height_m"]/p["wheelbase_m"]
        normal=mass*(G*np.cos(bank)+np.asarray(ay)*np.sin(bank))
        front=normal*p["front_weight_fraction"]+aero["front_downforce_n"]-transfer
        rear=normal*(1-p["front_weight_fraction"])+aero["rear_downforce_n"]+transfer
        lateral=mass*np.asarray(ay)*p["cg_height_m"]/p["track_m"]
        split=p["roll_front_fraction"]
        return np.stack([front/2-lateral*split,front/2+lateral*split,rear/2-lateral*(1-split),rear/2+lateral*(1-split)],axis=-1)

    def grip_capacity(self,loads,wear=0.,temperature=90.,surface=1.):
        mu=friction(self.tyre,loads,np.expand_dims(wear,-1),np.expand_dims(temperature,-1),np.expand_dims(surface,-1)*self.weather.grip)
        return np.maximum(loads,0.)*mu

    def calculate_traction_limit(self,loads,wear=0.,temperature=90.,surface=1.):
        return self.grip_capacity(loads,wear,temperature,surface)[...,2:].sum(axis=-1)

    def calculate_braking_force(self,loads,wear=0.,temperature=90.,surface=1.):
        cap=self.grip_capacity(loads,wear,temperature,surface)
        bias=self.p["brake_bias"]
        return np.minimum(self.p["brake_limit_n"],np.minimum(cap[...,:2].sum(axis=-1)/bias,cap[...,2:].sum(axis=-1)/(1-bias)))

    def calculate_corner_speed(self,radius,mass=810.,surface=1.,bank=0.,wear=0.,temperature=85.):
        """Bisection of speed-dependent lateral capacity, including axle balance."""
        r=np.asarray(radius,dtype=float); low=np.zeros_like(r); high=np.full_like(r,CONFIG["simulation"]["speed_cap_mps"])
        for _ in range(28):
            v=(low+high)/2
            ay=np.divide(v*v,r,out=np.zeros_like(v),where=r>0)
            aero=self.calculate_aero_forces(v,False,ay=ay)
            loads=self.wheel_loads(mass,aero,ay=ay,bank=bank)
            caps=self.grip_capacity(loads,wear,temperature,surface)
            demand=mass*(ay*np.cos(bank)-G*np.sin(bank))
            wf=self.p["front_weight_fraction"]
            capacity=np.minimum(caps[...,:2].sum(-1)/wf,caps[...,2:].sum(-1)/(1-wf))
            ok=(demand<=capacity)&np.all(loads>=0,axis=-1)
            low=np.where(ok,v,low); high=np.where(ok,high,v)
        return np.where(r>0,low,CONFIG["simulation"]["speed_cap_mps"])

    def update_tyre_state(self,*args,**kwargs):
        return evolve(self.tyre,*args,**kwargs)

    def update_fuel_state(self,fuel,distance):
        used=CONFIG["simulation"]["fuel_kg_per_m"]*distance
        if used>fuel+1e-10: raise ValueError("Insufficient fuel for requested distance")
        return max(0.,fuel-used)

    def simulate_lap(self,track,**kwargs):
        from .lap_simulator import simulate_lap
        return simulate_lap(self,track,**kwargs)

    def simulate_segment(self,segment,**kwargs):
        import pandas as pd
        kwargs.setdefault("flying",False)
        return self.simulate_lap(pd.DataFrame([segment]),**kwargs)

    def simulate_sector(self,segments,**kwargs):
        kwargs.setdefault("flying",False)
        return self.simulate_lap(segments,**kwargs)

    def compare_setups(self,track,setups,**kwargs):
        return [CarModel(s,self.weather,self.tyre,self.p).simulate_lap(track,**kwargs) for s in setups]
