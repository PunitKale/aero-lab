"""Descriptive evidence, not causal attribution or measured confidence."""
from datetime import datetime, timezone
import numpy as np

DISCLAIMER='Analytical model estimates; not CFD, wind-tunnel data or official F1 telemetry.'
def enrich(result):
    name=next(iter(result['recommendations']));rec=result['recommendations'][name]
    traces=result['traces'][name];geo=result['geometry'][name]
    changes={k:{'baseline':v,'candidate':rec['setup'][k]} for k,v in result['baseline_setup'].items() if rec['setup'][k]!=v}
    for role,t in traces.items():
        dt=np.array(t['dt_s']);ds=np.array(t['step_m']);lap=float(dt.sum())
        rec[role].update({'average_speed_kmh':geo['length_m']/lap*3.6,
          'mean_downforce_n':float(np.dot(t['downforce_n'],dt)/lap),
          'mean_drag_n':float(np.dot(t['drag_n'],dt)/lap),
          'downforce_impulse_ns':float(np.dot(t['downforce_n'],dt)),
          'drag_work_j':float(np.dot(t['drag_n'],ds)),
          'confidence':'Unvalidated model estimate — uncertainty not quantified'})
    b,c=traces['baseline'],traces['candidate'];cell_delta=np.array(c['dt_s'])-np.array(b['dt_s'])
    cumulative=np.r_[0,np.cumsum(cell_delta)].tolist()
    grouped={kind:float(sum(d for d,k in zip(cell_delta,c['classification']) if k==kind)) for kind in sorted(set(c['classification']))}
    delta=rec['lap_delta_s'];winner='Tie at displayed precision' if abs(delta)<.0005 else ('Candidate' if delta<0 else 'Baseline')
    insights=[]
    if not changes:insights.append('No setup changes detected. Candidate matches baseline.')
    else:
        insights.append(f'Candidate is {abs(delta):.3f} s {"faster" if delta<0 else "slower"} in this model run.' if abs(delta)>=.0005 else 'Setups differ, but predicted lap times match at displayed precision.')
        largest=max(rec['sector_comparison'],key=lambda s:abs(s['delta_s']))
        insights.append(f"Largest sector difference: S{largest['sector_id']%10}, candidate minus baseline {largest['delta_s']:+.3f} s.")
        insights.append('Cell-time differences by mapped classification: '+', '.join(f'{k.replace("_"," ")} {v:+.3f} s' for k,v in grouped.items())+'. Negative means candidate gains time.')
        if rec['candidate']['cl_down']!=rec['baseline']['cl_down'] or rec['candidate']['cd']!=rec['baseline']['cd']:
            insights.append(f"The submitted aero inputs change model Cl from {rec['baseline']['cl_down']:.3f} to {rec['candidate']['cl_down']:.3f} and Cd from {rec['baseline']['cd']:.3f} to {rec['candidate']['cd']:.3f}. Higher Cl increases available load; higher Cd increases resistance at equal airspeed. These coupled runs do not isolate the causal contribution of an individual input.")
        else:insights.append('Aero coefficients are unchanged; the submitted mass, fuel or tyre changes alter the coupled speed envelope. This comparison does not isolate individual effects.')
    rec['comparison']={'changes':changes,'winner':winner,'insights':insights,'classification_delta_s':grouped,
        'distance_m':b['distance_m']+[geo['length_m']],'cumulative_delta_s':cumulative}
    result['metadata']={'schema_version':2,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'circuit':name,
        'model_version':rec['candidate']['model_version'],'baseline_setup':result['baseline_setup'],'candidate_setup':rec['setup'],
        'weather':{k:rec['setup'][k] for k in ['air_temperature_c','track_temperature_c','wind_speed_mps','wind_direction_deg']},
        'assumptions':['dry conditions','analytical sector thirds','periodic flying lap','estimated tyre and aero model','flat terrain','no measured calibration'],
        'confidence':'Unvalidated; no calibrated error interval available','disclaimer':DISCLAIMER,'source':geo['source']}
    return result
