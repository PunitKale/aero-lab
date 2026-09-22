// Keep the analytics layer lightweight: Three.js loads only on first simulation selection.
let replay=null,loading=null;
const panel=document.querySelector('#simulation-layer'),analysis=document.querySelector('#analysis-layer');
const tabs=[...document.querySelectorAll('[data-layer]')];
async function switchLayer(layer) {
  const simulation=layer==='simulation';panel.hidden=!simulation;analysis.hidden=simulation;
  tabs.forEach(b=>{b.classList.toggle('active',b.dataset.layer===layer);b.setAttribute('aria-selected',String(b.dataset.layer===layer));});
  if(!simulation){replay?.setActive(false);if(globalThis.Plotly)Plotly.Plots.resize('plot');return;}
  if(!globalThis.AERO_DATA?.recommendations?.[document.querySelector('#circuit').value])return;
  if(!loading)loading=(async()=>{
    const [{createReplay},{createUI}]=await Promise.all([import('./replay.js'),import('./ui.js')]);
    const ui=createUI(panel);replay=createReplay(ui.host,globalThis.AERO_DATA,state=>ui.update(state));ui.bind(replay);
    replay.setCircuit(document.querySelector('#circuit').value);
  })();
  try{await loading;replay.setActive(!panel.hidden&&!document.hidden);}
  catch(error){console.error(error);panel.replaceChildren();const message=document.createElement('p');message.className='sim-error';message.textContent='The 3D renderer could not start. Use a WebGL2-capable browser with hardware acceleration, and open this page through the local Python viewer. The Analysis tab remains available. Details: '+error.message;panel.append(message);loading=null;}
}
tabs.forEach(b=>b.addEventListener('click',()=>switchLayer(b.dataset.layer)));
window.addEventListener('aero-pending',()=>replay?.command('pause'));
// The retained fictional dashboard still switches already-saved runs directly.
if(!document.querySelector('#setup-form'))document.querySelector('#circuit').addEventListener('change',()=>replay?.setCircuit(document.querySelector('#circuit').value));
window.addEventListener('aero-data',()=>{replay?.setCircuit(document.querySelector('#circuit').value,true);if(!panel.hidden||location.hash==='#simulation')switchLayer('simulation');});
document.addEventListener('visibilitychange',()=>replay?.setActive(!document.hidden&&!panel.hidden));
// Back/forward cache keeps the document alive; do not destroy its renderer.
window.addEventListener('pagehide',event=>event.persisted?replay?.setActive(false):replay?.dispose());
window.addEventListener('pageshow',event=>{if(event.persisted)replay?.setActive(!document.hidden&&!panel.hidden);});
if(location.hash==='#simulation')switchLayer('simulation');
