import os
import pandas as pd
import pytest
from src.ingestion import read_csv
from src.database import schema_sql,ordered_tables

def test_required_csv_fields(tmp_path):
    p=tmp_path/'bad.csv'; p.write_text('speed_mps\n\n')
    with pytest.raises(ValueError): read_csv(p,['speed_mps','fuel_kg'])

def test_schema_foreign_keys():
    t={'dim_circuit':pd.DataFrame([{'circuit_id':1,'name':'X'}]),'dim_sector':pd.DataFrame([{'sector_id':1,'circuit_id':1}])}
    sql=schema_sql(ordered_tables(t))
    assert 'FOREIGN KEY' in sql and 'PRIMARY KEY' in sql

@pytest.mark.integration
def test_live_release_reconciliation():
    from src.config import ROOT
    path=ROOT/'reports/mysql_reconciliation.csv'
    if not path.exists(): pytest.skip('Generate and load release first')
    assert pd.read_csv(path).matched.all()
    from dotenv import load_dotenv
    from sqlalchemy import create_engine,text
    load_dotenv(ROOT/'.env')
    if not os.environ.get('MYSQL_URL'):pytest.skip('MYSQL_URL unavailable')
    engine=create_engine(os.environ['MYSQL_URL'])
    with engine.connect() as c:
        expected=pd.read_csv(ROOT/'data/processed/tables/fact_simulation_lap.csv').lap_time_s.sum()
        actual=c.execute(text('SELECT SUM(lap_time_s) FROM fact_simulation_lap')).scalar_one()
        assert actual==pytest.approx(expected,abs=1e-7)
        assert c.execute(text('SELECT COUNT(*) FROM fact_vehicle_state WHERE drs=1 AND drs_zone=0')).scalar_one()==0
    engine.dispose()

@pytest.mark.integration
def test_powerbi_source_totals():
    from src.config import ROOT
    folder=ROOT/'data/processed/tables'
    if not folder.exists(): pytest.skip('Generate release first')
    laps=pd.read_csv(folder/'fact_simulation_lap.csv'); sectors=pd.read_csv(folder/'fact_simulation_sector.csv')
    merged=laps.merge(sectors.groupby('run_id').sector_time_s.sum(),on='run_id')
    assert ((merged.lap_time_s-merged.sector_time_s).abs()<1e-6).all()
