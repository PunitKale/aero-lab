// Verify the committed run, never unsimulated draft edits.
const verificationButton=document.getElementById('verify-prediction');
window.addEventListener('aero-data',()=>{verificationButton.disabled=false;document.getElementById('verification-result').textContent='Not checked. Repeat this comparison at 2.5 m spacing to assess numerical sensitivity.';const e=DATA.metadata?.execution;document.getElementById('execution-note').textContent=e?'Python computation: '+e.elapsed_ms+' ms · '+e.reused_laps+'/2 exact lap results reused.':'';});
verificationButton.onclick=async()=>{
 if(busy||!activeId)return;busy=true;verificationButton.disabled=true;selector.disabled=true;document.getElementById('run-simulation').disabled=true;
 const name=selector.value,rec=DATA.recommendations[name],output=document.getElementById('verification-result');
 output.textContent='Checking 5 m against 2.5 m spacing…';
 try{const response=await fetch('/api/verify',{method:'POST',signal:AbortSignal.timeout(60000),headers:{'Content-Type':'application/json'},body:JSON.stringify({circuit_id:activeId,parameters:rec.setup})});const check=await response.json();if(!response.ok)throw Error(check.error||'Check failed');if(check.dataset_id!==rec.dataset_id)throw Error('Model version changed. Run a new simulation before verification.');
 DATA.metadata.verification=check;
 output.textContent=check.assessment+'. Candidate − baseline: '+check.production_delta_s.toFixed(3)+' s at 5 m; '+check.finer_delta_s.toFixed(3)+' s at 2.5 m. Baseline lap changes by '+check.lap_shift_s.baseline.toFixed(3)+' s; candidate by '+check.lap_shift_s.candidate.toFixed(3)+' s. '+check.disclaimer;
 document.getElementById('confidence-detail').textContent='Baseline and candidate: unvalidated model estimates. '+check.assessment+'. Real-world accuracy has not been measured.';
 document.getElementById('sensitivity-note').textContent=output.textContent;
 if(!check.identical_setups&&!check.ranking_resolved){document.getElementById('winner').textContent='Inconclusive across resolutions';document.getElementById('winner-card').className='metric neutral';}
 const note=document.createElement('li');note.textContent='Numerical check: '+check.assessment+'. Treat the earlier gains/losses as results of the 5 m model only.';document.getElementById('insights-list').append(note);
 DATA.numerical_sensitivity[name]=check;
 }catch(error){output.textContent='Prediction check unavailable: '+error.message+'. No accuracy claim can be made.';}
 finally{busy=false;verificationButton.disabled=false;selector.disabled=false;document.getElementById('run-simulation').disabled=false;}
};
