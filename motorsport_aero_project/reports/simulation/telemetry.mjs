// Pure replay math: exported independently so it can be tested without WebGL.
export function createRun(trace, setup) {
  const required = ['time_s','dt_s','distance_m','step_m','speed_mps','exit_speed_mps',
    'downforce_n','front_downforce_n','rear_downforce_n','drag_n','acceleration_mps2','tyre_wear','sector_id'];
  const n = trace.time_s?.length;
  if (!n || required.some(k => trace[k]?.length !== n || trace[k].some(v => !Number.isFinite(v))))
    throw new Error('Missing or invalid saved telemetry.');
  for (let i=0; i<n; i++) {
    if (trace.dt_s[i]<=0 || trace.step_m[i]<=0 || trace.speed_mps[i]<0 || trace.exit_speed_mps[i]<0)
      throw new Error('Invalid replay cell.');
    if (i && (Math.abs(trace.time_s[i]-trace.time_s[i-1]-trace.dt_s[i-1])>1e-6 ||
      Math.abs(trace.distance_m[i]-trace.distance_m[i-1]-trace.step_m[i-1])>1e-6))
      throw new Error('Non-contiguous saved telemetry.');
  }
  return {trace, setup, duration:trace.time_s[n-1]+trace.dt_s[n-1], length:trace.distance_m[n-1]+trace.step_m[n-1]};
}

export function sampleRun(run, elapsed) {
  if (!Number.isFinite(elapsed) || elapsed < 0) throw new Error('Replay time must be finite and nonnegative.');
  const {trace:t,duration,length} = run;
  const laps=Math.floor(elapsed/duration), time=elapsed-laps*duration;
  let lo=0, hi=t.time_s.length-1;
  while(lo<hi) { const m=Math.ceil((lo+hi)/2); if(t.time_s[m]<=time) lo=m; else hi=m-1; }
  const i=lo, f=Math.min(1,Math.max(0,(time-t.time_s[i])/t.dt_s[i]));
  // Integrate linearly changing cell speed, normalized to the saved step length.
  // Lumped gear-shift losses stretch the cell clock; pose is illustrative within a cell.
  const a=t.speed_mps[i], b=t.exit_speed_mps[i];
  const progress=(a+b)>0 ? (2*a*f+(b-a)*f*f)/(a+b) : f;
  const distance=t.distance_m[i]+progress*t.step_m[i];
  // Interpolate saved cell forces for the visual overlay; analysis uses original cells.
  const value=k=>t[k][i]+(t[k][(i+1)%t[k].length]-t[k][i])*f;
  return {time,laps,distance,totalDistance:laps*length+distance,phase:distance/length,
    speed:a+(b-a)*f, downforce:value('downforce_n'), frontForce:value('front_downforce_n'),
    rearForce:value('rear_downforce_n'), drag:value('drag_n'), acceleration:value('acceleration_mps2'),
    wear:t.tyre_wear[i]+((t.tyre_wear_end?.[i]??t.tyre_wear[i])-t.tyre_wear[i])*f, sector:t.sector_id[i]%10, index:i, setup:run.setup};
}
