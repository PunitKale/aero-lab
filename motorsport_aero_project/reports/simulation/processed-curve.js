import * as THREE from 'three';

// Distance-indexed adapter over Python's processed coordinates. No second spline
// fit, scaling, or independent geometry: sample knots remain exactly shared.
export class ProcessedCurve {
  constructor(geometry){
    this.points=geometry.points;this.length=geometry.length_m;
    if(this.points.length<4||this.length<=0)throw new Error('Invalid processed circuit geometry');
  }
  locate(u){
    const d=((u%1)+1)%1*this.length;let lo=0,hi=this.points.length-1;
    while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(this.points[mid][0]<=d)lo=mid;else hi=mid-1;}
    const next=(lo+1)%this.points.length,a=this.points[lo],b=this.points[next];
    const end=next===0?this.length:b[0];return {a,b,f:(d-a[0])/(end-a[0])};
  }
  getPointAt(u,target=new THREE.Vector3()){
    const {a,b,f}=this.locate(u);
    // East -> +X; north -> -Z. Ground-plane handedness preserves the map shape.
    return target.set(a[1]+(b[1]-a[1])*f,0,-a[2]-(b[2]-a[2])*f);
  }
  getTangentAt(u,target=new THREE.Vector3()){
    const {a,b}=this.locate(u);return target.set(b[1]-a[1],0,a[2]-b[2]).normalize();
  }
  getSpacedPoints(divisions=500){return Array.from({length:divisions+1},(_,i)=>this.getPointAt(i/divisions));}
  getLength(){return this.length;}
}
