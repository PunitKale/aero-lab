import * as THREE from 'three';
import {createRun,sampleRun} from './telemetry.mjs';
import {createCircuit,disposeGroup} from './circuits.js';
import {createCar} from './car.js';
import {createScene} from './scene.js';

export function createReplay(host,data,onTelemetry) {
  const view=createScene(host);let circuit,runs,cars,name,elapsed=0,playing=false,active=false,multiplier=1,mode='chase',selected='candidate',compare=false,forces=true,flow=false,last=null,hudTime=0,snap=true;
  const point=new THREE.Vector3(),tangent=new THREE.Vector3();
  function setCircuit(next,force=false) {
    if(next===name&&!force)return;
    if(circuit)disposeGroup(circuit.group);if(cars)Object.values(cars).forEach(c=>disposeGroup(c.group));
    name=next;const rec=data.recommendations[name];
    runs={baseline:createRun(data.traces[name].baseline,data.baseline_setup),candidate:createRun(data.traces[name].candidate,rec.setup)};
    circuit=createCircuit(name,runs.baseline.length,data.geometry?.[name]);view.scene.add(circuit.group);
    cars={baseline:createCar(runs.baseline.setup,0x96a9bc),candidate:createCar(runs.candidate.setup,0x24cfba)};
    Object.values(cars).forEach(c=>view.scene.add(c.group));elapsed=0;playing=false;last=null;snap=true;hudTime=0;
  }
  function frame(timestamp) {
    if(!active)return;
    // No background catch-up or large jump when the tab was suspended.
    const dt=last===null?0:Math.min((timestamp-last)/1000,.1);last=timestamp;
    if(playing)elapsed+=dt*multiplier;
    const states={};
    for(const key of ['baseline','candidate']) {
      const state=sampleRun(runs[key],elapsed);states[key]=state;
      circuit.curve.getPointAt(state.phase,point);circuit.curve.getTangentAt(state.phase,tangent);
      const car=cars[key];car.group.position.copy(point);car.group.position.y=.08;
      car.group.rotation.y=Math.atan2(tangent.x,tangent.z);
      car.group.visible=compare||key===selected;
      // Comparison lanes are presentation offsets, not alternate physics trajectories.
      if(compare){const offset=key==='candidate'?1.7:-1.7;car.group.position.x-=tangent.z*offset;car.group.position.z+=tangent.x*offset;}
      car.update(state,playing?dt*multiplier:0,elapsed,forces&&key===selected,flow&&key===selected);
    }
    // Cockpit camera is ahead of the helmet, looking over the nose and front wheels.
    view.updateCamera(mode,cars[selected].group,dt,snap);snap=false;
    view.renderer.render(view.scene,view.camera);
    if(timestamp-hudTime>=80||hudTime===0){onTelemetry({states,selected,elapsed,playing,compare,name,circuit,runs});hudTime=timestamp;}
  }
  function setActive(value){active=value;last=null;view.renderer.setAnimationLoop(value?frame:null);}
  return {
    setCircuit,setActive,
    command(key,value){if(key==='play')playing=true;if(key==='pause')playing=false;if(key==='reset'){elapsed=0;playing=false;snap=true;hudTime=0;}
      if(key==='speed')multiplier=Number(value);if(key==='camera'){mode=value;snap=true;}if(key==='run'){selected=value;snap=true;hudTime=0;}if(key==='compare')compare=value;if(key==='forces')forces=value;if(key==='flow')flow=value;},
    dispose(){setActive(false);if(circuit)disposeGroup(circuit.group);if(cars)Object.values(cars).forEach(c=>disposeGroup(c.group));view.dispose();}
  };
}
