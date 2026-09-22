import test from 'node:test';
import assert from 'node:assert/strict';
import {createCar} from '../reports/simulation/car.js';
import {createCircuit,disposeGroup} from '../reports/simulation/circuits.js';
import {layouts} from '../reports/simulation/circuit-definitions.mjs';
import {readFileSync} from 'node:fs';
const winners=JSON.parse(readFileSync(new URL('../reports/recommendations.json',import.meta.url)));
test('Procedural circuit meshes have finite vertices and valid indices',()=>{
  for(const name of Object.keys(layouts)){
    const c=createCircuit(name,winners[name].baseline.distance_m);let meshes=0;
    c.group.traverse(o=>{if(o.geometry){meshes++;const a=o.geometry.attributes.position;assert.ok([...a.array].every(Number.isFinite));if(o.geometry.index)assert.ok([...o.geometry.index.array].every(i=>i<a.count));}});
    assert.ok(meshes>20);disposeGroup(c.group);assert.equal(c.group.parent,null);
  }
});
test('Procedural car accepts actual setup and updates force geometry',()=>{
  const c=createCar(winners['Downforce Circuit'].setup,0x24cfba);
  c.update({speed:70,frontForce:6000,rearForce:8000,drag:2800},.016,1,true,true);
  c.group.updateMatrixWorld(true);
  c.group.traverse(o=>assert.ok(o.matrixWorld.elements.every(Number.isFinite)));
  disposeGroup(c.group);
});
