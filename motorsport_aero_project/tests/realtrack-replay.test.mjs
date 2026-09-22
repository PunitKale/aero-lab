import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {ProcessedCurve} from '../reports/simulation/processed-curve.js';
import {createRun,sampleRun} from '../reports/simulation/telemetry.mjs';
import {createCircuit,disposeGroup} from '../reports/simulation/circuits.js';
const data=JSON.parse(readFileSync(new URL('../data/processed/realtrack/replay.json',import.meta.url)));
test('Every processed XY knot and telemetry clock is preserved in the real-track replay',()=>{
 for(const [name,g] of Object.entries(data.geometry)){
  const curve=new ProcessedCurve(g);
  for(const [d,x,y] of g.points){const p=curve.getPointAt(d/g.length_m);assert.ok(Math.abs(p.x-x)<1e-7);assert.ok(Math.abs(p.z+y)<1e-7);}
  assert.ok(curve.getPointAt(0).distanceTo(curve.getPointAt(1))<1e-9);
  for(const role of ['baseline','candidate']){const t=data.traces[name][role],r=createRun(t,{});assert.ok(Math.abs(r.duration-data.recommendations[name][role].lap_time_s)<1e-8);for(let i=0;i<t.time_s.length;i++){const s=sampleRun(r,t.time_s[i]);assert.equal(s.distance,t.distance_m[i]);const p=curve.getPointAt(s.phase);assert.ok(Math.abs(p.x-t.x_m[i])<1e-7);}assert.equal(sampleRun(r,r.duration).laps,1);}
 }
});
test('Real-geometry track builds finite meshes without modifying source coordinates',()=>{
 for(const [name,g] of Object.entries(data.geometry)){
  const original=JSON.stringify(g.points);const track=createCircuit(name,g.length_m,g);assert.equal(track.realGeometry,true);
  track.group.traverse(o=>{if(o.geometry)assert.ok([...o.geometry.attributes.position.array].every(Number.isFinite));});assert.equal(JSON.stringify(g.points),original);disposeGroup(track.group);
 }
});
