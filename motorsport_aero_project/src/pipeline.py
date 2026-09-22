"""Reproducible release pipeline: python -m src.pipeline [--draws 200]."""
import argparse,json,logging,time
from dataclasses import asdict
import numpy as np
import pandas as pd
from .config import ROOT,CONFIG
from .logging_config import configure_logging
from .synthetic_data import generate_inputs,metadata
from .schemas import Setup,VehicleState,Weather
from .vehicle_model import CarModel
from .lap_simulator import simulate_stint,braking_test
from .optimization import optimize,constraint_reasons,Evaluator
from .uncertainty import paired_uncertainty
from .explainability import sector_comparison,sensitivity
from .validation import validate_trace,quality_report
from .telemetry import drs_events
from .database import ordered_tables,schema_sql,seed_sql,data_dictionary,load_mysql
from .export import export_tables,json_export
log=logging.getLogger(__name__)

def build(draws=200,search_seeds=5):
    started=time.time()
    for directory in ['data/raw','data/synthetic','data/processed','reports','excel','powerbi','sql','notebooks']:
        (ROOT/directory).mkdir(parents=True,exist_ok=True)
    tables,setups,tracks,weathers,tyres=generate_inputs()
    export_tables(tables,ROOT/'data/synthetic')
    registry=[]; laps=[]; states=[]; segments=[]; sectors=[]; events=[]; warnings=[]; checks=[]; tyre_rows=[]
    stamp=metadata('simulated'); errors=[]
    def add(result,cid,sid,wid=1,tid=2,session=1,group='setup_sweep',drs=True,pair_id=0,lap_number=1):
        rid=len(registry)+1
        registry.append(dict(run_id=rid,circuit_id=cid,setup_id=sid,weather_id=wid,tyre_id=tid,session_id=session,car_id=1,driver_id=1,date_id=20260917,
            comparison_group=group,drs_available=int(drs),pair_id=pair_id,lap_number=lap_number,**stamp))
        laps.append(dict(simulation_lap_id=rid,run_id=rid,**result.summary,**stamp))
        for df,store,idcol in [(result.trace,states,'vehicle_state_id'),(result.segments,segments,'simulation_segment_id'),(result.sectors,sectors,'simulation_sector_id'),(drs_events(result.trace),events,'drs_event_id')]:
            for row in df.to_dict('records'): store.append({idcol:len(store)+1,'run_id':rid,**row})
        for row in result.trace.iloc[::5][['sample_index','distance_m','tyre_wear','tyre_temperature_c','tyre_mu','fuel_kg']].to_dict('records'):
            tyre_rows.append(dict(tyre_state_id=len(tyre_rows)+1,run_id=rid,tyre_id=tid,**row))
        for warning in result.warnings: warnings.append(dict(warning_id=len(warnings)+1,run_id=rid,warning_code=warning,severity='constraint'))
        for check in validate_trace(result): checks.append(dict(validation_id=len(checks)+1,run_id=rid,**check))
        return rid
    log.info('Generating matched setup/circuit/weather sweeps')
    for cid,(name,track) in enumerate(tracks.items(),1):
        for sid,setup in enumerate(setups,1):
            for wid,w in enumerate(weathers,1):
                try:
                    car=CarModel(setup,w); result=car.simulate_lap(track)
                    add(result,cid,sid,wid=wid,session=3 if wid==3 else 1)
                except ValueError as e: errors.append(dict(circuit=name,setup_id=sid,weather_id=wid,error=str(e)))
        log.info('Completed sweep: %s',name)
    # Separate tyre experiment includes matched medium reference already present in sweep.
    track=tracks['Apex Ring']
    for tid,tyre in enumerate(tyres,1): add(CarModel(tyre=tyre).simulate_lap(track),2,1,tid=tid,group='tyre_comparison')
    for sid in [1,2,3]:
        for available in [False,True]: add(CarModel(setups[sid-1]).simulate_lap(track,drs_available=available),2,sid,group='drs_pair',drs=available,pair_id=sid)
    base=CarModel().simulate_lap(track)
    for _ in range(3): add(base,2,1,group='repeatability')
    for lapnum,r in enumerate(simulate_stint(CarModel(),track),1): add(r,2,1,session=2,group='stint',lap_number=lapnum)
    optimization_runs=[]; optimization_rows=[]; winners={}; allsearch=[]
    for cid,(name,track) in enumerate(tracks.items(),1):
        for seed in range(42,42+(search_seeds if cid==2 else 1)):
            log.info('Optimizing %s seed %s',name,seed)
            df=optimize(track,seed=seed,budget=24)
            oid=len(optimization_runs)+1
            optimization_runs.append(dict(optimization_run_id=oid,circuit_id=cid,objective='qualifying',seed=seed,evaluation_count=len(df),**stamp))
            for row in df.to_dict('records'): optimization_rows.append(dict(optimization_result_id=len(optimization_rows)+1,optimization_run_id=oid,**row))
            allsearch.append(df.assign(circuit=name,seed=seed))
            if seed==42:
                best=df.loc[df.feasible].iloc[0]; candidate=Setup(**{k:float(best[k]) for k in CONFIG['bounds']})
                sid=len(tables['dim_setup'])+1
                tables['dim_setup']=pd.concat([tables['dim_setup'],pd.DataFrame([dict(setup_id=sid,setup_name=f'{name} qualifying',**asdict(candidate),**metadata())])],ignore_index=True)
                baseline=CarModel().simulate_lap(track); result=CarModel(candidate).simulate_lap(track)
                add(result,cid,sid,group='recommendation')
                winner={"circuit":name,"setup_id":sid,"setup":asdict(candidate),"baseline":baseline.summary,"candidate":result.summary,
                    "lap_delta_s":result.summary['lap_time_s']-baseline.summary['lap_time_s'],"constraints":constraint_reasons(CarModel(candidate),result),
                    "braking_baseline":braking_test(CarModel()),"braking_candidate":braking_test(CarModel(candidate))}
                no_drs=CarModel(candidate).simulate_lap(track,drs_available=False)
                winner['drs_time_gain_s']=no_drs.summary['lap_time_s']-result.summary['lap_time_s']
                winner['sector_comparison']=sector_comparison(baseline,result).to_dict('records')
                winners[name]=winner
                result.trace.to_csv(ROOT/f'data/processed/recommended_trace_{cid}.csv',index=False)
                baseline.trace.to_csv(ROOT/f'data/processed/baseline_trace_{cid}.csv',index=False)
    # All objectives run through the direct simulator, using the same feasible candidate bank.
    log.info('Comparing race, overtaking, high-downforce and wet objectives')
    shortlist=pd.concat(allsearch).query("circuit == 'Apex Ring' and seed == 42 and feasible").sort_values('lap_time_s').drop_duplicates(list(CONFIG['bounds'])).head(6)
    choices=[Setup()]+[Setup(**{k:float(row[k]) for k in CONFIG['bounds']}) for _,row in shortlist.iterrows()]
    objective_results=[]
    for objective in ['race','overtaking','high_downforce','wet']:
        ev=Evaluator(tracks['Apex Ring'],Weather('Wet',100500,285.15,.68) if objective=='wet' else None,objective)
        for s in choices: ev(s.vector(),'candidate_bank')
        oid=len(optimization_runs)+1
        optimization_runs.append(dict(optimization_run_id=oid,circuit_id=2,objective=objective,seed=42,evaluation_count=len(ev.rows),**stamp))
        for row in ev.rows:
            optimization_rows.append(dict(optimization_result_id=len(optimization_rows)+1,optimization_run_id=oid,pareto=False,**row))
            objective_results.append(row)
    candidate=Setup(**winners['Apex Ring']['setup'])
    log.info('Running %s paired uncertainty draws',draws)
    uncertainty,unc_summary=paired_uncertainty(tracks['Apex Ring'],candidate,draws=draws)
    winners['Apex Ring']['uncertainty']=unc_summary
    uncertainty.to_csv(ROOT/'data/processed/uncertainty.csv',index=False)
    sensitivity(tracks['Apex Ring'],candidate).to_csv(ROOT/'data/processed/sensitivity.csv',index=False)
    pd.DataFrame(objective_results).to_csv(ROOT/'data/processed/objective_comparison.csv',index=False)
    pd.concat(allsearch).to_csv(ROOT/'data/processed/search_evaluations.csv',index=False)
    pd.DataFrame(errors,columns=['circuit','setup_id','weather_id','error']).to_csv(ROOT/'data/processed/rejected_simulations.csv',index=False)
    tables.update({"run_registry":pd.DataFrame(registry),"fact_simulation_lap":pd.DataFrame(laps),"fact_vehicle_state":pd.DataFrame(states),
        "fact_simulation_segment":pd.DataFrame(segments),"fact_simulation_sector":pd.DataFrame(sectors),
        "fact_drs_event":pd.DataFrame(events),"fact_tyre_state":pd.DataFrame(tyre_rows),
        "fact_simulation_warning":pd.DataFrame(warnings,columns=['warning_id','run_id','warning_code','severity']),
        "fact_optimization_run":pd.DataFrame(optimization_runs),"fact_optimization_result":pd.DataFrame(optimization_rows),"fact_model_validation":pd.DataFrame(checks)})
    # Independent measured/source tables are intentionally empty; no fabricated measured laps.
    tables['fact_lap']=pd.DataFrame({'lap_id':pd.Series(dtype='int64'),'run_id':pd.Series(dtype='int64'),'lap_time_s':pd.Series(dtype='float64')})
    tables['fact_sector']=pd.DataFrame({'sector_fact_id':pd.Series(dtype='int64'),'run_id':pd.Series(dtype='int64'),'sector_id':pd.Series(dtype='int64'),'sector_time_s':pd.Series(dtype='float64')})
    tables['fact_telemetry']=pd.DataFrame({'telemetry_id':pd.Series(dtype='int64'),'run_id':pd.Series(dtype='int64'),'sample_index':pd.Series(dtype='int64'),'speed_mps':pd.Series(dtype='float64')})
    tables=ordered_tables(tables)
    export_tables(tables,ROOT/'data/processed/tables')
    data_dictionary(tables).to_csv(ROOT/'reports/data_dictionary.csv',index=False)
    quality_report(tables).to_csv(ROOT/'reports/data_quality.csv',index=False)
    (ROOT/'sql/schema.sql').write_text(schema_sql(tables),encoding='utf-8')
    (ROOT/'sql/seed.sql').write_text(seed_sql(tables),encoding='utf-8')
    json_export(ROOT/'reports/recommendations.json',winners)
    json_export(ROOT/'reports/execution_summary.json',{'elapsed_seconds':time.time()-started,'runs':len(registry),'rejected_simulations':len(errors),'uncertainty':unc_summary,'search_seeds':search_seeds})
    log.info('Loading isolated MySQL database and checking totals')
    try:
        reconciliation=load_mysql(tables); reconciliation.to_csv(ROOT/'reports/mysql_reconciliation.csv',index=False)
        # Repeat load is the idempotence integration test.
        again=load_mysql(tables)
        assert again.matched.all(), 'MySQL duplicate-load reconciliation failed'
        from sqlalchemy import create_engine,text
        from dotenv import load_dotenv
        import os
        load_dotenv(ROOT/'.env'); engine=create_engine(os.environ['MYSQL_URL'])
        with engine.begin() as conn:
            for stmt in (ROOT/'sql/views.sql').read_text().split(';'):
                if stmt.strip(): conn.execute(text(stmt))
        engine.dispose()
    except Exception as exc:
        (ROOT/'reports/mysql_error.txt').write_text(type(exc).__name__+': '+str(exc))
        log.exception('MySQL integration failed; release is not database-verified')
    log.info('Pipeline complete: %s runs, %s state samples',len(registry),len(states))
    return tables,winners

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--draws',type=int,default=200); p.add_argument('--search-seeds',type=int,default=5)
    args=p.parse_args(); configure_logging(); build(args.draws,args.search_seeds)
