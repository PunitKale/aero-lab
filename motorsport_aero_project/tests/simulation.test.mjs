import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRun,sampleRun} from '../reports/simulation/telemetry.mjs';
import {layouts} from '../reports/simulation/circuit-definitions.mjs';
import * as THREE from '../reports/vendor/three/three.module.js';

const html=readFileSync(new URL('../reports/legacy_dashboard.html',import.meta.url),'utf8');
const data=JSON.parse(html.match(/const DATA=(.*?);globalThis.AERO_DATA=DATA;/s)[1]);
for(const name of Object.keys(layouts)) for(const key of ['baseline','candidate']) {
  test(`${name}: ${key} preserves saved timing, distance, forces and sectors`,()=>{
    const t=data.traces[name][key],w=data.recommendations[name];
    const run=createRun(t,key==='candidate'?w.setup:data.baseline_setup);
    assert.ok(Math.abs(run.duration-w[key].lap_time_s)<1e-9);
    assert.equal(run.length,w[key].distance_m);
    let last=-1;
    for(let i=0;i<t.time_s.length;i++) {
      const s=sampleRun(run,t.time_s[i]);assert.equal(s.index,i);assert.equal(s.sector,t.sector_id[i]%10);
      assert.equal(s.distance,t.distance_m[i]);assert.equal(s.speed,t.speed_mps[i]);assert.equal(s.downforce,t.downforce_n[i]);assert.equal(s.drag,t.drag_n[i]);
      const nearEnd=sampleRun(run,t.time_s[i]+t.dt_s[i]-1e-9);assert.ok(Math.abs(nearEnd.distance-t.distance_m[i]-t.step_m[i])<1e-5);
      for(let j=0;j<4;j++){const s=sampleRun(run,t.time_s[i]+j*t.dt_s[i]/4);assert.ok(s.distance>=last);last=s.distance;assert.ok(s.phase>=0&&s.phase<1);}
    }
    const wrap=sampleRun(run,run.duration);assert.equal(wrap.laps,1);assert.equal(wrap.distance,0);assert.equal(wrap.time,0);
    assert.equal(sampleRun(run,run.duration*3+.2).laps,3);
  });
}
test('Downforce Circuit reproduces requested setup, laps and comparison lead',()=>{
  const w=data.recommendations['Downforce Circuit'];
  assert.equal(w.setup.front_wing_deg.toFixed(2),'12.48');assert.equal(w.setup.rear_wing_deg.toFixed(2),'10.04');
  assert.equal(w.setup.front_height_m.toFixed(4),'0.0384');assert.equal(w.setup.rear_height_m.toFixed(4),'0.0551');
  assert.equal(w.baseline.lap_time_s.toFixed(3),'27.654');assert.equal(w.candidate.lap_time_s.toFixed(3),'26.517');assert.equal(w.lap_delta_s.toFixed(3),'-1.137');
  const t=data.traces['Downforce Circuit'],b=createRun(t.baseline,data.baseline_setup),c=createRun(t.candidate,w.setup);
  assert.ok(sampleRun(c,c.duration).totalDistance>sampleRun(b,c.duration).totalDistance);
});
test('Invalid data and invalid clocks are rejected',()=>{
  assert.throws(()=>createRun({},{}));
  const t=structuredClone(data.traces['Apex Ring'].candidate);t.dt_s[1]=-1;assert.throws(()=>createRun(t,{}));
  const r=createRun(data.traces['Apex Ring'].candidate,{});assert.throws(()=>sampleRun(r,-1));assert.throws(()=>sampleRun(r,NaN));
});
test('All layouts close smoothly and scale to lap distance without centerline intersections',()=>{
  const cross=(a,b,c)=>(b.x-a.x)*(c.z-a.z)-(b.z-a.z)*(c.x-a.x);
  for(const [name,def] of Object.entries(layouts)){
    const p=def.points.map(([x,z])=>new THREE.Vector3(x,0,z));let curve=new THREE.CatmullRomCurve3(p,true,'centripetal');
    const length=data.recommendations[name].baseline.distance_m;const scale=length/curve.getLength();p.forEach(v=>v.multiplyScalar(scale));curve=new THREE.CatmullRomCurve3(p,true,'centripetal');curve.arcLengthDivisions=6000;
    assert.ok(curve.getPointAt(0).distanceTo(curve.getPointAt(1))<1e-8);
    assert.ok(curve.getTangentAt(0).dot(curve.getTangentAt(1))>.999);
    assert.ok(Math.abs(curve.getLength()/length-1)<.002);
    const samples=curve.getSpacedPoints(200);
    for(let i=0;i<200;i++)for(let j=i+2;j<200;j++){
      if(i===0&&j===199)continue;const [a,b,c,d]=[samples[i],samples[i+1],samples[j],samples[j+1]];
      assert.ok(!(cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0),`${name} crosses itself`);
    }
  }
});
test('Analytics markup remains available alongside lazy 3D integration',()=>{
  for(const id of ['circuit','plot','settings','sectors','uncertainty','source','analysis-layer','simulation-layer'])assert.ok(html.includes(`id="${id}"`));
  assert.ok(html.includes("Plotly.react('plot'"));assert.ok(html.includes('simulation/boot.js'));assert.ok(html.includes('"three":"./vendor/three/three.module.js"'));
});
