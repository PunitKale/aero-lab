import '../time-format.js';
const formatTime=globalThis.AeroTime.format;
export function createUI(panel) {
  panel.innerHTML=`
    <div class="sim-heading"><div><small>AERO LAB / SIMULATION LAYER</small><h2>The setup, in motion.</h2><p id="sim-character"></p></div><span class="sim-tag">SYNTHETIC MODEL · SAVED RUN REPLAY</span></div>
    <div class="sim-summary"><div>Baseline <strong id="sim-baseline-lap"></strong></div><div>Candidate <strong id="sim-candidate-lap"></strong></div><div>Candidate − baseline <strong id="sim-gain"></strong></div></div>
    <p class="sim-help" id="sim-sensitivity" hidden></p>
    <div class="sim-toolbar" aria-label="Replay controls">
      <div class="sim-buttons"><button type="button" data-command="play">▶ Play</button><button type="button" data-command="pause">Ⅱ Pause</button><button type="button" data-command="reset">↺ Reset</button></div>
      <label>Playback <select id="sim-speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></label>
      <label>Camera <select id="sim-camera"><option value="chase">Chase</option><option value="cockpit">Cockpit-style</option><option value="tv">TV / broadcast</option><option value="orbit">Free orbit</option></select></label>
      <label>Focus run <select id="sim-run"><option value="candidate">Candidate</option><option value="baseline">Baseline</option></select></label>
      <label class="sim-check"><input type="checkbox" id="sim-compare"> Compare both cars</label>
    </div>
    <div class="sim-viewport" id="sim-viewport">
      <div class="sim-scene-status"><span id="sim-status">PAUSED</span><span id="sim-focus">CANDIDATE</span></div>
      <div class="sim-map"><canvas id="sim-map" width="230" height="160" aria-label="Illustrative circuit map with baseline and candidate positions"></canvas><span><i class="candidate-dot"></i> Candidate <i class="baseline-dot"></i> Baseline</span></div>
      <div class="sim-caption">Illustrative spline layout · force arrows are conceptual</div>
    </div>
    <div class="sim-hud" aria-label="Live telemetry for focused run">
      ${[['clock','Lap time','min:s'],['sector','Sector',''],['distance','Lap distance','m'],['velocity','Speed','km/h'],['downforce','Downforce','kN'],['drag','Drag','kN'],['acceleration','Acceleration','m/s²'],['wear','Tyre wear','%']].map(([id,label,unit])=>`<div><span>${label}</span><strong id="sim-${id}">—</strong><small>${unit}</small></div>`).join('')}
    </div>
    <div class="sim-details"><div><span>FOCUSED SETUP</span><p id="sim-setup"></p><p id="sim-progress"></p></div><div><span>AERO OVERLAY</span><div class="sim-options"><label><input id="sim-forces" type="checkbox" checked> Force arrows</label><label><input id="sim-flow" type="checkbox"> Airflow particles</label></div><p><b class="sim-down">↓ Green / teal:</b> axle downforce. <b class="sim-drag">← Amber / orange:</b> opposing drag. Stronger force changes arrow length and hue. Shared scale: 1 m per 4 kN + 0.25 m visibility floor.</p></div></div>
    <p class="sim-help" id="sim-helptext">Free orbit: drag to rotate, scroll or pinch to zoom, right-drag to pan. Both cars use the same elapsed clock; lateral comparison offsets are for visibility. Reset starts a flying lap. Each completed lap repeats the saved fuel and tyre state.</p>
    <p class="sim-disclaimer">All vehicle, circuit, and performance data are synthetic. This visualization is a conceptual digital-vehicle model, not CFD or real telemetry.</p>
    <p class="sim-method">The curves illustrate circuit character; they do not reproduce the solver’s corner-radius sequence. Airflow is a speed-driven visual cue, not a fluid simulation. <a href="../docs/simulation_3d.md">Implementation and assumptions</a></p>`;
  const el=id=>panel.querySelector('#sim-'+id),canvas=el('map'),ctx=canvas.getContext('2d');
  let currentName='',mapPoints=[],bounds,geometryKind=null;
  function drawMap(circuit,states,selected,compare) {
    if(currentName!==circuit){currentName=circuit;mapPoints=circuit.curve.getSpacedPoints(300);const xs=mapPoints.map(p=>p.x),zs=mapPoints.map(p=>p.z);bounds={x:Math.min(...xs),z:Math.min(...zs),w:Math.max(...xs)-Math.min(...xs),h:Math.max(...zs)-Math.min(...zs)};}
    const scale=Math.min(200/bounds.w,128/bounds.h),px=p=>[(p.x-bounds.x-bounds.w/2)*scale+115,(p.z-bounds.z-bounds.h/2)*scale+80];
    ctx.clearRect(0,0,230,160);ctx.beginPath();mapPoints.forEach((p,i)=>{const [x,y]=px(p);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.strokeStyle='#79939f';ctx.lineWidth=3;ctx.stroke();
    const [sx,sy]=px(mapPoints[0]);ctx.fillStyle='white';ctx.fillRect(sx-3,sy-3,6,6);
    for(const key of ['baseline','candidate'])if(compare||key===selected){const [x,y]=px(circuit.curve.getPointAt(states[key].phase));ctx.beginPath();ctx.arc(x,y,key===selected?5:4,0,Math.PI*2);ctx.fillStyle=key==='candidate'?'#24cfba':'#a8b9cd';ctx.fill();ctx.strokeStyle='#10263d';ctx.lineWidth=1.5;ctx.stroke();}
  }
  return {host:el('viewport'),bind(replay){panel.querySelectorAll('[data-command]').forEach(b=>b.onclick=()=>replay.command(b.dataset.command));for(const k of ['speed','camera','run'])el(k).onchange=e=>replay.command(k,e.target.value);for(const k of ['compare','forces','flow'])el(k).onchange=e=>replay.command(k,e.target.checked);},
    update({states,selected,elapsed,playing,compare,name,circuit,runs}) {
      if(geometryKind!==circuit.realGeometry){
        geometryKind=circuit.realGeometry;
        panel.querySelector('.sim-disclaimer').textContent=geometryKind?'Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.':'All vehicle, circuit, and performance data are synthetic. This visualization is a conceptual digital-vehicle model, not CFD or real telemetry.';
        panel.querySelector('.sim-caption').textContent=geometryKind?'Public mapped centreline · model-generated force arrows':'Illustrative spline layout · force arrows are conceptual';
        if(geometryKind){panel.querySelector('.sim-method').innerHTML='Silverstone geometry: OpenStreetMap contributors, ODbL; other circuits: Tomislav Bacinger, MIT. Road width, kerbs and scenery are illustrative. Analytical sectors and lap origin are not official timing lines. <a href="dynamic-methodology.html">Methodology & limitations</a>';panel.querySelector('#sim-helptext').textContent='Free orbit: drag to rotate, scroll or pinch to zoom, right-drag to pan. Cars use a shared clock and the latest Python API result. Export live runs separately from the saved MySQL and Power BI research dataset. Comparison lane offsets are illustrative. Reset starts a flying lap; each repeated lap resets the saved tyre state.';}
      }
      const s=states[selected],f=(id,v)=>el(id).textContent=v;
      const sensitivity=globalThis.AERO_DATA?.numerical_sensitivity?.[name];el('sensitivity').hidden=!sensitivity;
      if(sensitivity)f('sensitivity',`Mesh sensitivity: delta ${formatTime(sensitivity.production_delta_s,true)} min:s at ${sensitivity.production_spacing_m} m, ${formatTime(sensitivity.finer_delta_s,true)} min:s at ${sensitivity.finer_spacing_m} m. ${sensitivity.production_delta_s*sensitivity.finer_delta_s<0?'The sign reverses; the setup gain is not robust.':'Numerical comparison only; not measured validation.'}`);
      f('character',name+' · '+circuit.character);f('baseline-lap',formatTime(runs.baseline.duration)+ ' min:s');f('candidate-lap',formatTime(runs.candidate.duration)+ ' min:s');f('gain',formatTime(runs.candidate.duration-runs.baseline.duration,true)+' min:s');
      f('status',playing?'PLAYING':'PAUSED');f('focus',selected.toUpperCase()+(compare?' · SHARED CLOCK':''));
      f('clock',formatTime(s.time));f('sector',s.sector+'/3');f('distance',s.distance.toFixed(0)+' / '+runs[selected].length.toFixed(0));f('velocity',(s.speed*3.6).toFixed(0));f('downforce',(s.downforce/1000).toFixed(2));f('drag',(s.drag/1000).toFixed(2));f('acceleration',s.acceleration.toFixed(2));f('wear',(s.wear*100).toFixed(2));
      f('setup',`Front wing ${s.setup.front_wing_deg.toFixed(2)}° · Rear wing ${s.setup.rear_wing_deg.toFixed(2)}° · Ride height F ${s.setup.front_height_m.toFixed(4)} m / R ${s.setup.rear_height_m.toFixed(4)} m`);
      const lead=states.candidate.totalDistance-states.baseline.totalDistance;
      f('progress',`Session ${formatTime(elapsed)} min:s · Lap ${s.laps+1}`+(compare?` · Candidate ${lead>=0?'ahead':'behind'} by ${Math.abs(lead).toFixed(1)} m`:''));drawMap(circuit,states,selected,compare);
      panel.querySelector('[data-command="play"]').disabled=playing;panel.querySelector('[data-command="pause"]').disabled=!playing;
    }
  };
}
