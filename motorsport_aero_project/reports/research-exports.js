function rows(DATA,name,kind){const roles=["baseline","candidate"];const w=DATA.recommendations[name],meta=DATA.metadata;if(!meta)return[];
   const common={circuit:name,timestamp_utc:meta.timestamp_utc,model_version:meta.model_version,dataset_id:w.dataset_id,is_synthetic:true,disclaimer:meta.disclaimer,confidence:meta.confidence,assumptions:JSON.stringify(meta.assumptions),source_url:meta.source.source_url,source_license:meta.source.source_license,source_sha256:meta.source.snapshot_sha256,verification_status:meta.verification?.assessment??'Not checked',finer_delta_s:meta.verification?.finer_delta_s??'',ranking_resolved:meta.verification?.ranking_resolved??''};
   for(const [k,v] of Object.entries(meta.baseline_setup))common['baseline_'+k]=v;for(const [k,v] of Object.entries(meta.candidate_setup))common['candidate_'+k]=v;
   if(kind==='lap')return roles.map(role=>{const r=w[role];return {...common,role,run_id:r.run_id,lap_time_s:r.lap_time_s,delta_vs_baseline_s:r.lap_time_s-w.baseline.lap_time_s,max_speed_kmh:r.max_speed_mps*3.6,average_speed_kmh:r.average_speed_kmh,mean_downforce_n:r.mean_downforce_n,mean_drag_n:r.mean_drag_n,downforce_impulse_ns:r.downforce_impulse_ns,drag_work_j:r.drag_work_j,tyre_wear_change:r.tyre_wear_change};});
   if(kind==='sector')return w.sector_comparison.flatMap(s=>roles.map(role=>({...common,role,run_id:w[role].run_id,sector:s.sector_id%10,sector_time_s:s['sector_time_s_'+role],candidate_minus_baseline_s:s.delta_s})));
   return roles.flatMap(role=>{const t=DATA.traces[name][role];return t.distance_m.map((_,i)=>({...common,role,run_id:w[role].run_id,...Object.fromEntries(Object.entries(t).map(([k,a])=>[k,a[i]]))}));});
 }

function serialize(rows){if(!rows.length)return '';const keys=Object.keys(rows[0]);const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';return [keys,...rows.map(r=>keys.map(k=>r[k]))].map(row=>row.map(quote).join(',')).join('\r\n');}
globalThis.AeroExports=Object.freeze({rows,serialize});
