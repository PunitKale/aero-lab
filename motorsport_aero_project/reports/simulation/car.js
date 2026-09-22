import * as THREE from 'three';

// Original procedural single-seater. Local +Z is forward, +Y is up, dimensions in metres.
export function createCar(setup, color) {
  const group=new THREE.Group(),body=new THREE.Group();group.add(body);
  const paint=new THREE.MeshStandardMaterial({color,metalness:.35,roughness:.36});
  const carbon=new THREE.MeshStandardMaterial({color:0x111b25,roughness:.65});
  const tyre=new THREE.MeshStandardMaterial({color:0x090d12,roughness:.95});
  const silver=new THREE.MeshStandardMaterial({color:0xa8c3cf,metalness:.75,roughness:.3});
  function box(w,h,d,x,y,z,material=paint,parent=body){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material);m.position.set(x,y,z);m.castShadow=true;parent.add(m);return m;}
  box(1.25,.14,4,0,.15,-.1,carbon);box(.72,.45,2.9,0,.43,-.1);
  box(.35,.22,1.6,0,.36,1.7);box(.65,.35,1.1,0,.62,-1.4);
  for(const s of [-1,1]){box(.45,.37,1.65,s*.58,.34,-.5);box(.04,.27,.5,s*.96,.19,2.05,carbon);}
  box(.5,.14,.7,0,.72,-.1,carbon); // Cockpit opening.
  const helmet=new THREE.Mesh(new THREE.SphereGeometry(.19,12,8),new THREE.MeshStandardMaterial({color:0xf9d775}));helmet.position.set(0,.86,-.12);body.add(helmet);
  const halo=new THREE.Mesh(new THREE.TorusGeometry(.36,.025,5,18,Math.PI*1.7),carbon);halo.rotation.x=Math.PI/2;halo.position.set(0,.93,.03);body.add(halo);
  box(.035,.27,.035,0,.78,.36,carbon);
  const frontWing=box(1.9,.045,.48,0,.16,2.1);frontWing.rotation.x=THREE.MathUtils.degToRad(setup.front_wing_deg);
  const rearWing=box(1.65,.07,.6,0,.99,-2.02);rearWing.rotation.x=THREE.MathUtils.degToRad(setup.rear_wing_deg);
  for(const s of [-1,1]){box(.035,.5,.68,s*.83,.91,-2.02,carbon);box(.045,.8,.08,s*.35,.55,-2.05,carbon);}
  // Static setup rake is represented without exaggerating the millimetre differences.
  body.position.y=(setup.front_height_m+setup.rear_height_m)/2-.04;
  body.rotation.x=Math.atan2(setup.rear_height_m-setup.front_height_m,3.6);
  const wheels=[];
  for(const z of [1.5,-1.6])for(const s of [-1,1]) {
    const pivot=new THREE.Group();pivot.position.set(s*.99,.34,z);group.add(pivot);
    const wheel=new THREE.Mesh(new THREE.CylinderGeometry(.34,.34,.3,16),tyre);wheel.rotation.z=Math.PI/2;wheel.castShadow=true;pivot.add(wheel);
    const rim=new THREE.Mesh(new THREE.CylinderGeometry(.19,.19,.315,10),silver);rim.rotation.z=Math.PI/2;pivot.add(rim);
    const marker=new THREE.Mesh(new THREE.BoxGeometry(.32,.045,.29),silver);marker.position.y=.23;pivot.add(marker);
    wheels.push(pivot);
    box(.6,.035,.045,s*.62,.27,z+.12,carbon,group);box(.6,.035,.045,s*.62,.3,z-.12,carbon,group);
  }
  const arrows=new THREE.Group();group.add(arrows);
  const front=new THREE.ArrowHelper(new THREE.Vector3(0,-1,0),new THREE.Vector3(0,3,1.5),2,0x55dcb0,.4,.24);
  const rear=new THREE.ArrowHelper(new THREE.Vector3(0,-1,0),new THREE.Vector3(0,3,-1.5),2,0x55dcb0,.4,.24);
  const drag=new THREE.ArrowHelper(new THREE.Vector3(0,0,-1),new THREE.Vector3(0,1.5,-2.4),2,0xffb45a,.4,.24);arrows.add(front,rear,drag);
  const positions=new Float32Array(64*3),flow=new THREE.Points(new THREE.BufferGeometry(),new THREE.PointsMaterial({color:0xa1d6e2,size:.065,transparent:true,opacity:.5}));
  flow.geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));group.add(flow);
  let spin=0;const forceColor=new THREE.Color(),dragColor=new THREE.Color();
  function update(state,dt,elapsed,showForces,showFlow) {
    spin=(spin+state.speed*dt/.34)%(Math.PI*2);wheels.forEach(w=>w.rotation.x=spin);
    arrows.visible=showForces;
    // Shared linear force scale: 1 metre per 4 kN, with a 0.25 m visibility floor.
    for(const [arrow,value,z] of [[front,state.frontForce,1.5],[rear,state.rearForce,-1.5]]) {
      const len=.25+value/4000;arrow.position.set(0,.45+len,z);arrow.setLength(len,Math.min(.4,len*.3),.23);
      forceColor.setHSL(.46-value/100000,.75,.58);arrow.setColor(forceColor);
    }
    const len=.25+state.drag/4000;drag.setLength(len,Math.min(.4,len*.3),.23);dragColor.setHSL(.13-Math.min(state.drag/80000,.12),.95,.65);drag.setColor(dragColor);
    flow.visible=showFlow;
    if(showFlow){for(let i=0;i<64;i++){positions[i*3]=Math.sin(i*13.7)*1.8;positions[i*3+1]=.5+((i*17)%23)/12;positions[i*3+2]=5-((i*.37+elapsed*state.speed*.15)%11);}flow.geometry.attributes.position.needsUpdate=true;}
  }
  return {group,update};
}
