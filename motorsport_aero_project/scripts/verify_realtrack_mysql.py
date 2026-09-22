"""Read-only schema/projection and supplied-query acceptance checks."""
from pathlib import Path
import os,json
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];load_dotenv(ROOT/'.env')
value=os.environ.get('REALTRACK_MYSQL_URL') or os.environ['MYSQL_URL']
engine=create_engine(make_url(value)._replace(database='aero_lab_real'));views=[];queries=[]
with engine.connect() as connection:
    for name in ['dim_circuit','dim_setup','dim_sector','dim_run','fact_lap','fact_sector','fact_telemetry']:
        actual=set(connection.execute(text(f'SELECT * FROM {name} LIMIT 0')).keys())
        expected=set(pd.read_csv(ROOT/f'data/processed/realtrack/{name}.csv',nrows=0).columns)
        assert actual==expected,(name,expected-actual,actual-expected);views.append(name)
    sql='\n'.join(line for line in (ROOT/'sql/realtrack_queries.sql').read_text().splitlines() if not line.lstrip().startswith('--'))
    for statement in sql.split(';'):
        if statement.strip():
            result=connection.execute(text(statement))
            if result.returns_rows:queries.append(len(result.fetchall()))
    nc=len(pd.read_csv(ROOT/'data/processed/realtrack/circuits.csv'))
    nr=len(pd.read_csv(ROOT/'data/processed/realtrack/simulation_runs.csv'))
    ns=len(pd.read_csv(ROOT/'data/processed/realtrack/sectors.csv'))
    assert queries==[nc,nr,ns,nr,0],queries
engine.dispose()
evidence={'view_column_sets_passed':views,'analysis_query_row_counts':queries,'reconciliation_query_mismatches':queries[-1]}
(ROOT/'data/processed/realtrack/mysql_query_validation.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
