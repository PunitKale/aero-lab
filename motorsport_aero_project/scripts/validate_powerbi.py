"""Validate PBIR JSON against Microsoft's public schemas; cache schemas locally."""
from pathlib import Path
import json,urllib.request
from urllib.parse import urljoin,urldefrag
from jsonschema import Draft7Validator,RefResolver
ROOT=Path(__file__).resolve().parents[1];cache=ROOT/'powerbi/schema_cache';cache.mkdir(exist_ok=True)
store={}
def fetch(url):
    url=urldefrag(url)[0]
    if url in store:return store[url]
    import hashlib
    path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if path.exists():s=json.loads(path.read_text())
    else:
        try:
            with urllib.request.urlopen(url,timeout=30) as response:s=json.load(response)
        except Exception as e: raise RuntimeError(f'{url}: {e}') from e
        path.write_text(json.dumps(s))
    store[url]=s
    # Microsoft embedded schemas sometimes declare a dotted $id while served
    # at a hyphenated URL. Register that declared identifier to the same schema.
    if '$id' in s: store[s['$id']]=s
    return s
errors=[];count=0
files=list((ROOT/'powerbi/Aero.Report').rglob('*.json'))+[ROOT/'powerbi/Aero.Report/definition.pbir',ROOT/'powerbi/Aero.pbip',ROOT/'powerbi/Aero.SemanticModel/definition.pbism']
for path in files:
    obj=json.loads(path.read_text());url=obj.get('$schema')
    if not url:continue
    try:
        schema=fetch(url);resolver=RefResolver(base_uri=url,referrer=schema,handlers={'https':fetch,'http':fetch})
        for error in Draft7Validator(schema,resolver=resolver).iter_errors(obj):errors.append({'file':str(path.relative_to(ROOT)),'error':error.message,'path':list(error.path)})
        count+=1
    except Exception as e:errors.append({'file':str(path.relative_to(ROOT)),'error':str(e)})
result={'files_checked':count,'errors':errors,'desktop_rendered':False,'note':'JSON schema validation does not execute DAX, parse TMDL or verify visual rendering.'}
(ROOT/'reports/powerbi_schema_validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2)[:6000])
if errors:raise SystemExit(1)
