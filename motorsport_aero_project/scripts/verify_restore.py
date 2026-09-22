"""Reconstruct a separate verification database using delivered SQL scripts."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv
from src.config import ROOT
from src.database import ordered_tables,schema_sql,seed_sql

def statements(script):
    """Split authored SQL outside string literals (including escaped quotes)."""
    quote=None;escaped=False;start=0
    for i,char in enumerate(script):
        if escaped:escaped=False;continue
        if char=='\\' and quote:escaped=True;continue
        if quote:
            if char==quote:quote=None
        elif char in ["'",'"','`']:quote=char
        elif char==';':
            if script[start:i].strip():yield script[start:i]
            start=i+1
    if script[start:].strip():yield script[start:]

if __name__=='__main__':
    tables=ordered_tables({p.stem:pd.read_csv(p) for p in (ROOT/'data/processed/tables').glob('*.csv')})
    ddl=schema_sql(tables);seed=seed_sql(tables)
    (ROOT/'sql/schema.sql').write_text(ddl,encoding='utf-8');(ROOT/'sql/seed.sql').write_text(seed,encoding='utf-8')
    load_dotenv(ROOT/'.env');url=make_url(os.environ['MYSQL_URL']);engine=create_engine(url._replace(database=None))
    with engine.begin() as c:
        for script in [ddl,seed]:
            script=script.replace('motorsport_aero','motorsport_aero_restore_check')
            for stmt in statements(script):c.execute(text(stmt))
        results={name:int(c.execute(text(f'SELECT COUNT(*) FROM `{name}`')).scalar_one()) for name in tables}
        assert all(results[n]==len(df) for n,df in tables.items())
        total=float(c.execute(text('SELECT SUM(lap_time_s) FROM fact_simulation_lap')).scalar_one())
    engine.dispose()
    (ROOT/'reports/restore_verification.json').write_text(json.dumps({'database':'motorsport_aero_restore_check','table_counts':results,'all_counts_match':True,'lap_time_sum_s':total},indent=2))
    print('Delivered schema and seed SQL restored successfully into a separate database.')
