"""Portable CSV/JSON exports and source manifests."""
import json
from pathlib import Path
from .ingestion import manifest

def export_tables(tables,directory: Path):
    directory.mkdir(parents=True,exist_ok=True)
    for name,df in tables.items(): df.to_csv(directory/f'{name}.csv',index=False,float_format='%.12g')
    (directory/'manifest.json').write_text(json.dumps(manifest(directory),indent=2))

def json_export(path: Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
