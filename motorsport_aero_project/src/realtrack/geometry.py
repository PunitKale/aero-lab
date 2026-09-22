"""WGS84 geographic -> local east/north metres -> smoothed fixed-distance geometry."""
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d

def to_local(lonlat):
    # WGS84 ECEF followed by the east/north tangent-plane rotation. No fake GPS
    # points or map-image digitization; altitude is ignored and explicitly assumed 0.
    lon,lat=np.deg2rad(lonlat).T; a=6378137.;e2=6.69437999014e-3
    n=a/np.sqrt(1-e2*np.sin(lat)**2)
    xyz=np.column_stack((n*np.cos(lat)*np.cos(lon),n*np.cos(lat)*np.sin(lon),n*(1-e2)*np.sin(lat)))
    d=xyz-xyz[0];l0,p0=lon[0],lat[0]
    east=np.array([-np.sin(l0),np.cos(l0),0]);north=np.array([-np.sin(p0)*np.cos(l0),-np.sin(p0)*np.sin(l0),np.cos(p0)])
    return np.column_stack((d@east,d@north))

def process_geometry(lonlat,circuit,spacing=5.,sigma=4.):
    if spacing<=0 or sigma<0: raise ValueError('Invalid geometry spacing/smoothing')
    xy=to_local(lonlat)
    keep=np.r_[True,np.linalg.norm(np.diff(xy,axis=0),axis=1)>.05];xy=xy[keep]
    if np.linalg.norm(xy[-1]-xy[0])>.1: raise ValueError('Source is not closed')
    xy[-1]=xy[0]
    source_s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    # Interpolate source, smooth at uniform 1 m intervals, then reparameterize by
    # arc length. This reduces digitization noise before calculating curvature.
    initial=CubicSpline(source_s,xy,bc_type='periodic')
    grid=np.linspace(0,source_s[-1],int(np.ceil(source_s[-1])),endpoint=False)
    smooth=gaussian_filter1d(initial(grid),sigma=max(sigma/(source_s[-1]/len(grid)),.001),axis=0,mode='wrap')
    smooth=np.vstack([smooth,smooth[0]])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(smooth,axis=0),axis=1))]
    curve=CubicSpline(arc,smooth,bc_type='periodic');length=float(arc[-1])
    if not circuit['expected_length_range_m'][0]<length<circuit['expected_length_range_m'][1]: raise ValueError(f'Unexpected source length {length}')
    s=np.arange(0,length,spacing);pos=curve(s);d1=curve(s,1);d2=curve(s,2)
    curvature=(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])/np.maximum(np.linalg.norm(d1,axis=1)**3,1e-12)
    heading=np.arctan2(d1[:,1],d1[:,0]);steps=np.diff(np.r_[s,length])
    # Analytical equal-distance thirds snapped to sample boundaries, not FIA sectors.
    if circuit.get('sector_boundaries'):
        b1 = int(np.searchsorted(s, length * circuit['sector_boundaries'][0]))
        b2 = int(np.searchsorted(s, length * circuit['sector_boundaries'][1]))
        sec_desc = f"Configured boundaries {circuit['sector_boundaries']}"
    else:
        b1=int(np.searchsorted(s,length/3));b2=int(np.searchsorted(s,2*length/3))
        sec_desc = 'Analytical equal-distance thirds; not official timing sectors'
    seq=np.arange(len(s));sector=np.where(seq<b1,1,np.where(seq<b2,2,3));cid=circuit['circuit_id']
    frame=pd.DataFrame({'track_point_id':cid*100000+seq,'circuit_id':cid,'point_index':seq,'distance_m':s,'step_m':steps,
        'x_m':pos[:,0],'y_m':pos[:,1],'heading_rad':heading,'curvature_1pm':curvature,
        'classification':np.where(abs(curvature)<1/700,'straight',np.where(abs(curvature)<1/160,'fast_corner','corner')),
        'sector_id':cid*10+sector,'is_synthetic':False,'is_derived':True,'data_source':'OSM-derived smoothed centreline'})
    edges=[0,float(s[b1]),float(s[b2]),length]
    sectors=pd.DataFrame([{'sector_id':cid*10+i+1,'circuit_id':cid,'sector_number':i+1,'name':f'Sector {i+1}',
        'start_distance_m':edges[i],'end_distance_m':edges[i+1],'is_synthetic':True,'data_source':sec_desc} for i in range(3)])
    return frame,sectors,{'length_m':length,'raw_length_m':float(source_s[-1]),'raw_points':len(lonlat),'clean_points':len(xy),
        'sample_count':len(frame),'projection':'WGS84 ECEF to local east/north tangent plane; altitude 0 m',
        'origin_lon':float(lonlat[0,0]),'origin_lat':float(lonlat[0,1]),'smoothing_sigma_m':sigma,'spacing_m':spacing,
        'max_smoothing_displacement_m':float(np.max(np.linalg.norm(initial(grid)-smooth[:-1],axis=1)))}
