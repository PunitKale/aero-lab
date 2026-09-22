"""Rebuild the offline catalogue from attributed, cached geographic sources."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.config import ROOT
from src.realtrack.geometry import process_geometry

def build():
    entries=[]
    specs=[('silverstone','Silverstone Grand Prix',None,5887),('monaco','Monaco','mc-1929',3337),('monza','Monza','it-1922',5793),('spa','Spa-Francorchamps','be-1925',7004),('suzuka','Suzuka','jp-1962',5807)]
    for i,(slug,name,file,nominal) in enumerate(specs):
        if file:
            path=ROOT/'data/raw/catalogue'/f'{file}.geojson'
            coords=np.array(json.loads(path.read_text())['features'][0]['geometry']['coordinates'])[:,:2]
            source={'source_url':f'https://github.com/bacinger/f1-circuits/blob/master/circuits/{file}.geojson','source_license':'MIT','attribution':'Tomislav Bacinger, f1-circuits','snapshot_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'data_source':'Public mapped GeoJSON; approximate centreline, not surveyed','is_synthetic':False}
        else:
            coords=np.loadtxt(ROOT/'data/raw/silverstone/centreline_lonlat.csv',delimiter=',',skiprows=1)
            source=json.loads((ROOT/'data/raw/silverstone/provenance.json').read_text())
        if np.linalg.norm(coords[0]-coords[-1])>1e-9:coords=np.vstack([coords,coords[0]])
        spec={'circuit_id':101+i,'expected_length_range_m':[nominal*.85,nominal*1.15]}
        track,sectors,metadata=process_geometry(coords,spec)
        entries.append({'id':slug,'name':name,**spec,'length_m':metadata['length_m'],'centerline_lonlat':coords.tolist(),
            'corner_classifications':track[['distance_m','curvature_1pm','classification']].to_dict('records'),
            'sector_boundaries':sectors.to_dict('records'),'default_weather':{'air_temperature_c':20.,'track_temperature_c':30.,'wind_speed_mps':0.,'wind_direction_deg':0.},
            'source':source,'metadata':metadata})
    path=ROOT/'config/circuits.json';path.write_text(json.dumps({'schema_version':1,'default':'silverstone','circuits':entries},indent=2),encoding='utf-8')
    print([(e['name'],round(e['length_m'],1)) for e in entries])
if __name__=='__main__':build()
