"""Build the Silverstone analysis entry point, reusing local Plotly and 3D modules."""
import json
from ..config import ROOT
from .dashboard_view import render_dashboard

def build_dashboard(data):
    sensitivity=ROOT/'data/processed/realtrack/mesh_sensitivity.json'
    data['numerical_sensitivity']={}
    if sensitivity.exists():
        for row in json.loads(sensitivity.read_text()).get('circuits',[]):
            if data['recommendations'].get(row['circuit'],{}).get('dataset_id')==row['dataset_id']:
                data['numerical_sensitivity'][row['circuit']]=row
    reports=ROOT/'reports';legacy=reports/'legacy_dashboard.html'
    if not legacy.exists() and (reports/'dashboard.html').exists():legacy.write_bytes((reports/'dashboard.html').read_bytes())
    template=render_dashboard()
    payload=json.dumps(data,allow_nan=False).replace('</','<\\/')
    (reports/'dashboard.html').write_text(template.replace('__PAYLOAD__',payload),encoding='utf-8')
