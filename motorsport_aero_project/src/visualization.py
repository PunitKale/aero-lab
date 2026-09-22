"""Publication figures from canonical run exports. All figures are synthetic."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .config import ROOT
from .schemas import Setup
from .aero_map import coefficients
from .vehicle_model import CarModel

def build_figures():
    out=ROOT/'reports/figures';out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
    base=pd.read_csv(ROOT/'data/processed/baseline_trace_2.csv');rec=pd.read_csv(ROOT/'data/processed/recommended_trace_2.csv')
    search=pd.read_csv(ROOT/'data/processed/search_evaluations.csv');s=search.query("circuit=='Apex Ring' and seed==42 and feasible")
    speed=np.linspace(0,95,96);car=CarModel();a=car.calculate_aero_forces(speed)
    notes=[]
    def finish(name,title,xlabel,ylabel,n,meaning):
        ax=plt.gca();ax.set_title(title,loc='left',fontweight='bold',pad=16);ax.set_xlabel(xlabel);ax.set_ylabel(ylabel)
        if ax.get_legend_handles_labels()[0]:ax.legend(frameon=False)
        plt.gcf().text(.02,.01,f'SYNTHETIC • Apex Ring / dry qualifying unless stated • n={n}',fontsize=8,color='#596575')
        plt.tight_layout(rect=[0,.04,1,1]);plt.savefig(out/f'{name}.png',bbox_inches='tight');plt.close();notes.append((name,title,meaning))
    for key,title,ylabel in [('downforce_n','Downforce increases with airspeed','Downforce (N)'),('drag_n','Drag force across airspeed','Drag (N)')]:
        plt.figure(figsize=(9,4.8));plt.plot(speed,a[key],color='#176B91',label='Baseline setup');finish(key,title,'Air speed (m/s)',ylabel,len(speed),'Speed-squared scaling is modified by the assumed ride-height response.')
    plt.figure(figsize=(9,4.8));plt.plot(speed[1:],a['downforce_n'][1:]/a['drag_n'][1:],label='Baseline');finish('efficiency','Aerodynamic efficiency','Air speed (m/s)','Downforce / drag',95,'A high force ratio does not independently establish the fastest lap.')
    plt.figure(figsize=(9,4.8));plt.plot(speed[1:],a['front_downforce_n'][1:]/a['downforce_n'][1:],label='Front');plt.plot(speed[1:],a['rear_downforce_n'][1:]/a['downforce_n'][1:],label='Rear');finish('balance','Front and rear aerodynamic balance','Air speed (m/s)','Load fraction',95,'Heave sensitivity changes the load split with speed.')
    hf=np.linspace(.02,.06,40);hr=np.linspace(.03,.09,40);x,y=np.meshgrid(hf,hr);cf,cr,cd=coefficients(Setup(),x,y)
    plt.figure(figsize=(9,5.5));plt.pcolormesh(x*1000,y*1000,cf+cr,shading='auto',cmap='viridis');plt.colorbar(label='Downforce coefficient');finish('ride_height_map','Synthetic ride-height aero map','Front ride height (mm)','Rear ride height (mm)',1600,'Floor response has a smooth optimum; out-of-domain extrapolation is rejected.')
    hr=np.linspace(.03,.09,100);cf,cr,cd=coefficients(Setup(),.04,hr)
    plt.figure(figsize=(9,4.8));plt.plot(np.degrees(np.arctan((hr-.04)/3.6)),cf+cr,label='Front height 40 mm');finish('rake','Rake sensitivity at fixed front height','Rake (deg)','Downforce coefficient',100,'Rake is derived from axle ride heights, not optimized independently.')
    for name,cols,title,ylabel in [('speed_trace',['speed_mps'],'Speed by aerodynamic setup','Speed (m/s)'),('tyre_load',['max_wheel_load_n'],'Maximum individual tyre load','Load (N)')]:
        plt.figure(figsize=(10,4.8))
        for frame,label,color in [(base,'Baseline','#606C7D'),(rec,'Recommended','#176B91')]:plt.plot(frame.distance_m,frame[cols[0]],label=label,color=color)
        finish(name,title,'Distance (m)',ylabel,len(rec),'Use matched circuit, weather, tyre and initial fuel conditions.')
    b=base.groupby('sector_id').dt_s.sum();r=rec.groupby('sector_id').dt_s.sum();pos=np.arange(len(b))
    plt.figure(figsize=(9,4.8));plt.bar(pos-.18,b,.36,label='Baseline',color='#8593A2');plt.bar(pos+.18,r,.36,label='Recommended',color='#176B91');plt.xticks(pos,[f'Sector {int(x)%10}' for x in b.index]);finish('sector_times','Sector time comparison','Sector','Time (s)',3,'Sector contributions explain where the lap-time difference originates.')
    delta=r-b;bottom=np.r_[0,np.cumsum(delta)[:-1]]
    plt.figure(figsize=(9,4.8));plt.bar(pos,delta,bottom=bottom,color=['#176B91' if v<0 else '#D46A2A' for v in delta]);plt.xticks(pos,[f'Sector {int(x)%10}' for x in b.index]);plt.axhline(0,color='#4A5563',lw=.8);finish('lap_waterfall','Cumulative lap-time change','Sector contribution','Candidate minus baseline (s)',3,'Negative contributions reduce lap time; bars accumulate to the total delta.')
    tables=ROOT/'data/processed/tables';states=pd.read_csv(tables/'fact_vehicle_state.csv');runs=pd.read_csv(tables/'run_registry.csv');pairs=runs.query("comparison_group=='drs_pair' and setup_id==1")
    plt.figure(figsize=(10,4.8))
    for _,run in pairs.iterrows():
        tr=states.loc[states.run_id==run.run_id];plt.plot(tr.distance_m,tr.speed_mps,label='DRS enabled' if run.drs_available else 'DRS disabled')
    finish('drs_speed','Paired DRS speed comparison','Distance (m)','Speed (m/s)',len(pairs),'DRS closes before braking; benefits are measured at matched distance.')
    # Schematic ring is explicitly not surveyed geometry or the solver's racing line.
    theta=2*np.pi*rec.distance_m/rec.step_m.sum();xx=(700+100*np.cos(3*theta))*np.cos(theta);yy=400*np.sin(theta)
    for name,color,title,label in [('track_speed',rec.speed_mps,'Speed on schematic circuit','Speed (m/s)'),('track_delta',rec.speed_mps-base.speed_mps,'Setup speed change on schematic circuit','Speed difference (m/s)')]:
        plt.figure(figsize=(9,5));plt.scatter(xx,yy,c=color,cmap='viridis' if name=='track_speed' else 'coolwarm',s=35);plt.colorbar(label=label);plt.axis('equal');finish(name,title+' — illustrative geometry','Schematic x (m)','Schematic y (m)',len(rec),'Shape is illustrative and does not claim a surveyed or curvature-consistent racing line.')
    cols=['front_wing_deg','rear_wing_deg','front_height_m','rear_height_m','lap_time_s'];corr=s[cols].corr()
    plt.figure(figsize=(8,6));plt.imshow(corr,vmin=-1,vmax=1,cmap='coolwarm');plt.xticks(range(5),['Front wing','Rear wing','Front height','Rear height','Lap time'],rotation=20);plt.yticks(range(5),['Front wing','Rear wing','Front height','Rear height','Lap time']);plt.colorbar(label='Pearson r');finish('correlation','Search-sample parameter correlations','Parameter','Parameter',len(s),'Search sampling is not randomized causal inference.')
    plt.figure(figsize=(9,5));plt.scatter(s.mean_drag_n,s.lap_time_s,c='#9DA9B5',s=24,label='Feasible candidate');p=s.loc[s.pareto];plt.scatter(p.mean_drag_n,p.lap_time_s,c='#176B91',s=45,label='Non-dominated in 3 objectives');finish('pareto','Lap time versus drag trade-off','Mean drag (N)','Lap time (s)',len(s),'Pareto membership also includes tyre wear; a 2D projection may hide the third objective.')
    sens=pd.read_csv(ROOT/'data/processed/sensitivity.csv');pivot=sens.pivot(index='parameter',columns='direction',values='delta_s')
    plt.figure(figsize=(9,5));plt.barh(pivot.index,pivot[-1],label='−5% of domain',color='#176B91');plt.barh(pivot.index,pivot[1],label='+5% of domain',color='#D46A2A',alpha=.75);plt.axvline(0,color='#555',lw=.7);finish('sensitivity','One-at-a-time setup sensitivity','Lap time change (s)','Parameter',len(sens),'Perturbations are bounded; asymmetry reflects nonlinear and constraint effects.')
    u=pd.read_csv(ROOT/'data/processed/uncertainty.csv');valid=u.loc[u.feasible & u.delta_s.notna()]
    plt.figure(figsize=(9,5));plt.hist(valid.delta_s,bins=24,color='#176B91',alpha=.9);lo,hi=valid.delta_s.quantile([.025,.975]);plt.axvline(lo,ls='--',color='#D46A2A',label='2.5 / 97.5 percentiles');plt.axvline(hi,ls='--',color='#D46A2A');plt.axvline(0,color='#555');finish('uncertainty','Paired uncertainty in setup improvement','Candidate minus baseline (s)','Scenario count',len(valid),'Interval is conditional on assumed uncertainty distributions and feasible draws.')
    # Residuals are surrogate versus direct synthetic simulator, never measured telemetry.
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestRegressor
    x=s[cols[:-1]];y=s.lap_time_s;a1,a2,b1,b2=train_test_split(x,y,random_state=42,test_size=.25)
    model=RandomForestRegressor(n_estimators=100,min_samples_leaf=2,random_state=42).fit(a1,b1);pred=model.predict(a2)
    residual=pd.DataFrame({'reference_lap_s':b2,'predicted_lap_s':pred,'residual_s':pred-b2});residual.to_csv(ROOT/'data/processed/surrogate_residuals.csv',index=False)
    plt.figure(figsize=(9,5));plt.scatter(b2,pred-b2,color='#176B91');plt.axhline(0,color='#555');finish('residuals','Surrogate holdout residuals — synthetic reference','Direct simulator lap time (s)','Prediction minus reference (s)',len(b2),'Holdout consists of entire setup rows; this does not validate real-car accuracy.')
    q=pd.read_csv(ROOT/'reports/data_quality.csv');q=q[q.row_count>0]
    plt.figure(figsize=(10,7));plt.barh(q.table_name.str.replace('fact_','').str.replace('dim_',''),q.row_count,color='#176B91');plt.xscale('log');finish('quality','Released data by table','Row count (log scale)','Table',len(q),'An empty measured table is preserved instead of fabricated measured records.')
    (out/'figure_notes.md').write_text('# Figure interpretation\n\n'+'\n\n'.join(f'## {title}\n\n![{title}]({name}.png)\n\n{meaning}' for name,title,meaning in notes),encoding='utf-8')
    return notes

if __name__=='__main__':build_figures()
