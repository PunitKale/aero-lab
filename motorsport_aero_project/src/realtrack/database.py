"""Foreign-key-safe MySQL snapshot loading and SQL/CSV reconciliation."""
import os,json
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv
from ..config import ROOT

ORDER=['circuits','sectors','track_points','aero_setups','simulation_runs','telemetry_points']

def seed_sql(tables):
    def literal(v):
        if isinstance(v,bool):return str(int(v))
        if isinstance(v,(int,float)):return repr(v)
        return "'"+str(v).replace('\\','\\\\').replace("'","''")+"'"
    parts=['USE aero_lab_real;','START TRANSACTION;']
    for name in ORDER:
        df=tables[name];cols=','.join('`'+c+'`' for c in df)
        for i in range(0,len(df),150):
            rows=['('+','.join(literal(v) for v in row)+')' for row in df.iloc[i:i+150].itertuples(index=False,name=None)]
            # Sample SQL is for the clean schema; the Python loader handles safe refresh.
            parts.append(f'INSERT INTO `{name}` ({cols}) VALUES '+',\n'.join(rows)+';')
    return '\n'.join(parts+['COMMIT;'])

def load_mysql(tables):
    load_dotenv(ROOT/'.env')
    value=os.getenv('REALTRACK_MYSQL_URL') or os.getenv('MYSQL_URL')
    if not value:raise ValueError('Set REALTRACK_MYSQL_URL in .env before loading MySQL')
    url=make_url(value)._replace(database='aero_lab_real')
    admin=create_engine(url._replace(database=None))
    with admin.begin() as con:con.execute(text('CREATE DATABASE IF NOT EXISTS aero_lab_real CHARACTER SET utf8mb4'))
    admin.dispose();engine=create_engine(url)
    ddl=(ROOT/'sql/realtrack_schema.sql').read_text()
    with engine.begin() as con:
        for statement in ddl.split(';'):
            if statement.strip():con.execute(text(statement))
    # DDL auto-commits in MySQL. Data refresh is a separate atomic transaction.
    ids=[int(x) for x in tables['circuits'].circuit_id]
    with engine.begin() as con:
        for cid in ids:
            for name in ['telemetry_points','simulation_runs','track_points','sectors']:
                con.execute(text(f'DELETE FROM `{name}` WHERE circuit_id=:cid'),{'cid':cid})
        for name in ORDER:
            df=tables[name];cols=list(df)
            query=f'INSERT INTO `{name}` ('+','.join('`'+c+'`' for c in cols)+') VALUES ('+','.join(':'+c for c in cols)+')'
            if name in ['circuits','aero_setups']:
                query+=' ON DUPLICATE KEY UPDATE '+','.join(f'`{c}`=VALUES(`{c}`)' for c in cols[1:])
            records=df.to_dict('records')
            for i in range(0,len(records),500):con.execute(text(query),records[i:i+500])
    checks=[]
    with engine.connect() as con:
        for name in ORDER:
            # Full table counts are appropriate for this dedicated, managed dataset.
            actual=con.execute(text(f'SELECT COUNT(*) FROM `{name}`')).scalar_one()
            checks.append({'check':name+' rows','expected':len(tables[name]),'actual':actual,'passed':actual==len(tables[name])})
        for r in tables['simulation_runs'].to_dict('records'):
            actual=con.execute(text('SELECT SUM(dt_s) FROM telemetry_points WHERE run_id=:r'),{'r':r['run_id']}).scalar_one()
            checks.append({'check':f"run {r['run_id']} seconds",'expected':r['lap_time_s'],'actual':actual,'passed':abs(actual-r['lap_time_s'])<1e-8})
        db=pd.read_sql(text('SELECT run_id,distance_m,x_m,y_m,speed_mps,downforce_n,drag_n FROM fact_telemetry ORDER BY run_id,point_index'),con)
        expected=tables['telemetry_points'].merge(tables['track_points'][['track_point_id','distance_m','x_m','y_m']],on='track_point_id').sort_values(['run_id','sample_index'])
        import numpy as np
        cols=['run_id','distance_m','x_m','y_m','speed_mps','downforce_n','drag_n']
        checks.append({'check':'all geometry and performance rows match Python','passed':db.shape[0]==expected.shape[0] and bool(np.allclose(db[cols],expected[cols],rtol=0,atol=1e-9))})
    engine.dispose()
    if not all(c['passed'] for c in checks):raise ValueError('MySQL reconciliation failed')
    return checks
