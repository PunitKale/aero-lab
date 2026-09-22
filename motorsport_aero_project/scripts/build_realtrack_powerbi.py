"""Author a five-page, MySQL-backed Power BI project; Desktop acceptance is separate."""
from pathlib import Path
import json,uuid
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'powerbi/Silverstone';DATA=ROOT/'data/processed/realtrack'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
MEASURES={
 'Lap Time s':'IF(HASONEVALUE(fact_lap[run_id]), MAX(fact_lap[lap_time_s]))',
 'Baseline Lap s':'IF(HASONEVALUE(dim_circuit[circuit_id]), CALCULATE([Lap Time s], REMOVEFILTERS(dim_setup), REMOVEFILTERS(dim_run), dim_run[comparison_role] = "baseline"))',
 'Candidate Lap s':'IF(HASONEVALUE(dim_circuit[circuit_id]), CALCULATE([Lap Time s], REMOVEFILTERS(dim_setup), REMOVEFILTERS(dim_run), dim_run[comparison_role] = "candidate"))',
 'Lap Delta s':'IF(NOT ISBLANK([Candidate Lap s]) && NOT ISBLANK([Baseline Lap s]), [Candidate Lap s] - [Baseline Lap s])',
 'Average Speed kmh':'DIVIDE(SUM(fact_telemetry[step_m]), SUM(fact_telemetry[dt_s])) * 3.6',
 'Max Speed kmh':'MAX(fact_telemetry[speed_mps]) * 3.6',
 'Average Downforce N':'DIVIDE(SUMX(fact_telemetry, fact_telemetry[downforce_n] * fact_telemetry[dt_s]), SUM(fact_telemetry[dt_s]))',
 'Average Drag N':'DIVIDE(SUMX(fact_telemetry, fact_telemetry[drag_n] * fact_telemetry[dt_s]), SUM(fact_telemetry[dt_s]))',
 'Aero Efficiency':'DIVIDE([Average Downforce N], [Average Drag N])',
 'Tyre Wear Change pct':'IF(HASONEVALUE(fact_telemetry[run_id]), SUMX(fact_telemetry, fact_telemetry[tyre_wear_end] - fact_telemetry[tyre_wear]) * 100)',
 'Sector Time s':'IF(HASONEVALUE(fact_sector[run_id]), SUM(fact_sector[sector_time_s]))',
 'Baseline Sector s':'IF(HASONEVALUE(dim_circuit[circuit_id]), CALCULATE([Sector Time s], REMOVEFILTERS(dim_setup), REMOVEFILTERS(dim_run), dim_run[comparison_role] = "baseline"))',
 'Candidate Sector s':'IF(HASONEVALUE(dim_circuit[circuit_id]), CALCULATE([Sector Time s], REMOVEFILTERS(dim_setup), REMOVEFILTERS(dim_run), dim_run[comparison_role] = "candidate"))',
 'Sector Delta s':'IF(NOT ISBLANK([Candidate Sector s]) && NOT ISBLANK([Baseline Sector s]), [Candidate Sector s] - [Baseline Sector s])',
 'Average Acceleration mps2':'DIVIDE(SUMX(fact_telemetry, fact_telemetry[acceleration_mps2] * fact_telemetry[dt_s]), SUM(fact_telemetry[dt_s]))',
 'Map East m':'AVERAGE(fact_telemetry[x_m])','Map North m':'AVERAGE(fact_telemetry[y_m])',
 'Setup Rank':'IF(NOT ISBLANK([Lap Time s]), RANKX(FILTER(ALLSELECTED(dim_setup), NOT ISBLANK(CALCULATE([Lap Time s]))), [Lap Time s], , ASC, DENSE))',
 'Model-generated share':'DIVIDE(CALCULATE(COUNTROWS(fact_telemetry), fact_telemetry[is_synthetic] = TRUE()), COUNTROWS(fact_telemetry))'
}
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2),encoding='utf-8')
def build():
    names=['dim_circuit','dim_setup','dim_sector','dim_run','fact_lap','fact_sector','fact_telemetry'];tables={n:pd.read_csv(DATA/f'{n}.csv') for n in names}
    report=OUT/'Silverstone.Report';model=OUT/'Silverstone.SemanticModel';definition=model/'definition';(definition/'tables').mkdir(parents=True,exist_ok=True)
    write(OUT/'Silverstone.pbip',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'Silverstone.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(report/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Silverstone.SemanticModel'}}})
    write(model/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    (definition/'database.tmdl').write_text('database\n\tcompatibilityLevel: 1600\n')
    (definition/'model.tmdl').write_text('model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n')
    (definition/'expressions.tmdl').write_text('expression MySQLServer = "127.0.0.1:3307" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\nexpression MySQLDatabase = "aero_lab_real" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n')
    relationships=[];keys={'circuit_id':'dim_circuit','setup_id':'dim_setup','sector_id':'dim_sector','run_id':'dim_run'};queries=[]
    for name,df in tables.items():
        lines=[f'table {name}'];types=[]
        for col in df:
            dtype='boolean' if pd.api.types.is_bool_dtype(df[col]) else 'int64' if pd.api.types.is_integer_dtype(df[col]) else 'double' if pd.api.types.is_numeric_dtype(df[col]) else 'string'
            mt={'boolean':'type logical','int64':'Int64.Type','double':'type number','string':'type text'}[dtype];types.append('{"'+col+'", '+mt+'}')
            lines += [f'\tcolumn {col}',f'\t\tdataType: {dtype}','\t\tsummarizeBy: none',f'\t\tsourceColumn: {col}','']
        if name=='fact_lap':
            for title,expression in MEASURES.items():lines += [f"\tmeasure '{title}' = {expression}",'\t\tformatString: 0.000','']
        # Credentials are stored by Power BI, never in M or the project.
        query=f'let\n    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),\n    Rows = Source{{[Schema=MySQLDatabase, Item="{name}"]}}[Data],\n    Typed = Table.TransformColumnTypes(Rows, {{'+', '.join(types)+'}, "en-US")\nin\n    Typed'
        lines += [f'\tpartition {name} = m','\t\tmode: import','\t\tsource =']+['\t\t\t'+line for line in query.splitlines()]
        (definition/'tables'/f'{name}.tmdl').write_text('\n'.join(lines),encoding='utf-8');queries.append('// Query name: '+name+'\n'+query)
        if name.startswith('fact_'):
            for key,dim in keys.items():
                if key in df:relationships += [f'relationship {uuid.uuid5(uuid.NAMESPACE_URL,"realtrack/"+name+key)}',f'\tfromColumn: {name}.{key}',f'\ttoColumn: {dim}.{key}','\tcrossFilteringBehavior: oneDirection','']
    (definition/'relationships.tmdl').write_text('\n'.join(relationships));(OUT/'measures.dax').write_text('\n\n'.join(n+' = '+e for n,e in MEASURES.items()))
    (OUT/'queries.pq').write_text('\n\n'.join(queries));rd=report/'definition'
    write(rd/'version.json',{'$schema':BASE+'versionMetadata/1.0.0/schema.json','version':'4.0.0'});write(rd/'report.json',{'$schema':BASE+'report/2.0.0/schema.json','themeCollection':{}})
    def col(t,c):return {'field':{'Column':{'Expression':{'SourceRef':{'Entity':t}},'Property':c}},'queryRef':t+'.'+c}
    def measure(m):return {'field':{'Measure':{'Expression':{'SourceRef':{'Entity':'fact_lap'}},'Property':m}},'queryRef':'fact_lap.'+m}
    def role(*items):return {'projections':list(items)}
    def chart(cat,metric,series=True):
        q={'Category':role(col(*cat)),'Y':role(measure(metric))}
        if series:q['Series']=role(col('dim_run','comparison_role'))
        return q
    pages=[
      ('Executive Overview', [('clusteredColumnChart',chart(('dim_setup','name'),'Lap Time s',False),'Lap time by assumed setup'),('clusteredBarChart',chart(('dim_sector','name'),'Sector Delta s',False),'Candidate − baseline by analytical sector')]),
      ('Circuit Map & Sectors',[('scatterChart',{'X':role(measure('Map East m')),'Y':role(measure('Map North m')),'Category':role(col('fact_telemetry','point_index')),'Series':role(col('dim_sector','name'))},'Mapped centreline points — set equal x/y metre scales'),('clusteredColumnChart',{'Category':role(col('dim_sector','name')),'Y':role(measure('Baseline Sector s'),measure('Candidate Sector s'))},'Baseline and candidate sector times')]),
      ('Aero Trade-off',[('lineChart',chart(('fact_telemetry','distance_m'),'Average Downforce N'),'Downforce by distance — model-generated'),('lineChart',chart(('fact_telemetry','distance_m'),'Average Drag N'),'Drag by distance — model-generated')]),
      ('Telemetry Analysis',[('lineChart',chart(('fact_telemetry','distance_m'),'Average Speed kmh'),'Speed profile — model-generated'),('lineChart',chart(('fact_telemetry','distance_m'),'Average Acceleration mps2'),'Acceleration / braking — model-generated')]),
      ('Setup Optimizer',[('tableEx',{'Values':role(col('dim_setup','name'),col('dim_setup','front_wing_deg'),col('dim_setup','rear_wing_deg'),measure('Lap Time s'),measure('Setup Rank'),measure('Tyre Wear Change pct'))},'Nine alternatives plus baseline — discrete grid only'),('scatterChart',{'X':role(measure('Average Drag N')),'Y':role(measure('Lap Time s')),'Category':role(col('dim_setup','name'))},'Lap time versus time-weighted drag')])]
    ids=[]
    for i,(title,visuals) in enumerate(pages):
        pid=f'page{i+1:02d}';ids.append(pid);folder=rd/'pages'/pid
        write(folder/'page.json',{'$schema':BASE+'page/2.0.0/schema.json','name':pid,'displayName':title,'displayOption':'FitToPage','height':820,'width':1440})
        def visual(vid,kind,q,x,y,w,h,label):
            title_object = {'properties': {'show': {'expr': {'Literal': {'Value': 'true'}}}, 'text': {'expr': {'Literal': {'Value': "'" + label + "'"}}}}}
            obj = {'$schema': BASE+'visualContainer/2.1.0/schema.json', 'name': vid,
                   'position': {'x':x,'y':y,'z':0,'height':h,'width':w,'tabOrder':0},
                   'visual': {'visualType':kind,'query':{'queryState':q},'visualContainerObjects':{'title':[title_object]}}}
            write(folder/'visuals'/vid/'visual.json',obj)
        for j,(t,c,label) in enumerate([('dim_circuit','name','Circuit — select one'),('dim_setup','name','Setup'),('dim_run','comparison_role','Run role — clear for grid comparison'),('dim_sector','name','Analytical sector')]):visual(pid+f'_s{j}','slicer',{'Values':role(col(t,c))},16+j*356,10,346,90,label)
        for j,m in enumerate(['Baseline Lap s','Candidate Lap s','Lap Delta s','Model-generated share']):visual(pid+f'_k{j}','card',{'Values':role(measure(m))},16+j*356,110,346,90,m)
        for j,(kind,q,label) in enumerate(visuals):visual(pid+f'_v{j}',kind,q,16+j*712,235,696,530,label)
        # Visible on every page, in a native title; no dependency on custom visuals.
        visual(pid+'_disclaimer','card',{'Values':role(measure('Model-generated share'))},16,770,1408,45,'Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.')
    write(rd/'pages/pages.json',{'$schema':BASE+'pagesMetadata/1.0.0/schema.json','pageOrder':ids,'activePageName':ids[0]})
    write(OUT/'page_specifications.json',[{'page':p[0],'visuals':[{'type':v[0],'title':v[2],'query':v[1]} for v in p[1]]} for p in pages])
    geo=tables['fact_telemetry'].drop_duplicates('point_index');xspan=geo.x_m.max()-geo.x_m.min();yspan=geo.y_m.max()-geo.y_m.min()
    write(OUT/'circuit_map_deneb.json',{'$schema':'https://vega.github.io/schema/vega-lite/v5.json','description':'OSM-derived centreline, analytical sectors. Filter to one run. Equal metre scale using fixed aspect ratio.','data':{'name':'dataset'},'width':650,'height':round(650*yspan/xspan),'mark':{'type':'line','strokeWidth':4},'encoding':{'x':{'field':'x_m','type':'quantitative','scale':{'zero':False}},'y':{'field':'y_m','type':'quantitative','scale':{'zero':False}},'order':{'field':'point_index','type':'quantitative'},'color':{'field':'sector_id','type':'nominal'},'tooltip':[{'field':k,'type':'quantitative'} for k in ['point_index','distance_m','speed_kmh','downforce_n']]}})
    print('Authored five-page MySQL-backed Power BI project:',OUT/'Silverstone.pbip')
if __name__=='__main__':build()
