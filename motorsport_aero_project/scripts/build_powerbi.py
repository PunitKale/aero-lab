"""Author a PBIP/PBIR/TMDL project with 18 report pages and CSV import partitions.

JSON schemas are validated separately. Power BI Desktop rendering is a distinct
acceptance check and cannot be inferred from successful file generation.
"""
from pathlib import Path
import json,uuid
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'powerbi'; DATA=OUT/'data'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2),encoding='utf-8')

def build():
    DATA.mkdir(parents=True,exist_ok=True)
    source=ROOT/'data/processed/tables'; tables={p.stem:pd.read_csv(p) for p in source.glob('*.csv')}
    runs=tables['run_registry']; keycols=['run_id','circuit_id','setup_id','weather_id','tyre_id','session_id','car_id','date_id','comparison_group']
    # Flatten run dimension keys into facts to build a single-direction star schema.
    for name in ['fact_simulation_lap','fact_simulation_sector','fact_simulation_segment','fact_vehicle_state','fact_drs_event','fact_model_validation','fact_tyre_state']:
        df=tables[name];extra=[c for c in keycols if c=='run_id' or c not in df]
        tables[name]=df.merge(runs[extra],on='run_id',how='left')
    orun=tables['fact_optimization_run'];tables['fact_optimization_result']=tables['fact_optimization_result'].merge(orun[['optimization_run_id','circuit_id','objective','seed']],on='optimization_run_id',suffixes=('','_run'))
    rec=json.loads((ROOT/'reports/recommendations.json').read_text())
    tables['recommendations']=pd.DataFrame([dict(circuit_id=i+1,setup_id=w['setup_id'],baseline_lap_s=w['baseline']['lap_time_s'],candidate_lap_s=w['candidate']['lap_time_s'],lap_delta_s=w['lap_delta_s'],drs_gain_s=w['drs_time_gain_s'],top_speed_gain_mps=w['candidate']['top_speed_mps']-w['baseline']['top_speed_mps'],corner_speed_gain_mps=w['candidate']['high_speed_corner_mps']-w['baseline']['high_speed_corner_mps'],braking_distance_m=w['braking_candidate']['braking_distance_m'],tyre_wear_delta=w['candidate']['tyre_wear_delta'],feasible=int(not w['constraints'])) for i,w in enumerate(rec.values())])
    tables['uncertainty']=pd.read_csv(ROOT/'data/processed/uncertainty.csv').assign(circuit_id=2)
    tables['sensitivity']=pd.read_csv(ROOT/'data/processed/sensitivity.csv').assign(circuit_id=2)
    tables['interventions']=pd.read_csv(ROOT/'data/processed/interventions.csv')
    tables['robust_selection']=pd.read_csv(ROOT/'data/processed/robust_selection.csv').assign(circuit_id=2)
    tables['data_quality']=pd.read_csv(ROOT/'reports/data_quality.csv')
    lap=tables['fact_simulation_lap'];pairs=runs.query("comparison_group=='drs_pair'").merge(lap[['run_id','lap_time_s','top_speed_mps']],on='run_id')
    drs=pairs.query('drs_available==0')[['pair_id','lap_time_s','top_speed_mps']].merge(pairs.query('drs_available==1')[['pair_id','circuit_id','setup_id','lap_time_s','top_speed_mps']],on='pair_id',suffixes=('_off','_on'))
    drs['time_gain_s']=drs.lap_time_s_off-drs.lap_time_s_on;drs['speed_gain_mps']=drs.top_speed_mps_on-drs.top_speed_mps_off
    tables['drs_comparison']=drs
    measures={
      'Best Lap Time':"MIN(fact_simulation_lap[lap_time_s])",'Average Lap Time':"AVERAGE(fact_simulation_lap[lap_time_s])",
      'Lap-Time Delta':"AVERAGE(recommendations[lap_delta_s])",'Best Sector Time':"MIN(fact_simulation_sector[sector_time_s])",
      'Sector Delta':"VAR SelectedTime = AVERAGE(fact_simulation_sector[sector_time_s]) VAR BaselineTime = CALCULATE(AVERAGE(fact_simulation_sector[sector_time_s]), REMOVEFILTERS(dim_setup), dim_setup[setup_id] = 1, fact_simulation_sector[comparison_group] = \"setup_sweep\") RETURN SelectedTime - BaselineTime",
      'Average Downforce':"DIVIDE(SUMX(fact_vehicle_state, fact_vehicle_state[downforce_n] * fact_vehicle_state[dt_s]), SUM(fact_vehicle_state[dt_s]))",
      'Average Drag':"DIVIDE(SUMX(fact_vehicle_state, fact_vehicle_state[drag_n] * fact_vehicle_state[dt_s]), SUM(fact_vehicle_state[dt_s]))",
      'Aero Efficiency':"DIVIDE([Average Downforce], [Average Drag])",
      'Front Aero Balance':"DIVIDE(SUMX(fact_vehicle_state, fact_vehicle_state[front_downforce_n] * fact_vehicle_state[dt_s]), SUMX(fact_vehicle_state, fact_vehicle_state[downforce_n] * fact_vehicle_state[dt_s]))",
      'Rear Aero Balance':"1 - [Front Aero Balance]",'DRS Speed Gain':"AVERAGE(drs_comparison[speed_gain_mps])",'DRS Time Gain':"AVERAGE(drs_comparison[time_gain_s])",
      'Top Speed':"MAX(fact_vehicle_state[speed_mps])",'Average Corner Speed':"CALCULATE(AVERAGE(fact_vehicle_state[speed_mps]), fact_vehicle_state[radius_m] > 0)",
      'Optimization Rank':"IF(HASONEVALUE(fact_optimization_result[optimization_run_id]), RANKX(FILTER(ALLSELECTED(fact_optimization_result), fact_optimization_result[feasible] = TRUE()), CALCULATE(MIN(fact_optimization_result[objective_value])), , ASC, DENSE))",
      'Pareto Status':"IF(SELECTEDVALUE(fact_optimization_result[pareto]), \"Non-dominated\", \"Dominated or multiple\")",
      'Robustness Score':"DIVIDE(COUNTROWS(FILTER(uncertainty, uncertainty[feasible] = TRUE() && uncertainty[delta_s] < 0)), COUNTROWS(uncertainty))",
      'Constraint Violation Count':"COUNTROWS(FILTER(fact_optimization_result, fact_optimization_result[feasible] = FALSE()))",
      'Prediction Error':"BLANK()",'Validated Run Count':"CALCULATE(DISTINCTCOUNT(fact_model_validation[run_id]), fact_model_validation[passed] = TRUE())",
      'Synthetic Data Percentage':"DIVIDE(COUNTROWS(FILTER(fact_simulation_lap, fact_simulation_lap[synthetic_flag] = TRUE())), COUNTROWS(fact_simulation_lap))",
      'Simulated Lap Time':"AVERAGE(fact_simulation_lap[lap_time_s])",'Simulated Sector Time':"AVERAGE(fact_simulation_sector[sector_time_s])",
      'Simulated Top Speed':"[Top Speed]",'Simulated Maximum Downforce':"MAX(fact_vehicle_state[downforce_n])",'Simulated Maximum Drag':"MAX(fact_vehicle_state[drag_n])",
      'Simulated DRS Gain':"[DRS Time Gain]",'Simulated Braking Distance':"AVERAGE(recommendations[braking_distance_m])",
      'Simulated Corner-Speed Gain':"AVERAGE(recommendations[corner_speed_gain_mps])",'Simulated Fuel Effect':"CALCULATE(AVERAGE(interventions[delta_from_reference_s]), interventions[scenario] = \"heavy_fuel\")",'Simulated Tyre Degradation Effect':"CALCULATE(AVERAGE(interventions[delta_from_reference_s]), interventions[scenario] = \"worn_tyre\")",
      'Simulation-versus-reference error':"BLANK()"
    }
    # BLANK measures are deliberate until matched interventions / measured references exist.
    report=OUT/'Aero.Report'; model=OUT/'Aero.SemanticModel'; definition=model/'definition';definition.mkdir(parents=True,exist_ok=True)
    write(OUT/'Aero.pbip',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'Aero.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(report/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Aero.SemanticModel'}}})
    write(model/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    (definition/'database.tmdl').write_text('database\n\tcompatibilityLevel: 1600\n')
    (definition/'model.tmdl').write_text('model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n')
    (definition/'expressions.tmdl').write_text('expression DataFolder = "'+str(DATA).replace('\\','/')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n')
    relationships=[];dimkeys={'circuit_id':'dim_circuit','setup_id':'dim_setup','weather_id':'dim_weather','tyre_id':'dim_tyre','session_id':'dim_session','car_id':'dim_car','date_id':'dim_date','sector_id':'dim_sector'}
    (definition/'tables').mkdir(exist_ok=True)
    for name,df in tables.items():
        # Tables with no observations are imported with headers; types still explicit.
        df.to_csv(DATA/f'{name}.csv',index=False,float_format='%.12g')
        lines=[f'table {name}'];types=[]
        for col in df:
            dtype='boolean' if pd.api.types.is_bool_dtype(df[col]) else 'int64' if pd.api.types.is_integer_dtype(df[col]) else 'double' if pd.api.types.is_numeric_dtype(df[col]) else 'string'
            mtype={'boolean':'type logical','int64':'Int64.Type','double':'type number','string':'type text'}[dtype]
            types.append('{"'+col+'", '+mtype+'}')
            lines += [f'\tcolumn {col}',f'\t\tdataType: {dtype}','\t\tsummarizeBy: none',f'\t\tsourceColumn: {col}','']
        if name=='fact_simulation_lap':
            for title,expression in measures.items(): lines += [f"\tmeasure '{title}' = {expression}",'\t\tformatString: 0.000','']
        lines += [f'\tpartition {name} = m','\t\tmode: import','\t\tsource =','\t\t\tlet',f'\t\t\t\tSource = Csv.Document(File.Contents(DataFolder & "/{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','\t\t\t\tTyped = Table.TransformColumnTypes(Headers, {'+', '.join(types)+'}, "en-US")','\t\t\tin','\t\t\t\tTyped']
        (definition/'tables'/f'{name}.tmdl').write_text('\n'.join(lines),encoding='utf-8')
        if name.startswith('fact_') or name in ['recommendations','uncertainty','sensitivity','drs_comparison','interventions','robust_selection']:
            for key,dim in dimkeys.items():
                if key in df:
                    relationships += [f'relationship {uuid.uuid5(uuid.NAMESPACE_URL,name+key)}',f'\tfromColumn: {name}.{key}',f'\ttoColumn: {dim}.{key}','\tcrossFilteringBehavior: oneDirection','']
    (definition/'relationships.tmdl').write_text('\n'.join(relationships))
    (OUT/'measures.dax').write_text('\n\n'.join(f'{n} = {e}' for n,e in measures.items()),encoding='utf-8')
    specs=[
      ('Project Overview','dim_circuit','circuit_name','Simulated Lap Time','clusteredColumnChart'),
      ('Setup Recommendation','dim_circuit','circuit_name','Lap-Time Delta','clusteredBarChart'),
      ('Aero Performance','fact_vehicle_state','speed_mps','Average Downforce','lineChart'),
      ('Sector and Lap Analysis','dim_sector','sector_name','Simulated Sector Time','clusteredColumnChart'),
      ('DRS Analysis','dim_setup','setup_name','DRS Time Gain','clusteredBarChart'),
      ('Setup Optimization','fact_optimization_result','method','Constraint Violation Count','clusteredColumnChart'),
      ('Pareto Analysis','fact_optimization_result','optimization_result_id','Optimization Rank','tableEx'),
      ('Sensitivity and Uncertainty','sensitivity','parameter',None,'tableEx'),
      ('Model Validation','fact_model_validation','test_name','Validated Run Count','clusteredBarChart'),
      ('Data Quality','data_quality','table_name',None,'tableEx'),
      ('Digital Car Overview','dim_circuit','circuit_name','Simulated Top Speed','clusteredColumnChart'),
      ('Speed and Acceleration','fact_vehicle_state','distance_mps' if False else 'distance_m','Top Speed','lineChart'),
      ('Force Breakdown','fact_vehicle_state','distance_m','Average Drag','lineChart'),
      ('Cornering Performance','dim_circuit','circuit_name','Average Corner Speed','clusteredColumnChart'),
      ('Tyre and Fuel Evolution','fact_tyre_state','distance_m',None,'tableEx'),
      ('DRS Simulation','dim_setup','setup_name','DRS Speed Gain','clusteredBarChart'),
      ('Setup Simulation Comparison','dim_setup','setup_name','Simulated Lap Time','clusteredBarChart'),
      ('Simulation Validation','fact_model_validation','test_name','Validated Run Count','clusteredBarChart')]
    def col(table,name):return {'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}
    def measure(name):return {'Measure':{'Expression':{'SourceRef':{'Entity':'fact_simulation_lap'}},'Property':name}}
    def projection(field,ref):return {'field':field,'queryRef':ref}
    def lit(value):return {'expr':{'Literal':{'Value':value}}}
    rd=report/'definition'
    write(rd/'version.json',{'$schema':BASE+'versionMetadata/1.0.0/schema.json','version':'4.0.0'})
    write(rd/'report.json',{'$schema':BASE+'report/2.0.0/schema.json','themeCollection':{}})
    pageids=[]
    for i,(title,table,category,metric,kind) in enumerate(specs):
        pid=f'page{i+1:02d}';pageids.append(pid);folder=rd/'pages'/pid
        write(folder/'page.json',{'$schema':BASE+'page/2.0.0/schema.json','name':pid,'displayName':title,'displayOption':'FitToPage','height':720,'width':1280})
        def visual(vid,vtype,query,x,y,w,h,label):
            obj={'$schema':BASE+'visualContainer/2.1.0/schema.json','name':vid,'position':{'x':x,'y':y,'z':0,'height':h,'width':w,'tabOrder':0},
                 'visual':{'visualType':vtype,'query':{'queryState':query},'visualContainerObjects':{'title':[{'properties':{'show':lit('true'),'text':lit("'"+label.replace("'","''")+"'")}}]}}}
            write(folder/'visuals'/vid/'visual.json',obj)
        for j,(dim,field) in enumerate([('dim_circuit','circuit_name'),('dim_setup','setup_name'),('dim_weather','name'),('dim_tyre','name')]):
            visual(f'{pid}_s{j}','slicer',{'Values':{'projections':[projection(col(dim,field),dim+'.'+field)]}},16+j*315,10,305,85,field)
        if kind=='tableEx':
            selected=[category]+[c for c in tables[table] if c!=category and (pd.api.types.is_numeric_dtype(tables[table][c]) or c=='status')][:6]
            q={'Values':{'projections':[projection(col(table,c),table+'.'+c) for c in selected]}}
        else:q={'Category':{'projections':[projection(col(table,category),table+'.'+category)]},'Y':{'projections':[projection(measure(metric),'fact_simulation_lap.'+metric)]}}
        visual(pid+'_main',kind,q,16,205,1248,490,title+' — synthetic data')
        for j,m in enumerate(['Best Lap Time','Top Speed','Aero Efficiency','Synthetic Data Percentage']):
            visual(f'{pid}_k{j}','card',{'Values':{'projections':[projection(measure(m),'fact_simulation_lap.'+m)]}},16+j*315,105,305,90,m)
    write(rd/'pages/pages.json',{'$schema':BASE+'pagesMetadata/1.0.0/schema.json','pageOrder':pageids,'activePageName':pageids[0]})
    write(OUT/'page_specifications.json',[dict(page=s[0],table=s[1],category=s[2],measure=s[3],visual=s[4]) for s in specs])
    write(ROOT/'reports/powerbi_build_status.json',{'pages':18,'visuals':162,'format':'PBIP/PBIR + TMDL','desktop_rendered':False,'published':False,'status':'Authored project; schema validation and Desktop acceptance tracked separately'})
    print('Authored Power BI project:',OUT/'Aero.pbip')

if __name__=='__main__':build()
