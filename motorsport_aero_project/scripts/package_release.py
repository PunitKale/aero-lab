"""Create a portable dependency lock and zip, excluding secrets and runtime files."""
import sys,json,zipfile,hashlib,platform
from pathlib import Path
from importlib.metadata import distribution
from packaging.requirements import Requirement
ROOT=Path(__file__).resolve().parents[1]
roots=['numpy','pandas','scipy','scikit-learn','matplotlib','seaborn','plotly','SQLAlchemy','PyMySQL','cryptography','python-dotenv','pytest','openpyxl','XlsxWriter','PyYAML','nbformat','jsonschema']
seen={}
def visit(name):
    d=distribution(name);key=d.metadata['Name'].lower().replace('_','-')
    if key in seen:return
    seen[key]=(d.metadata['Name'],d.version)
    for requirement in d.requires or []:
        r=Requirement(requirement)
        if r.marker is None or r.marker.evaluate({'extra':''}):visit(r.name)
for root in roots:visit(root)
(ROOT/'requirements-lock.txt').write_text('\n'.join(f'{n}=={v}' for n,v in sorted(seen.values(),key=lambda x:x[0].lower()))+'\n')
(ROOT/'reports/environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'model_version':'1.0.0','mysql':'8.0.46','excel_recalculation':'executed','powerbi_desktop':'unavailable'},indent=2))
# Packaging must not fabricate or renew UI acceptance. Preserve the earlier analysis
# checks, clearly scoped to the original layer, and link the separate 3D evidence.
ui_path=ROOT/'reports/ui_verification.json'
ui=json.loads(ui_path.read_text()) if ui_path.exists() else {'result':'not executed'}
ui['scope']='Prior analysis-layer checks; not browser acceptance of the new 3D layer.'
ui['simulation_evidence']='simulation_validation.json'
ui_path.write_text(json.dumps(ui,indent=2))
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.pytest_cache','schema_cache','.venv','node_modules']) and p.name not in ['.env','release_manifest.json']]
manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
(ROOT/'reports/release_manifest.json').write_text(json.dumps(manifest,indent=2))
output=ROOT.parent/'Motorsport_Aero_Project_Release.zip'
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in files+[ROOT/'reports/release_manifest.json']:archive.write(p,str(Path('motorsport_aero_project')/p.relative_to(ROOT)))
    for folder in ['planning','reports']:
        for p in (ROOT.parent/folder).glob('*'):
            if p.is_file():archive.write(p,str(Path(folder)/p.name))
    archive.write(ROOT.parent/'README.md','README.md')
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    assert not any(Path(n).name=='.env' for n in archive.namelist())
print(json.dumps({'archive':str(output),'bytes':output.stat().st_size,'files':len(files)+1,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2))
