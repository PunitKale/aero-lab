import * as THREE from 'three';
import {layouts} from './circuit-definitions.mjs';
import {ProcessedCurve} from './processed-curve.js';

export function createCircuit(name, length, geometry=null) {
  const group=new THREE.Group(), def=geometry?{character:'Real mapped geometry / model-generated performance'}:layouts[name];
  let points,curve;
  if(geometry){points=geometry.points.map(([,x,y])=>new THREE.Vector3(x,0,-y));curve=new ProcessedCurve(geometry);}
  else {
    points=def.points.map(([x,z])=>new THREE.Vector3(x,0,z));curve=new THREE.CatmullRomCurve3(points,true,'centripetal');
    const scale=length/curve.getLength();points.forEach(p=>p.multiplyScalar(scale));curve=new THREE.CatmullRomCurve3(points,true,'centripetal');
    curve.arcLengthDivisions=6000;curve.updateArcLengths();
  }
  const mat=(color)=>new THREE.MeshStandardMaterial({color,roughness:.95});
  const asphalt=mat(0x28343e), runoff=mat(0x56686a), white=mat(0xd8e4e8), red=mat(0xbe4953);
  // A ribbon samples a closed spline by arc length, with horizontal outward normals.
  function ribbon(inner,outer,y,material,start=0,end=1,steps=800) {
    const vertices=[],indices=[];
    for(let i=0;i<=steps;i++) {
      const u=start+(end-start)*i/steps,p=curve.getPointAt(u%1),t=curve.getTangentAt(u%1);
      const nx=-t.z,nz=t.x;
      vertices.push(p.x+nx*inner,y,p.z+nz*inner,p.x+nx*outer,y,p.z+nz*outer);
      if(i<steps){const j=i*2;indices.push(j,j+2,j+1,j+1,j+2,j+3);}
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setIndex(indices);g.computeVertexNormals();
    // DoubleSide makes the ribbon independent of clockwise/counterclockwise layout winding.
    material.side=THREE.DoubleSide;
    const mesh=new THREE.Mesh(g,material);mesh.receiveShadow=true;group.add(mesh);return mesh;
  }
  ribbon(-10,10,.01,runoff);ribbon(-6,6,.03,asphalt);
  ribbon(-6,-5.85,.04,white);ribbon(5.85,6,.04,white);
  const count=240;
  // One indexed mesh per kerb color: avoid hundreds of independent draw calls.
  for(const color of [0,1]) for(const side of [-1,1]) {
    const verts=[],ind=[];
    for(let i=color;i<count;i+=2) for(let j=0;j<3;j++){
      const u=(i+j/2)/count,p=curve.getPointAt(u%1),t=curve.getTangentAt(u%1),k=verts.length/3;
      verts.push(p.x-t.z*6*side,.06,p.z+t.x*6*side,p.x-t.z*7*side,.06,p.z+t.x*7*side);
      if(j<2)ind.push(k,k+2,k+1,k+1,k+2,k+3);
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));g.setIndex(ind);g.computeVertexNormals();
    const m=color?white:red;m.side=THREE.DoubleSide;group.add(new THREE.Mesh(g,m));
  }
  const start=curve.getPointAt(0),tangent=curve.getTangentAt(0),yaw=Math.atan2(tangent.x,tangent.z);
  for(let row=0;row<2;row++)for(let col=0;col<12;col++){
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(1,.03,1),mat((row+col)%2?0x18232c:0xffffff));
    mesh.position.set(start.x+Math.cos(yaw)*(col-5.5)+Math.sin(yaw)*row,.075,start.z-Math.sin(yaw)*(col-5.5)+Math.cos(yaw)*row);mesh.rotation.y=yaw;group.add(mesh);
  }
  const bounds=new THREE.Box3().setFromPoints(points),size=bounds.getSize(new THREE.Vector3());
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(size.x+1500,size.z+1500),mat(0x284d43));ground.rotation.x=-Math.PI/2;ground.position.y=-.04;ground.receiveShadow=true;group.add(ground);
  // Instancing keeps the repeated trackside environment cheap on integrated graphics.
  const barriers=new THREE.InstancedMesh(new THREE.BoxGeometry(1.2,1.5,7),mat(0x80929a),180);
  const trees=new THREE.InstancedMesh(new THREE.ConeGeometry(4,14,5),mat(0x1a3934),110);
  const dummy=new THREE.Object3D();
  for(let i=0;i<180;i++){
    const u=i/180,p=curve.getPointAt(u),t=curve.getTangentAt(u);dummy.position.set(p.x-t.z*13,.7,p.z+t.x*13);dummy.rotation.set(0,Math.atan2(t.x,t.z),0);dummy.updateMatrix();barriers.setMatrixAt(i,dummy.matrix);
  }
  // Reject trees near any part of the track, including a neighboring hairpin.
  const samples=curve.getSpacedPoints(700);let placed=0;
  for(let i=0;placed<110 && i<2000;i++) {
    const u=(i*.61803398875)%1,p=curve.getPointAt(u),t=curve.getTangentAt(u),offset=30+(i%7)*12;
    const x=p.x+t.z*offset,z=p.z-t.x*offset;
    if(samples.some(q=>(q.x-x)**2+(q.z-z)**2<22**2))continue;
    dummy.position.set(x,7,z);dummy.rotation.set(0,i,0);dummy.updateMatrix();trees.setMatrixAt(placed++,dummy.matrix);
  }trees.count=placed;group.add(barriers,trees);
  const pit=new THREE.Mesh(new THREE.BoxGeometry(13,6,48),mat(0x667d8a));pit.position.set(start.x-Math.cos(yaw)*30,3,start.z+Math.sin(yaw)*30);pit.rotation.y=yaw;pit.castShadow=true;group.add(pit);
  const roof=new THREE.Mesh(new THREE.BoxGeometry(17,1,53),mat(0x173950));roof.position.copy(pit.position);roof.position.y=6.5;roof.rotation.y=yaw;group.add(roof);
  return {group,curve,bounds,length,character:def.character,realGeometry:Boolean(geometry)};
}

export function disposeGroup(group) {
  const geometries=new Set(),materials=new Set();
  group.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));});
  geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());group.removeFromParent();
}
