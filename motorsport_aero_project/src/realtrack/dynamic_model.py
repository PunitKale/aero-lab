"""Interactive model v2: longitudinal wind, assumed compound/temperature grip and fuel mass. See docs/dynamic_simulation.md."""
import numpy as np
import pandas as pd

def aero_coefficients(setup, diffuser_efficiency=None):
    f,r=setup['front_wing_deg'],setup['rear_wing_deg']
    de = diffuser_efficiency if diffuser_efficiency is not None else setup.get('diffuser_efficiency', 1.0)
    floor=np.clip(1-3*abs(setup['front_height_m']-.04)-2*abs(setup['rear_height_m']-.06),.7,1)
    cl = (1.5 * de + .045*f + .06*r) * floor
    cd = .55 + .0007*f*f + .001*r*r + .08*(1-floor) + .02*(de-1)**2
    return float(cl), float(cd)

def simulate(track,setup,vehicle):
    m=vehicle['mass_kg'];g=9.81;mu=vehicle['mu'];cl,cd=aero_coefficients(setup, diffuser_efficiency=setup.get('diffuser_efficiency'))
    q=.5*vehicle['rho_kg_m3']*vehicle['area_m2'];ds=track.step_m.to_numpy();n=len(ds)
    rr=vehicle['rolling_coefficient']*m*g
    # Meteorological wind direction: FROM north clockwise; heading is east CCW.
    heading=track.heading_rad.to_numpy()
    wind=vehicle.get('wind_speed_mps',0.)*np.sin(heading+np.deg2rad(vehicle.get('wind_direction_deg',0.)))
    # Bound wind at both endpoints of every cell; ignore crosswind side force.
    wind_hi=np.maximum(wind,np.roll(wind,-1));wind_lo=np.minimum(wind,np.roll(wind,-1))
    max_w=np.maximum.reduce([wind,np.roll(wind,1),np.roll(wind,-1)])
    min_w=np.minimum.reduce([wind,np.roll(wind,1),np.roll(wind,-1)])
    terminal_speed=vehicle['max_speed_mps']
    k=np.abs(track.curvature_1pm.to_numpy());kcell=np.maximum(k,np.roll(k,-1))
    # m*v²*k <= mu*(m*g + q*CL*v²), plus an explicit lateral acceleration cap.
    # Reserve grip for the drive force needed to balance drag/rolling resistance.
    # Neighbor maxima bound both ends of a cell, avoiding a point/cell mismatch.
    kbound=np.maximum.reduce([k,np.roll(k,1),np.roll(k,-1)])
    lo=np.zeros(n);hi=np.minimum(np.sqrt(vehicle['max_lateral_mps2']/np.maximum(kbound,1e-12)),terminal_speed)
    for _ in range(60):
        mid=(lo+hi)/2
        required=np.hypot(m*mid*mid*kbound,q*cd*np.maximum(mid+max_w,0)**2+rr)
        feasible=(required<=mu*(m*g+q*cl*np.maximum(mid+min_w,0)**2)) & ((q*cd*np.maximum(mid+max_w,0)**2+rr)*mid<=vehicle["power_w"])
        lo=np.where(feasible,mid,lo);hi=np.where(feasible,hi,mid)
    v=lo
    def limits(a,b,curvature,index):
        high=max(a,b);low=min(a,b)
        # Conservative cell envelope: lateral demand at high speed, tyre capacity
        # at low speed. The friction circle shares grip between turning and braking.
        capacity=mu*(m*g+q*cl*max(low+wind_lo[index],0)**2);fy=m*high*high*curvature
        fx=np.sqrt(max(0,capacity*capacity-fy*fy))
        drive=min(fx,vehicle['power_w']/max(high,1))
        acc=max(0,(drive-q*cd*max(high+wind_hi[index],0)**2-rr)/m)
        brake=min(vehicle['max_brake_mps2'],(fx+q*cd*max(low+wind_lo[index],0)**2+rr)/m)
        return acc,brake
    # Monotonically tighten a periodic flying-lap envelope. No arbitrary starting
    # speed and no hard-coded target lap time. Require convergence before export.
    for iteration in range(300):
        previous=v.copy()
        for i in range(n):
            j=(i+1)%n;acc,_=limits(v[i],v[j],kcell[i],i)
            if v[j]**2>v[i]**2+2*acc*ds[i]+1e-10:
                lo,hi=v[i],v[j]
                for _ in range(28):
                    mid=(lo+hi)/2;acc,_=limits(v[i],mid,kcell[i],i)
                    if mid*mid<=v[i]**2+2*acc*ds[i]:lo=mid
                    else:hi=mid
                v[j]=lo
        for i in range(n-1,-1,-1):
            j=(i+1)%n;_,brake=limits(v[i],v[j],kcell[i],i)
            if v[i]**2>v[j]**2+2*brake*ds[i]+1e-10:
                lo,hi=v[j],v[i]
                for _ in range(28):
                    mid=(lo+hi)/2;_,brake=limits(mid,v[j],kcell[i],i)
                    if mid*mid<=v[j]**2+2*brake*ds[i]:lo=mid
                    else:hi=mid
                v[i]=lo
        if np.max(abs(v-previous))<1e-8: break
    else: raise ValueError('Speed envelope did not converge')
    exit_v=np.roll(v,-1);dt=2*ds/(v+exit_v);acc=(exit_v**2-v**2)/(2*ds)
    # Force values at the cell-average squared speed (constant acceleration in s).
    v2=(v*v+exit_v*exit_v)/2; air2=(np.maximum(v+wind,0)**2+np.maximum(exit_v+np.roll(wind,-1),0)**2)/2;df=q*cl*air2;drag=q*cd*air2
    front_fraction=np.clip(.43+.004*(setup['front_wing_deg']-setup['rear_wing_deg']),.32,.53)
    wear_step=vehicle.get("wear_multiplier",1.)*ds*1e-6*(1+.2*v2*k/g+.08*np.maximum(-acc,0)/g)
    wear_start=np.r_[0,np.cumsum(wear_step)[:-1]]
    result=pd.DataFrame({'track_point_id':track.track_point_id,'sample_index':np.arange(n),'time_s':np.r_[0,np.cumsum(dt)[:-1]],'dt_s':dt,
        'speed_mps':v,'exit_speed_mps':exit_v,'acceleration_mps2':acc,'downforce_n':df,'front_downforce_n':df*front_fraction,'rear_downforce_n':df*(1-front_fraction),
        'drag_n':drag,'tyre_wear':wear_start,'tyre_wear_end':wear_start+wear_step,'is_synthetic':True,'data_source':'Aero Lab rule-based model-generated outputs'})
    return result,{'lap_time_s':float(dt.sum()),'max_speed_mps':float(v.max()),'tyre_wear_change':float(wear_step.sum()),'solver_iterations':iteration+1,'cl_down':cl,'cd':cd}
