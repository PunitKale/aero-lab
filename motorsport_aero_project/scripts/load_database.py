"""Load an existing generated release without rerunning numerical experiments."""
import sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.config import ROOT
from src.database import load_mysql
from sqlalchemy import create_engine,text
tables={p.stem:pd.read_csv(p) for p in (ROOT/'data/processed/tables').glob('*.csv')}
first=load_mysql(tables);second=load_mysql(tables)
assert first.matched.all() and second.matched.all()
second.to_csv(ROOT/'reports/mysql_reconciliation.csv',index=False)
engine=create_engine(os.environ['MYSQL_URL'])
with engine.begin() as c:
    for stmt in (ROOT/'sql/views.sql').read_text().split(';'):
        if stmt.strip():c.execute(text(stmt))
    print('MySQL version:',c.execute(text('SELECT VERSION()')).scalar_one())
    print('DRS pairs:',c.execute(text('SELECT COUNT(*) FROM vw_drs_comparison')).scalar_one())
engine.dispose()
error=ROOT/'reports/mysql_error.txt'
if error.exists():
    with (ROOT/'reports/mysql_initial_error_resolved.txt').open('a') as log:log.write('\nResolved on successful snapshot reload: '+error.read_text())
    error.unlink()
print(second.to_string(index=False))
