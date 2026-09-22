"""Physically linked synthetic input generation with explicit metadata."""
from dataclasses import asdict
from datetime import datetime,timezone
import itertools
import numpy as np
import pandas as pd
from .schemas import Setup,Weather,Tyre
from .config import CONFIG
from .circuit_model import circuits
from .aero_map import coefficients

def metadata(source="synthetic") -> dict:
    return dict(data_source_type=source,synthetic_flag=True,model_version=CONFIG["model_version"],data_version=CONFIG["data_version"],
        generation_timestamp=datetime.now(timezone.utc).isoformat(),random_seed=CONFIG["random_seed"],validation_status="schema_checked")

def setup_design(seed=42,count=12):
    """Baseline plus stratified random continuous setups; fixed seed controls values."""
    rng=np.random.default_rng(seed); bounds=np.array(list(CONFIG["bounds"].values()))
    values=rng.uniform(bounds[:,0]+.1*(bounds[:,1]-bounds[:,0]),bounds[:,1]-.1*(bounds[:,1]-bounds[:,0]),(count-1,4))
    return [Setup()]+[Setup(*x) for x in values]

def generate_inputs(seed=42):
    setups=setup_design(seed); tracks=circuits()
    weather=[Weather(),Weather("Hot",97000,310.15,.97),Weather("Wet",100500,285.15,.68)]
    tyres=[Tyre("Soft",1.68,.000003),Tyre(),Tyre("Hard",1.52,.0000014)]
    tables={
        "dim_car":pd.DataFrame([{"car_id":1,"car_name":"Synthetic RWD Single-Seater",**{k:v for k,v in CONFIG["car"].items() if not isinstance(v,list)}}]),
        "dim_circuit":pd.DataFrame([dict(circuit_id=i+1,circuit_name=n,length_m=t.length_m.sum()) for i,(n,t) in enumerate(tracks.items())]),
        "dim_track_segment":pd.concat(tracks.values(),ignore_index=True),
        "dim_setup":pd.DataFrame([dict(setup_id=i+1,setup_name="Baseline" if i==0 else f"Candidate {i:02d}",**asdict(s)) for i,s in enumerate(setups)]),
        "dim_weather":pd.DataFrame([dict(weather_id=i+1,**asdict(w)) for i,w in enumerate(weather)]),
        "dim_tyre":pd.DataFrame([dict(tyre_id=i+1,**asdict(t)) for i,t in enumerate(tyres)]),
        "dim_driver":pd.DataFrame([dict(driver_id=1,driver_name="Deterministic idealized driver",consistency_sigma_s=0.)]),
        "dim_date":pd.DataFrame([dict(date_id=20260917,date_iso="2026-09-17",year=2026,month=9,day=17)]),
        "dim_session":pd.DataFrame([dict(session_id=i+1,session_name=n,date_id=20260917) for i,n in enumerate(["Qualifying","Race","Wet study"])]),
    }
    segments=tables["dim_track_segment"]
    tables["dim_sector"]=segments[["sector_id","circuit_id"]].drop_duplicates().assign(sector_name=lambda d:d.sector_id.map(lambda x:f"Sector {x%10}"))
    tables["dim_corner"]=segments.loc[segments.radius_m>0,["segment_id","sector_id","radius_m","banking_rad","width_m"]].rename(columns={"segment_id":"corner_id"})
    aero=[]
    for sid,s in enumerate(setups,1):
        for speed,hf,hr,yaw,drs in itertools.product([0,30,50,70,90],[.025,.04,.055],[.04,.06,.085],[-5,0,5],[0,1]):
            cf,cr,cd=coefficients(s,hf,hr,yaw,drs=bool(drs)); q=.5*1.225*speed**2
            aero.append(dict(aero_map_id=len(aero)+1,setup_id=sid,speed_mps=speed,front_height_m=hf,rear_height_m=hr,yaw_deg=yaw,drs=drs,
                cl_front=float(cf),cl_rear=float(cr),cd=float(cd),downforce_n=float(q*1.5*(cf+cr)),drag_n=float(q*1.5*cd)))
    tables["fact_aero_map"]=pd.DataFrame(aero)
    stamp=metadata()
    for name in tables:
        for k,v in stamp.items(): tables[name][k]=v
    return tables,setups,tracks,weather,tyres
