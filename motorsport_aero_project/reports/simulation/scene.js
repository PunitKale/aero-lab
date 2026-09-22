import * as THREE from 'three';
import {OrbitControls} from '../vendor/three/OrbitControls.js';

export function createScene(host) {
  const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;
  host.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','Interactive synthetic vehicle and circuit. Use the telemetry panel for numeric data.');
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x91a9b7);scene.fog=new THREE.Fog(0x91a9b7,450,2200);
  scene.add(new THREE.HemisphereLight(0xd9eeff,0x365642,2.3));
  const sun=new THREE.DirectionalLight(0xffebcb,3);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);
  Object.assign(sun.shadow.camera,{left:-35,right:35,top:35,bottom:-35,near:1,far:220});sun.shadow.bias=-.0003;
  scene.add(sun,sun.target);
  const camera=new THREE.PerspectiveCamera(48,1,.08,4000);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxDistance=1700;controls.minDistance=3;controls.maxPolarAngle=Math.PI*.48;
  const resize=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(w&&h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}});resize.observe(host);
  const forward=new THREE.Vector3(),desired=new THREE.Vector3(),target=new THREE.Vector3(),up=new THREE.Vector3(0,1,0),previousCar=new THREE.Vector3();
  let lastMode='';
  function updateCamera(mode,car,dt,snap=false) {
    forward.set(0,0,1).applyQuaternion(car.quaternion);target.copy(car.position);
    controls.enabled=mode==='orbit';
    if(mode==='orbit') {
      if(lastMode!==mode||snap){controls.target.copy(target);camera.position.copy(target).add(new THREE.Vector3(28,24,-28));}
      controls.update();
    }else {
      // Follow translation exactly; damp only changes in the chase offset. Otherwise
      // a fast replay leaves the camera tens of metres behind its intended distance.
      if(mode==='chase'&&lastMode===mode&&!snap)camera.position.add(car.position).sub(previousCar);
      if(mode==='cockpit'){desired.copy(target).addScaledVector(forward,.45).addScaledVector(up,1.08);target.addScaledVector(forward,35).addScaledVector(up,.95);}
      else if(mode==='tv') {
        // A stationary elevated camera per 120 m patch gives a broadcast-style pan.
        desired.set(Math.round(target.x/120)*120+55,42,Math.round(target.z/120)*120+60);target.y+=.7;
      } else {desired.copy(target).addScaledVector(forward,-11).addScaledVector(up,5);target.addScaledVector(forward,7);target.y+=.6;}
      const alpha=snap||lastMode!==mode||mode==='cockpit'?1:1-Math.exp(-dt*6);
      camera.position.lerp(desired,alpha);camera.lookAt(target);
    }
    previousCar.copy(car.position);lastMode=mode;sun.target.position.copy(car.position);sun.position.copy(car.position).add(new THREE.Vector3(-45,90,35));
  }
  return {scene,renderer,camera,controls,updateCamera,dispose(){resize.disconnect();controls.dispose();renderer.dispose();renderer.domElement.remove();}};
}
