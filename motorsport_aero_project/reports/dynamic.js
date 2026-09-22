// Draft form state is separate from the last successful Python result.
// One atomic data commit updates charts and replay, preventing mixed-circuit views.
const DATA={recommendations:{},traces:{},geometry:{},numerical_sensitivity:{}};
globalThis.AERO_DATA=DATA;
const selector=document.querySelector('#circuit'),statusEl=document.querySelector('#run-status');
let catalogue,activeId=null,busy=false,requestVersion=0;
const fieldInputs={};
document.querySelectorAll('#setup-form button').forEach(button=>button.disabled=true);
selector.disabled=true;
function status(message,error=false){statusEl.textContent=message;statusEl.classList.toggle('error',error);}
function selectedCircuit(){return catalogue.circuits.find(c=>c.name===selector.value);}
function draft(){const values={};for(const [key,el] of Object.entries(fieldInputs))values[key]=key==='tyre_compound'?el.value:Number(el.value);return values;}
function fill(values){for(const [key,el] of Object.entries(fieldInputs)){el.value=values[key];const slider=document.getElementById('range-'+key);if(slider)slider.value=values[key];}status('Draft updated. Click Run Simulation to apply it.');Research.draftUpdate();}
function defaults(){return {...catalogue.defaults,...selectedCircuit().default_weather};}
function buildFields(){
  const host=document.querySelector('#setup-fields');
  for(const [key,[min,max,step,label]] of Object.entries(catalogue.fields)){
    const div=document.createElement('div');div.className='setup-field';
    const lab=document.createElement('label');lab.htmlFor='input-'+key;lab.textContent=label;
    const slider=document.createElement('input');slider.type='range';slider.id='range-'+key;slider.setAttribute('aria-label',label+' slider');
    const input=document.createElement('input');input.type='number';input.id='input-'+key;input.required=true;
    for(const el of [slider,input]){el.min=min;el.max=max;el.step=step;el.value=catalogue.defaults[key];}
    slider.oninput=()=>{input.value=slider.value;status('Unapplied edits — click Run Simulation.');};
    input.oninput=()=>{slider.value=input.value;status('Unapplied edits — click Run Simulation.');};
    fieldInputs[key]=input;div.append(lab,slider,input);host.append(div);
  }
  const div=document.createElement('div');div.className='setup-field';const label=document.createElement('label');label.textContent='Tyre compound';label.htmlFor='input-tyre_compound';
  const input=document.createElement('select');input.id='input-tyre_compound';catalogue.compounds.forEach(c=>input.add(new Option(c,c)));input.value='medium';input.onchange=()=>status('Unapplied edits — click Run Simulation.');fieldInputs.tyre_compound=input;div.append(label,input);host.append(div);
  document.querySelectorAll('#setup-form button:not(#export-run):not([data-csv])').forEach(button=>button.disabled=false);
  selector.disabled=false;Research.init();
}
async function run(){
  if(busy||!document.querySelector('#setup-form').reportValidity())return;
  const circuit=selectedCircuit(),version=++requestVersion,params=draft();busy=true;
  document.querySelector('#run-simulation').disabled=true;selector.disabled=true;
  document.querySelector('#results').setAttribute('aria-busy','true');
  window.dispatchEvent(new Event('aero-pending'));status('Calculating two 5 m flying laps in Python…');
  try{
    const response=await fetch('/api/simulate',{method:'POST',signal:AbortSignal.timeout(60000),headers:{'Content-Type':'application/json'},body:JSON.stringify({circuit_id:circuit.id,parameters:params})});
    const result=await response.json();if(!response.ok)throw new Error(result.error||'Simulation request failed');
    if(version!==requestVersion)return;
    // Keep object identity: an already-created replay holds this object.
    for(const key of Object.keys(DATA))delete DATA[key];Object.assign(DATA,result);activeId=circuit.id;
    document.querySelector('#results').hidden=false;render();window.dispatchEvent(new Event('aero-data'));
    document.querySelector('#export-run').disabled=false;
    const len=result.geometry[circuit.name].length_m;
    document.querySelector('#circuit-detail').textContent=circuit.name+' · '+len.toFixed(1)+' m processed lap · '+circuit.source.source_license+' · analytical sector thirds · assumed dry weather';
    status('Simulation complete. All views show this run. '+(JSON.stringify(params)!==JSON.stringify(draft())?'You have additional unapplied edits.':''));
  }catch(error){
    // Failed circuit changes cannot leave another circuit’s figures under its name.
    if(activeId){selector.value=catalogue.circuits.find(c=>c.id===activeId).name;}
    status(error.message+'. Last successful result retained. Start with python -m src.realtrack.api --port 8765.',true);
  }finally{busy=false;selector.disabled=false;document.querySelector('#run-simulation').disabled=false;document.querySelector('#results').setAttribute('aria-busy','false');}
}
document.querySelector('#setup-form').onsubmit=e=>{e.preventDefault();run();};
document.querySelector('#reset-setup').onclick=()=>fill(defaults());
document.querySelector('#save-setup').onclick=()=>{if(!document.querySelector('#setup-form').reportValidity())return;try{localStorage.setItem('aero-lab-setup-v2',JSON.stringify(draft()));status('Setup saved in this browser. Load Preset → Saved setup restores it.');}catch{status('Browser storage is unavailable.',true);}};
document.querySelector('#load-preset').onclick=()=>{
  const preset=document.querySelector('#preset').value;let values=defaults();
  if(preset==='low')Object.assign(values,{front_wing_deg:10,rear_wing_deg:12});
  if(preset==='high')Object.assign(values,{front_wing_deg:24,rear_wing_deg:30});
  if(preset==='saved'){try{const saved=JSON.parse(localStorage.getItem('aero-lab-setup-v2'));if(!saved||Object.keys(catalogue.defaults).some(k=>!(k in saved)))throw Error();values=saved;}catch{status('No valid saved setup in this browser.',true);return;}}
  fill(values);
};
document.querySelector('#export-run').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(DATA)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='aero-lab-'+activeId+'-run.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
selector.addEventListener('change',()=>{
  if(!document.querySelector('#setup-form').reportValidity()){
    if(activeId)selector.value=catalogue.circuits.find(c=>c.id===activeId).name;
    status('Correct the invalid setup value before changing circuits.',true);return;
  }
  const weather=selectedCircuit().default_weather;fill({...draft(),...weather});run();
});
document.querySelector('[data-layer="analysis"]').addEventListener('click',()=>requestAnimationFrame(()=>{if(activeId){Plotly.Plots.resize('map');Plotly.Plots.resize('plot');}}));
(async()=>{try{const r=await fetch('/api/circuits');if(!r.ok)throw Error('Circuit API unavailable');catalogue=await r.json();catalogue.circuits.forEach(c=>selector.add(new Option(c.name,c.name)));selector.value=catalogue.circuits.find(c=>c.id===catalogue.default).name;buildFields();fill(defaults());await run();}catch(e){status('Cannot load the Python API. Run python -m src.realtrack.api --port 8765, then refresh. '+e.message,true);}})();
