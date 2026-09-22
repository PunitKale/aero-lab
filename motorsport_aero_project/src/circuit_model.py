"""Ordered synthetic tracks. Segment lengths partition the circuit exactly."""
import numpy as np
import pandas as pd

def circuits() -> dict[str,pd.DataFrame]:
    """Create low-drag, mixed and aero-sensitive research circuits."""
    designs={"Velocity Park":(1,[1050,190,650,150,700,200],[0,75,0,40,0,110]),
             "Apex Ring":(2,[650,220,500,200,550,240],[0,95,0,50,0,150]),
             "Downforce Circuit":(3,[420,300,330,260,400,350],[0,160,0,110,0,210])}
    result={}
    for name,(cid,lengths,radii) in designs.items():
        rows=[]
        for j,(length,radius) in enumerate(zip(lengths,radii)):
            rows.append(dict(segment_id=cid*100+j+1,circuit_id=cid,sector_id=cid*10+j//2+1,
                segment_order=j+1,kind="corner" if radius else "straight",length_m=length,radius_m=radius,
                banking_rad=(.02 if j==1 else -.01 if j==3 else 0.),grade_rad=0.,surface_grip=1.,
                width_m=12.,drs_zone=int(j in [0,4]),drs_start_fraction=.15,drs_end_fraction=.82))
        result[name]=pd.DataFrame(rows)
    return result

def discretize(track: pd.DataFrame, step_m: float=20.) -> dict[str,np.ndarray]:
    """Create cells; curvature belongs to cells and corner limits to both endpoints."""
    if step_m<=0 or len(track)==0 or (track.length_m<=0).any():
        raise ValueError("Positive track lengths and integration step required")
    rows=[]
    for r in track.to_dict("records"):
        count=int(np.ceil(r["length_m"]/step_m))
        for j in range(count):
            rows.append({**r,"dx":r["length_m"]/count,"zone":bool(r["drs_zone"] and r["drs_start_fraction"] <= (j+.5)/count <= r["drs_end_fraction"])})
    cells=pd.DataFrame(rows)
    data={c:cells[c].to_numpy() for c in cells.columns}
    data["distance_m"]=np.cumsum(data["dx"])-data["dx"]
    data["curvature"]=np.divide(1.,data["radius_m"],out=np.zeros(len(cells)),where=data["radius_m"]>0)
    return data
