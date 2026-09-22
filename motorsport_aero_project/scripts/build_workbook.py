"""Generate requested Excel engineering workbook using XlsxWriter.

Run with the bundled document Python runtime. The user explicitly requested
openpyxl/XlsxWriter generation code. Formula recalculation is a separate Excel step.
"""
from pathlib import Path
import json
import pandas as pd
import xlsxwriter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/aero-release'; OUT.mkdir(parents=True,exist_ok=True)
TABLES=ROOT/'data/processed/tables'

def read(name): return pd.read_csv(TABLES/f'{name}.csv')

def build():
    winners=json.loads((ROOT/'reports/recommendations.json').read_text())
    conf=json.loads((ROOT/'config/project.json').read_text())
    workbook=xlsxwriter.Workbook(OUT/'Motorsport_Aero_Engineering.xlsx')
    workbook.set_properties({'title':'Motorsport Aerodynamic Setup Optimization','subject':'Synthetic vehicle model engineering analysis','author':'Research project'})
    fmt=workbook.add_format({'font_name':'Arial','font_size':10,'num_format':'0.000'})
    header=workbook.add_format({'font_name':'Arial','bold':True,'font_color':'white','bg_color':'#18334F','text_wrap':True,'valign':'vcenter'})
    title=workbook.add_format({'font_name':'Arial','font_size':16,'bold':True,'font_color':'#18334F'})
    note=workbook.add_format({'font_name':'Arial','font_size':10,'font_color':'#5C6673'})
    inp=workbook.add_format({'font_name':'Arial','font_color':'#245EB2','bg_color':'#EDF4FF','locked':False,'num_format':'0.000'})
    names=['Lap Summary','Setup Comparison','Assumptions','Aero Calculations','Lap-Time Model','Sector Comparison','DRS Analysis','Sensitivity Analysis','Optimization Results','Charts',
        'Vehicle Inputs','Simulation Settings','Segment Simulation','Speed Trace','Force Breakdown','Tyre State','Fuel State','Car Inputs','Circuit Inputs','Sector Inputs','Corner Inputs','Tyre Inputs','Weather Inputs','Aero Map','Setup Scenarios','Data Quality','Python Reconciliation','MySQL Reconciliation','Unit Reference','Project Scope','README']
    sheets={n:workbook.add_worksheet(n) for n in names}; counts={}
    for name,ws in sheets.items():
        ws.hide_gridlines(2); ws.set_default_row(19); ws.set_column(0,0,25);ws.set_column(1,30,19,fmt)
        ws.write(1,0,name,title);ws.write(2,0,'SYNTHETIC RESEARCH MODEL  |  SI units  |  model 1.0.0',note)
        ws.freeze_panes(5,1);ws.set_landscape();ws.fit_to_pages(1,0);ws.repeat_rows(0,4)
        ws.set_footer('&LResearch model – synthetic data&RPage &P of &N')
    def table(name,df,caption=None):
        ws=sheets[name]; df=df.copy().astype(object).where(pd.notna(df),None)
        if caption: ws.write(3,0,caption,note)
        if len(df):
            ws.add_table(4,0,4+len(df),len(df.columns)-1,{'name':'T'+''.join(x for x in name if x.isalnum()),'columns':[{'header':str(c),'header_format':header} for c in df.columns],'data':df.values.tolist(),'style':'Table Style Medium 2'})
        else:
            ws.write_row(4,0,list(df.columns),header);ws.write(5,0,'No records available. Not measured or validated.',note)
        ws.set_row(4,34);counts[name]=len(df)
    summary=pd.DataFrame([{'circuit':k,'baseline_lap_s':w['baseline']['lap_time_s'],'candidate_lap_s':w['candidate']['lap_time_s'],
        'delta_s':w['lap_delta_s'],'candidate_top_speed_mps':w['candidate']['top_speed_mps'],'drs_gain_s':w['drs_time_gain_s'],'setup_id':w['setup_id'],'constraint_violations':len(w['constraints'])} for k,w in winners.items()])
    summary.columns=['Circuit','Baseline (s)','Candidate (s)','Delta (s)','Top speed (m/s)','DRS gain (s)','Setup ID','Violations']
    table('Lap Summary',summary,'Nominal dry qualifying comparison. Candidate minus baseline: negative is faster.')
    integer=workbook.add_format({'font_name':'Arial','num_format':'0'})
    sheets['Lap Summary'].set_column(6,7,15,integer)
    for i in range(len(summary)): sheets['Lap Summary'].write_formula(i+5,3,f'=C{i+6}-B{i+6}',fmt)
    setup=read('dim_setup');table('Setup Comparison',setup.iloc[:,:7])
    table('Setup Scenarios',setup.iloc[:,:7])
    inputs=pd.DataFrame([(k,v,'Assumed generic car') for k,v in conf['car'].items() if isinstance(v,(int,float))],columns=['parameter','value','source'])
    table('Car Inputs',inputs)
    for i,row in inputs.iterrows():
        sheets['Car Inputs'].write(i+5,1,row.value,inp)
        sheets['Car Inputs'].data_validation(i+5,1,i+5,1,{'validate':'decimal','criteria':'>','value':0,'input_title':'Positive SI value','error_title':'Invalid input','error_message':'Enter a positive numeric value.'})
    table('Vehicle Inputs',inputs)
    for i in range(len(inputs)): sheets['Vehicle Inputs'].write_formula(i+5,1,f"='Car Inputs'!B{i+6}",fmt)
    table('Assumptions',pd.DataFrame([['AirDensity',1.225,'kg/m3'],['ReferenceArea',1.5,'m2'],['ClDown',3.,'dimensionless'],['Cd',.9,'dimensionless'],['FrontFraction',.44,'fraction'],['Gravity',9.80665,'m/s2'],['Friction',1.6,'reference mu'],['Mass',810.,'kg'],['Radius',100.,'m'],['Tolerance',1e-6,'relative'],['DRSDragMultiplier',.82,'fraction'],['DRSRearMultiplier',.75,'fraction']],columns=['input','value','unit']))
    for i,name in enumerate(['AirDensity','ReferenceArea','ClDown','Cd','FrontFraction','Gravity','Friction','Mass','Radius','Tolerance','DRSDragMultiplier','DRSRearMultiplier']):
        workbook.define_name(name,f"='Assumptions'!$B${i+6}");sheets['Assumptions'].write(i+5,1,[1.225,1.5,3.,.9,.44,9.80665,1.6,810.,100.,1e-6,.82,.75][i],inp)
    sheets['Assumptions'].data_validation('B6:B17',{'validate':'decimal','criteria':'>','value':0})
    columns=['speed_mps','q_pa','downforce_n','drag_n','front_n','rear_n','front_fraction','rear_fraction','aero_efficiency','drag_power_w','DRS_drag_n','drag_reduction_n']
    table('Aero Calculations',pd.DataFrame([[v]+[None]*11 for v in range(0,101,5)],columns=columns),'Independent scalar equations with constant coefficients. Live editable assumptions.')
    for row in range(6,27):
        fs=[f'=0.5*AirDensity*A{row}^2',f'=B{row}*ReferenceArea*ClDown',f'=B{row}*ReferenceArea*Cd',f'=C{row}*FrontFraction',f'=C{row}-E{row}',f'=IF(C{row}=0,"n.a.",E{row}/C{row})',f'=IF(C{row}=0,"n.a.",F{row}/C{row})',f'=IF(D{row}=0,"n.a.",C{row}/D{row})',f'=D{row}*A{row}',f'=D{row}*DRSDragMultiplier',f'=D{row}-K{row}']
        for j,f in enumerate(fs,1): sheets['Aero Calculations'].write_formula(row-1,j,f,fmt)
    # Simple independent limiting cases, not a second hidden lap simulator.
    examples=[['Initial speed',80.,'m/s'],['Target speed',30.,'m/s'],['Constant deceleration',15.,'m/s2'],['Braking distance',None,'m'],['Braking time',None,'s'],['Straight distance',500.,'m'],['Constant straight speed',50.,'m/s'],['Straight time',None,'s'],['Mechanical corner speed',None,'m/s']]
    table('Lap-Time Model',pd.DataFrame(examples,columns=['quantity','value','unit']),'Limiting-case equations; the full integrated lap is imported in Lap Summary.')
    for cell,formula in {'B9':'=(B6^2-B7^2)/(2*B8)','B10':'=(B6-B7)/B8','B13':'=B11/B12','B14':'=SQRT(Friction*Gravity*Radius)'}.items():sheets['Lap-Time Model'].write_formula(cell,formula,fmt)
    sectors=pd.DataFrame(winners['Apex Ring']['sector_comparison']);table('Sector Comparison',sectors)
    for i in range(len(sectors)): sheets['Sector Comparison'].write_formula(i+5,3,f'=C{i+6}-B{i+6}',fmt)
    trace=pd.read_csv(ROOT/'data/processed/recommended_trace_2.csv')
    table('Speed Trace',trace[['distance_m','time_s','dt_s','speed_mps','exit_speed_mps','acceleration_mps2','gear','drs']],'Apex Ring qualifying recommendation. Integrated simulation snapshot.')
    table('Force Breakdown',trace[['distance_m','engine_force_n','brake_force_n','drag_n','rolling_force_n','downforce_n','front_tyre_load_n','rear_tyre_load_n']])
    table('Tyre State',trace[['distance_m','tyre_wear','tyre_temperature_c','tyre_mu','max_wheel_load_n']])
    table('Fuel State',trace[['distance_m','fuel_kg','mass_kg']])
    table('Segment Simulation',trace.groupby(['segment_id','sector_id'],as_index=False).agg(segment_time_s=('dt_s','sum'),length_m=('step_m','sum'),top_speed_mps=('speed_mps','max')))
    registry=read('run_registry');laps=read('fact_simulation_lap');combined=registry.merge(laps[['run_id','lap_time_s','top_speed_mps']],on='run_id')
    drs=combined.query("comparison_group == 'drs_pair'")
    pairs=drs.query('drs_available == 0')[['pair_id','lap_time_s','top_speed_mps']].merge(drs.query('drs_available == 1')[['pair_id','lap_time_s','top_speed_mps']],on='pair_id',suffixes=('_off','_on'))
    pairs['time_gain_s']=pairs.lap_time_s_off-pairs.lap_time_s_on;pairs['top_speed_gain_mps']=pairs.top_speed_mps_on-pairs.top_speed_mps_off
    table('DRS Analysis',pairs,'Paired same-setup, same-weather laps; gain is off minus on.')
    for i in range(len(pairs)): sheets['DRS Analysis'].write_formula(i+5,5,f'=B{i+6}-D{i+6}',fmt)
    table('Sensitivity Analysis',pd.read_csv(ROOT/'data/processed/sensitivity.csv'),'Apex Ring; ±5% parameter-domain perturbation. Full simulator snapshots.')
    opt=pd.read_csv(ROOT/'data/processed/search_evaluations.csv');table('Optimization Results',opt[['circuit','seed','method','front_wing_deg','rear_wing_deg','front_height_m','rear_height_m','lap_time_s','objective_value','feasible','pareto','constraint_reasons']])
    mapping={'Circuit Inputs':'dim_circuit','Sector Inputs':'dim_sector','Corner Inputs':'dim_corner','Tyre Inputs':'dim_tyre','Weather Inputs':'dim_weather','Aero Map':'fact_aero_map'}
    for sheet,name in mapping.items():
        df=read(name);df=df[[c for c in df if c not in ['generation_timestamp','model_version','data_version','random_seed','validation_status']]]
        table(sheet,df)
    table('Simulation Settings',pd.DataFrame([(k,v) for k,v in conf['simulation'].items()],columns=['setting','value']))
    table('Data Quality',pd.read_csv(ROOT/'reports/data_quality.csv'),'Missing cells in rejected evaluations are explicit unavailable outputs, not zero.')
    if (ROOT/'reports/mysql_reconciliation.csv').exists():table('MySQL Reconciliation',pd.read_csv(ROOT/'reports/mysql_reconciliation.csv'))
    else:table('MySQL Reconciliation',pd.DataFrame([['Not executed','Configure MySQL and rerun pipeline']],columns=['status','action']))
    checks=pd.DataFrame([['Dynamic pressure',1531.25,None,None],['Downforce',6890.625,None,None],['Drag',2067.1875,None,None],['Drag power',103359.375,None,None],['Lap sector sum',winners['Apex Ring']['candidate']['lap_time_s'],None,None]],columns=['quantity','python_reference','excel_result','difference'])
    table('Python Reconciliation',checks,'Recalculate with Excel; cached Python values are not used as proof.')
    for i,ref in enumerate(["'Aero Calculations'!B16","'Aero Calculations'!C16","'Aero Calculations'!D16","'Aero Calculations'!J16","SUM('Sector Comparison'!C6:C8)"]):
        sheets['Python Reconciliation'].write_formula(i+5,2,'='+ref,fmt);sheets['Python Reconciliation'].write_formula(i+5,3,f'=C{i+6}-B{i+6}',fmt)
    sheets['Python Reconciliation'].conditional_format('D6:D10',{'type':'cell','criteria':'not between','minimum':-1e-6,'maximum':1e-6,'format':workbook.add_format({'bg_color':'#FDE6E3','font_color':'#9C2721'})})
    table('Unit Reference',pd.DataFrame([['Speed','m/s','km/h = m/s × 3.6'],['Force','N','Positive downforce convention'],['Pressure','Pa','Absolute local static pressure'],['Temperature','K','Kelvin = Celsius + 273.15'],['Angles','rad','Setup UI wing angles in degrees'],['Time','s','Negative candidate delta means faster']],columns=['quantity','storage_unit','definition']))
    table('Project Scope',pd.DataFrame([['Implemented','Quasi-static synthetic car, lap/stint solver, constraints and search'],['Assumed','Aero response, tyre/load coefficients, suspension compliance and DRS policy'],['Not measured','No proprietary telemetry; no real-car accuracy claim'],['Future','Transient suspension, full slip/thermal tyres, calibrated aero and current regulation model']],columns=['status','description']))
    table('README',pd.DataFrame([['Purpose','Compare synthetic aerodynamic setups and inspect engineering equations'],['Inputs','Blue cells are editable; formula cells are protected without a password'],['Refresh','Run the Python pipeline and rebuild this workbook to refresh simulation snapshots'],['Live formulas','Aero Calculations and limiting-case examples recalculate with editable inputs'],['Synthetic status','All simulations and aerodynamic data are synthetic'],['Comparison','Match circuit, weather, tyre, fuel and session before comparing times'],['Reconciliation','Python Reconciliation is checked after actual Excel recalculation'],['Limitations','No measured-car validation; do not use as a real-car safety approval']],columns=['topic','guidance']))
    for n in ['README','Project Scope']:sheets[n].set_column(1,1,105)
    table('Charts',pd.DataFrame({'speed_mps':list(range(0,101,5)),'downforce_n':[None]*21,'drag_n':[None]*21}))
    for i in range(21):
        for j,col in [(1,'C'),(2,'D')]:sheets['Charts'].write_formula(i+5,j,f"='Aero Calculations'!{col}{i+6}",fmt)
    chart=workbook.add_chart({'type':'scatter','subtype':'straight'})
    for col,label,color in [(1,'Downforce','#176B91'),(2,'Drag','#D66A29')]:chart.add_series({'name':label,'categories':['Charts',5,0,25,0],'values':['Charts',5,col,25,col],'line':{'color':color,'width':2}})
    chart.set_title({'name':'Force versus airspeed — constant coefficients'});chart.set_x_axis({'name':'Air speed (m/s)'});chart.set_y_axis({'name':'Force (N)','min':0});chart.set_legend({'position':'bottom'});chart.set_size({'width':720,'height':390});sheets['Charts'].insert_chart('E5',chart)
    line=workbook.add_chart({'type':'scatter','subtype':'straight'});line.add_series({'name':'Recommended setup','categories':['Speed Trace',5,0,4+len(trace),0],'values':['Speed Trace',5,3,4+len(trace),3],'line':{'color':'#176B91'}})
    line.set_title({'name':'Apex Ring speed trace — synthetic'});line.set_x_axis({'name':'Distance (m)'});line.set_y_axis({'name':'Speed (m/s)'});sheets['Speed Trace'].insert_chart('J5',line)
    bar=workbook.add_chart({'type':'column'})
    for col,label in [(1,'Baseline'),(2,'Candidate')]:bar.add_series({'name':label,'categories':['Lap Summary',5,0,7,0],'values':['Lap Summary',5,col,7,col]})
    bar.set_title({'name':'Circuit-specific qualifying lap time'});bar.set_y_axis({'name':'Lap time (s)','min':0});sheets['Lap Summary'].insert_chart('A12',bar,{'x_scale':1.6,'y_scale':1.2})
    for name,ws in sheets.items():
        ws.protect('',{'autofilter':True,'sort':True,'select_locked_cells':True,'select_unlocked_cells':True})
        ws.set_tab_color('#18334F' if name in ['Lap Summary','Setup Comparison','Charts'] else '#6D8CAC' if name=='Assumptions' else '#D5DDE5')
    sheets['Lap Summary'].activate();workbook.close()
    (ROOT/'reports/workbook_manifest.json').write_text(json.dumps({'sheet_count':len(sheets),'rows':counts,'formula_recalculation':'pending Excel verification'},indent=2))
    print(OUT/'Motorsport_Aero_Engineering.xlsx')

if __name__=='__main__':build()
