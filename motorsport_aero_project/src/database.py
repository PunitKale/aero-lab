"""MySQL DDL, transactional idempotent snapshots and live reconciliation."""
import json,os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv
from .config import ROOT

KEYS={"dim_car":"car_id","dim_circuit":"circuit_id","dim_sector":"sector_id","dim_corner":"corner_id", "dim_track_segment":"segment_id",
    "dim_session":"session_id","dim_driver":"driver_id","dim_weather":"weather_id","dim_tyre":"tyre_id","dim_setup":"setup_id","dim_date":"date_id",
    "fact_aero_map":"aero_map_id","run_registry":"run_id","fact_simulation_lap":"simulation_lap_id","fact_simulation_sector":"simulation_sector_id",
    "fact_simulation_segment":"simulation_segment_id","fact_vehicle_state":"vehicle_state_id","fact_simulation_warning":"warning_id",
    "fact_drs_event":"drs_event_id","fact_tyre_state":"tyre_state_id","fact_optimization_run":"optimization_run_id",
    "fact_optimization_result":"optimization_result_id","fact_model_validation":"validation_id","fact_lap":"lap_id","fact_sector":"sector_fact_id","fact_telemetry":"telemetry_id"}
REFERENCES={v:k for k,v in KEYS.items()}

def mysql_type(series):
    if pd.api.types.is_bool_dtype(series): return "BOOLEAN"
    if pd.api.types.is_integer_dtype(series): return "BIGINT"
    if pd.api.types.is_numeric_dtype(series): return "DOUBLE"
    return "VARCHAR(500)"

def schema_sql(tables):
    """Emit explicit CREATE TABLE statements with keys, constraints and indexes."""
    parts=["CREATE DATABASE IF NOT EXISTS motorsport_aero CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;","USE motorsport_aero;"]
    for name,df in tables.items():
        pk=KEYS[name]; defs=[]
        for col in df:
            dtype="BIGINT" if col in REFERENCES else mysql_type(df[col])
            defs.append(f"  `{col}` {dtype}"+(" NOT NULL" if col==pk or col.endswith('_id') else ""))
        defs.append(f"  PRIMARY KEY (`{pk}`)")
        for col in df:
            parent=REFERENCES.get(col)
            if parent and parent!=name and parent in tables:
                defs.append(f"  CONSTRAINT `fk_{name}_{col}` FOREIGN KEY (`{col}`) REFERENCES `{parent}` (`{col}`)")
            if col in ("lap_time_s","sector_time_s","segment_time_s","fuel_kg","speed_mps","downforce_n","drag_n"):
                defs.append(f"  CHECK (`{col}` >= 0)")
        if name=="fact_vehicle_state": defs.append("  UNIQUE KEY `uq_state_sample` (`run_id`,`sample_index`)")
        if name=="fact_simulation_sector": defs.append("  UNIQUE KEY `uq_run_sector` (`run_id`,`sector_id`)")
        parts.append(f"CREATE TABLE IF NOT EXISTS `{name}` (\n"+",\n".join(defs)+"\n) ENGINE=InnoDB;")
    return "\n\n".join(parts)

def ordered_tables(tables):
    """Topological table order for foreign-key-safe creation and loading."""
    remaining=dict(tables); result={}
    while remaining:
        progressed=False
        for name,df in list(remaining.items()):
            parents={REFERENCES[c] for c in df if c in REFERENCES and REFERENCES[c]!=name and REFERENCES[c] in tables}
            if parents <= result.keys(): result[name]=remaining.pop(name); progressed=True
        if not progressed: raise ValueError(f"Cyclic table dependencies: {list(remaining)}")
    return result

def seed_sql(tables):
    """Portable SQL seed export of actual synthetic release records."""
    def quote(v):
        if pd.isna(v): return "NULL"
        if isinstance(v,bool): return "1" if v else "0"
        if isinstance(v,(int,float)): return repr(v)
        return "'"+str(v).replace("\\","\\\\").replace("'","''")+"'"
    lines=["USE motorsport_aero;"]
    for name,df in tables.items():
        cols=",".join(f"`{c}`" for c in df)
        for start in range(0,len(df),200):
            values=["("+",".join(quote(x) for x in row)+")" for row in df.iloc[start:start+200].itertuples(index=False,name=None)]
            if values:
                update=','.join(f'`{c}`=VALUES(`{c}`)' for c in df if c!=KEYS[name])
                lines.append(f"INSERT INTO `{name}` ({cols}) VALUES\n"+",\n".join(values)+" ON DUPLICATE KEY UPDATE "+update+";")
    return "\n".join(lines)

def load_mysql(tables,url=None):
    """Atomically upsert data without disabling foreign keys or masking errors."""
    load_dotenv(ROOT/'.env'); url=url or os.environ.get("MYSQL_URL")
    if not url: raise ValueError("MYSQL_URL not configured")
    tables=ordered_tables(tables)
    u=make_url(url); admin=create_engine(u._replace(database=None))
    with admin.begin() as c: c.execute(text("CREATE DATABASE IF NOT EXISTS motorsport_aero CHARACTER SET utf8mb4"))
    engine=create_engine(url)
    ddl=schema_sql(tables)
    with engine.begin() as c:
        for statement in ddl.split(';'):
            if statement.strip() and not statement.strip().startswith(('CREATE DATABASE','USE ')): c.execute(text(statement))
        # This dedicated database is a versioned release snapshot. Replace only
        # managed tables atomically so a finer mesh cannot leave stale samples.
        for name in reversed(tables): c.execute(text(f'DELETE FROM `{name}`'))
        for name,df in tables.items():
            if df.empty: continue
            cols=list(df); pk=KEYS[name]
            query=f"INSERT INTO `{name}` ("+','.join(f'`{x}`' for x in cols)+") VALUES ("+','.join(f':{x}' for x in cols)+") ON DUPLICATE KEY UPDATE "+','.join(f'`{x}`=VALUES(`{x}`)' for x in cols if x!=pk)
            records=df.astype(object).where(pd.notnull(df),None).to_dict('records')
            for j in range(0,len(records),500): c.execute(text(query),records[j:j+500])
    checks=[]
    with engine.connect() as c:
        for name,df in tables.items():
            count=c.execute(text(f'SELECT COUNT(*) FROM `{name}`')).scalar_one()
            checks.append(dict(table_name=name,python_rows=len(df),mysql_rows=count,matched=count==len(df)))
        total=c.execute(text('SELECT SUM(lap_time_s) FROM fact_simulation_lap')).scalar_one()
        expected=tables['fact_simulation_lap'].lap_time_s.sum()
        checks.append(dict(table_name='lap_time_sum_s',python_rows=expected,mysql_rows=total,matched=abs(expected-total)<1e-8))
    engine.dispose(); admin.dispose()
    return pd.DataFrame(checks)

def data_dictionary(tables):
    """Column-level schema contract including units, examples, keys and nullability."""
    units={'_mps2':'m/s²','_mps':'m/s','_kg':'kg','_n':'N','_w':'W','_pa':'Pa','_s':'s','_m':'m','_deg':'deg','_rad':'rad','_k':'K','_c':'°C'}
    rows=[]
    for name,df in tables.items():
        for col in df:
            unit=next((v for suffix,v in units.items() if col.endswith(suffix)), 'dimensionless / identifier / text')
            rows.append(dict(table=name,column=col,mysql_type="BIGINT" if col in REFERENCES else mysql_type(df[col]),unit=unit,
                primary_key=col==KEYS[name],foreign_table=REFERENCES.get(col,'') if col!=KEYS[name] else '',nullable=not col.endswith('_id'),
                example=str(df[col].iloc[0]) if len(df) else 'No measured records available'))
    return pd.DataFrame(rows)
