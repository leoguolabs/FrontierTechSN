import {fileURLToPath} from 'node:url';
// Production-local V20 articulated Goo. Frozen raster identity, shared cloth sample,
// a true neck/collar overlap, head-anchored hand contacts, scene-local acting beats.
import {loadImage,createCanvas} from '@napi-rs/canvas';
import {PAL as P,lerp,ss,seg} from './toon.mjs';
import {gooHand,handMarker,handWorldMarker,GOO_NEAR_HAND,GOO_FAR_HAND} from './goo-hand.mjs';
const atlas=await loadImage(fileURLToPath(new URL('../../assets/goo-v04/rig-atlas.png',import.meta.url)));
const heads=await loadImage(fileURLToPath(new URL('../../assets/goo-v04/expressions-v19.png',import.meta.url)));
export const GOO={hoodie:'#EEB83B',cuff:'#EEB83B',ink:'#38251B'};
const cloth=createCanvas(128,128);cloth.getContext('2d').drawImage(atlas,260,340,128,128,0,0,128,128);
const headCells={calm:[62,38,437,447],think:[554,38,437,447],skeptic:[1055,38,437,447],happy:[62,537,437,447],surprise:[554,537,437,447],blink:[1055,537,437,447]};
const patterns=new WeakMap();function fabric(c){if(!patterns.has(c))patterns.set(c,c.createPattern(cloth,'repeat'));return patterns.get(c);}
let scene={scene:'',start:0,end:240,options:{}},observer=null;
export function setGooObserver(fn){observer=fn;}
export function setGooShot(shot){scene=shot;}
const mix=(a,b,u)=>[lerp(a[0],b[0],u),lerp(a[1],b[1],u)];
function joints(a,b,lengths=[102,102],side=1){const [l1,l2]=lengths,dx=b[0]-a[0],dy=b[1]-a[1],d=Math.hypot(dx,dy);if(d>l1+l2+.1||d<Math.abs(l1-l2)+.001)throw Error('Goo target unreachable '+d);const angle=Math.atan2(dy,dx)+side*Math.acos(Math.max(-1,Math.min(1,(l1*l1+d*d-l2*l2)/(2*l1*d))));return [a[0]+l1*Math.cos(angle),a[1]+l1*Math.sin(angle)];}
export function gooPointTip(wrist){const e=joints([102,-342],wrist),a=Math.atan2(wrist[1]-e[1],wrist[0]-e[0]);return handWorldMarker(wrist,a,'press','tip',GOO_NEAR_HAND,1.14);}
export function clothStroke(c,points,width){
 c.save();c.lineCap='round';c.lineJoin='round';c.beginPath();c.moveTo(...points[0]);for(const p of points.slice(1))c.lineTo(...p);c.strokeStyle=GOO.ink;c.lineWidth=width+6;c.stroke();c.strokeStyle=fabric(c);c.lineWidth=width;c.stroke();c.restore();
}
export function sleeve(c,a,b,{hand='open',side=1,lengths=[102,102],width=62,angle=null,handScale=1.14,front=false,elbow=null,handSide=1}={}){
 const e=elbow||joints(a,b,lengths,side),aa=Math.atan2(b[1]-e[1],b[0]-e[0]);
 const end=[b[0]-Math.cos(aa)*50,b[1]-Math.sin(aa)*50],before=mix(a,e,.79),after=mix(e,end,.30);
 c.save(); // Foreground sleeves cover the torso continuously, including both shoulders.
 c.lineCap='round';c.lineJoin='round';c.beginPath();c.moveTo(...a);c.lineTo(...before);c.quadraticCurveTo(...e,...after);c.lineTo(...end);
 c.strokeStyle=GOO.ink;c.lineWidth=width+6;c.stroke();c.strokeStyle=fabric(c);c.lineWidth=width;c.stroke();
 c.strokeStyle='#9C671B';c.lineWidth=1.8;c.beginPath();c.moveTo(e[0]+Math.sin(aa)*8,e[1]-Math.cos(aa)*8);c.quadraticCurveTo(e[0]+Math.sin(aa)*12+6,e[1]-Math.cos(aa)*12,e[0]+Math.sin(aa)*16+9,e[1]-Math.cos(aa)*16+3);c.stroke();c.restore();
 // The hand artwork includes the sleeve/cuff/wrist. Rotate it with the forearm.
 gooHand(c,...b,angle??aa,hand,handSide,handScale);return e;
}
function solveContact(shoulder,contact,kind,branch=1,lengths=[102,102],flex=0,handSide=GOO_NEAR_HAND){
 const [mx,my]=handMarker(kind,'tip',handSide),k=1.14,ex=lengths[1]+k*(mx*Math.cos(flex)-my*Math.sin(flex)),ey=k*(mx*Math.sin(flex)+my*Math.cos(flex));
 const e=joints(shoulder,contact,[lengths[0],Math.hypot(ex,ey)],branch),a=Math.atan2(contact[1]-e[1],contact[0]-e[0])-Math.atan2(ey,ex);
 return {elbow:e,wrist:[e[0]+lengths[1]*Math.cos(a),e[1]+lengths[1]*Math.sin(a)],angle:a+flex};
}
// Writing is a relaxed reach, not a two-bone IK fold toward the stomach.
// Solve the wrist on the shoulder-to-grip axis, then bow the elbow outward
// by only six local pixels. The palm and cuff turn with the same forearm.
function writingReach(point){
 const a=[102,-342],m=handMarker('writeGrip','tip',GOO_NEAR_HAND).map(v=>v*1.14);
 const dx=point[0]-a[0],dy=point[1]-a[1],d=Math.hypot(dx,dy);
 let angle=Math.atan2(dy,dx)-Math.asin(m[1]/d),wrist;
 for(let i=0;i<12;i++){
  wrist=[point[0]-m[0]*Math.cos(angle)+m[1]*Math.sin(angle),point[1]-m[0]*Math.sin(angle)-m[1]*Math.cos(angle)];
  const elbow=mix(a,wrist,.52);elbow[0]+=6;
  angle=Math.atan2(wrist[1]-elbow[1],wrist[0]-elbow[0]);
 }
 wrist=[point[0]-m[0]*Math.cos(angle)+m[1]*Math.sin(angle),point[1]-m[0]*Math.sin(angle)-m[1]*Math.cos(angle)];
 const elbow=mix(a,wrist,.52);elbow[0]+=6;
 return {wrist,elbow,angle};
}
function body(c){c.drawImage(atlas,125,184,620,816,-155,-408,310,408);}
function headPoint(p,angle){const y=p[1]+365;return [p[0]*Math.cos(angle)-y*Math.sin(angle),-365+p[0]*Math.sin(angle)+y*Math.cos(angle)];}
function wristForContact(point,angle,tip=[37,0]){return [point[0]-1.14*(tip[0]*Math.cos(angle)-tip[1]*Math.sin(angle)),point[1]-1.14*(tip[0]*Math.sin(angle)+tip[1]*Math.cos(angle))];}
const ease=(t,a,b)=>ss(seg(t,a,b));
function poseState({target=[170,-330],hand='open',face='calm',frame=0,acting,contact}={}){
 const t=(frame-scene.start)/24,o=scene.options||{},sc=scene.scene;
 let mode=acting||'present',amount=1,expression=face,tilt=0,left=[-156,-166],leftHand='relaxed',leftAngle=null,right=target,rightHand=hand,rightAngle=null,rightSide=1,leftSide=1,rightElbow=null,leftElbow=null;
 if(!acting){
  if(sc==='study'||sc==='identity'){mode='prop';}
  else if(sc==='reaction'){mode=t<3.7?'chin':t<5.4?'scratch':'chin';amount=t<3.7?ease(t,.35,.85):t<5.4?ease(t,3.7,4.15):ease(t,5.4,5.85);}
  else if(sc==='openingQuestion'){const at=(o.second_question-scene.start)/24;mode=t>at?'chin':'present';amount=t>at?ease(t,at,at+.45):1;}
  else if(sc==='direction'){mode=t<2.5?'chin':t<4.3?'glasses':'aha';amount=mode==='chin'?ease(t,.2,.65):mode==='glasses'?ease(t,2.5,2.9):ease(t,4.3,4.75);}
  else if(sc==='access'&&o.access_part==='policy'){const q=(o.tools_frame-scene.start)/24;mode=t<q?'chin':'present';amount=t<q?ease(t,.2,.65):1;}
  else if(sc==='access'&&o.access_part!=='policy'){mode=t<2.4?'glasses':t<5?'chin':'present';amount=ease(t,.15,.65);}
  else if(sc==='recap'&&o.mode==='end'){const q=(o.question_frame-scene.start)/24;mode=t<q?'chin':'aha';amount=ease(t,.1,.6);}
  else if(sc==='release'){mode=t<.55?'rest':t<1.6?'surprise':'present';amount=ease(t,.55,.95);}
  else if(face==='think'){mode=t<2.6?'chin':t<4.5?'glasses':'present';amount=ease(t,.2,.7);}
  else if(hand==='point'){mode='prop';}
 }
 // Short held gestures with a single accent, then a stable reading pose.
 if(mode==='chin'){
  expression=t<.3?'skeptic':'think';tilt=-.055*amount;rightSide=-1;
  const hit=solveContact([102,-342],headPoint([43,-383],tilt),'chin',-1);
  right=hit.wrist;rightElbow=hit.elbow;rightAngle=hit.angle;rightHand='chin';
  const support=solveContact([-100,-342],[rightElbow[0]-12,rightElbow[1]+25],'relaxed',1,[110,150],0,GOO_FAR_HAND);left=support.wrist;leftElbow=support.elbow;leftHand='relaxed';leftAngle=support.angle;
 }else if(mode==='scratch'){
  expression='skeptic';tilt=.035*amount;
  const tick=Math.sin(t*Math.PI*4)*1.6,hit=solveContact([102,-342],headPoint([65+tick,-557],tilt),'scratch',1);
  right=hit.wrist;rightElbow=hit.elbow;rightAngle=hit.angle;rightHand='scratch';
 }else if(mode==='glasses'){
  expression='think';tilt=-.025*amount;
  const hit=solveContact([102,-342],headPoint([65,-510],tilt),'press',1);
  right=hit.wrist;rightElbow=hit.elbow;rightAngle=hit.angle;rightHand='press';
 }else if(mode==='aha'){
  expression='happy';tilt=-.025;right=mix([160,-330],[170,-392],amount);rightAngle=-1.32;rightHand='point';left=[-152,-198];leftHand='relaxed';leftAngle=null;
 }else if(mode==='shrug'){
  expression='skeptic';tilt=.035;leftSide=-1;right=[183,-340];rightAngle=-.28;rightHand='open';left=[-174,-331];leftHand='open';leftAngle=-2.9;
 }else if(mode==='rest'){
  right=[158,-168];rightSide=-1;rightHand='relaxed';expression='calm';
 }else if(mode==='surprise'){
  right=mix([158,-168],[172,-322],amount);rightHand='open';rightAngle=-.7;expression='surprise';left=mix(left,[-166,-205],amount);leftHand='relaxed';
 }else if(mode==='present'){
  const enter=ease(t,.12,.55),accent=ease(t,1.6,1.85)*(1-ease(t,2.12,2.4));
  right=mix([154,-245],target,enter);right[1]-=10*accent;rightAngle=-.22-.15*accent;rightHand='open';
  expression=face==='think'?'think':t<1.15?'calm':'happy';tilt=-.018*accent;
  left=mix(left,[-155,-215],ease(t,3.2,3.65));
 }else if(mode==='prop'){
  expression=sc==='study'&&face!=='surprise'?'calm':face;tilt=sc==='study'?.09:0;if(sc==='study'||target[1]>-230)rightSide=-1;
  if(contact){const hit=contact.kind==='writeGrip'?writingReach(contact.point):solveContact([102,-342],contact.point,contact.kind||'grip',contact.branch??-1);right=hit.wrist;rightElbow=hit.elbow;rightAngle=hit.angle;rightHand=contact.kind||'grip';}
  if(sc==='identity'){expression=t>.7?(t>1.6?'happy':'surprise'):'think';left=mix(left,[-159,-198],ease(t,.8,1.3));leftHand='relaxed';}
 }
 // Blinks are brief held drawings on twos, never opaque overlays over pupils.
 if(['calm','happy'].includes(expression)&&frame%113>=86&&frame%113<90)expression='blink';
 return {mode,t,right,rightElbow,rightHand,rightAngle,rightSide,left,leftElbow,leftHand,leftAngle,leftSide,expression,tilt};
}
// Pose keys interpolate wrists, elbows and wrist rotations together. Elbow planes
// remain continuous during a gesture; no sudden IK branch flip at a mode change.
export function actingState(opts={}){
 const t=(opts.frame-scene.start)/24,o=scene.options||{},sc=scene.scene;
 const sample=(mode)=>{
  const v=poseState({...opts,acting:mode,target:mode==='prop'?opts.target:[170,-330]});
  v.rightElbow??=joints([102,-342],v.right,[102,102],v.rightSide);
  v.leftElbow??=joints([-100,-342],v.left,[105,105],v.leftSide);
  v.rightAngle=Math.atan2(v.right[1]-v.rightElbow[1],v.right[0]-v.rightElbow[0]);
  v.leftAngle=Math.atan2(v.left[1]-v.leftElbow[1],v.left[0]-v.leftElbow[0]);
  return v;
 };
 if(opts.acting)return sample(opts.acting);
 if(sc==='study'||sc==='identity'||opts.hand==='point')return sample('prop');
 let keys=[[0,'rest'],[.25,'present']];
 if(sc==='reaction')keys=[[0,'surprise'],[.4,'chin'],[3.7,'scratch'],[5.3,'chin'],[8.4,'shrug']];
 else if(sc==='openingQuestion')keys=[[0,'present'],[Math.max(.4,(o.second_question-scene.start)/24),'chin']];
 else if(sc==='direction')keys=[[0,'present'],[.3,'chin'],[2.7,'scratch'],[4.1,'glasses'],[5.5,'aha'],[8.5,'present']];
 else if(sc==='access'&&o.access_part==='policy')keys=[[0,'present'],[.3,'chin'],[Math.max(1,(o.tools_frame-scene.start)/24),'present']];
 else if(sc==='access')keys=[[0,'present'],[.5,'glasses'],[2.6,'chin'],[5.4,'shrug'],[7.3,'present'],[10,'aha']];
 else if(sc==='recap'&&o.mode==='end')keys=[[0,'present'],[.35,'chin'],[Math.max(1,(o.question_frame-scene.start)/24),'aha']];
 else if(sc==='release')keys=[[0,'rest'],[.6,'surprise'],[1.8,'present']];
 else if(opts.face==='think')keys=[[0,'present'],[.4,'chin'],[3.2,'glasses'],[5.4,'present']];
 else keys=[[0,'rest'],[.25,'present'],[7.1,'glasses'],[8.3,'present']];
 let ix=0;for(let i=0;i<keys.length;i++)if(t>=keys[i][0])ix=i;
 const current=sample(keys[ix][1]);if(ix===0)return current;
 const previous=sample(keys[ix-1][1]),onset=keys[ix][0],u=ease(t,onset+.06,onset+.62),ul=ease(t,onset+.12,onset+.84),uh=ease(t,onset-.10,onset+.30);
 if(u>=1&&ul>=1)return current;
 for(const key of ['right','rightElbow'])current[key]=mix(previous[key],current[key],u);
 for(const key of ['left','leftElbow'])current[key]=mix(previous[key],current[key],ul);
 // Travel outside the cheek when moving from chin to forehead or glasses.
 const faceTransition=['scratch','glasses'].includes(keys[ix][1])&&keys[ix-1][1]==='chin';
 if(faceTransition){const arc=Math.sin(Math.PI*u);current.right[0]+=62*arc;current.rightElbow[0]+=20*arc;}
 current.rightAngle=Math.atan2(current.right[1]-current.rightElbow[1],current.right[0]-current.rightElbow[0]);
 current.leftAngle=Math.atan2(current.left[1]-current.leftElbow[1],current.left[0]-current.leftElbow[0]);
 current.tilt=lerp(previous.tilt,current.tilt,uh);
 if(uh<.45)current.expression=previous.expression;
 if(u<.32)current.rightHand=previous.rightHand;else if(u<.72&&['chin','scratch','glasses'].includes(keys[ix][1]))current.rightHand='relaxed';
 if(ul<.7)current.leftHand=previous.leftHand;
 if(keys[ix][1]==='chin'||keys[ix-1][1]==='chin')current.frontLeft=true;
 return current;
}
export function goo(c,x,y,{s=1,dir=1,...opts}={}){
 const a=actingState(opts);if(observer)observer({shot:scene.id,x,y,s,dir,frame:opts.frame,...a});c.save();c.translate(x,y);c.scale(s,s);
 c.save();c.globalAlpha=.12;c.fillStyle=P.ink;c.beginPath();c.ellipse(0,0,158,12,0,0,Math.PI*2);c.fill();c.restore();
 // The back arm sits under the torso; the supporting forearm is drawn over it.
 c.save();c.scale(dir,1);sleeve(c,[-100,-342],a.left,{side:a.leftSide,lengths:[105,105],hand:a.leftHand,angle:a.leftAngle,width:63,elbow:a.leftElbow,handSide:GOO_FAR_HAND});sleeve(c,[102,-342],a.right,{side:a.rightSide,hand:a.rightHand,angle:a.rightAngle,width:64,elbow:a.rightElbow,handSide:GOO_NEAR_HAND});c.restore();
 body(c);
 c.save();c.scale(dir,1);
 // Broad short neck anchors the skull inside the hood opening at every tilt.
 c.fillStyle='#F9C594';c.strokeStyle=GOO.ink;c.lineWidth=3;c.beginPath();c.moveTo(-36,-409);c.lineTo(51,-408);c.lineTo(48,-350);c.quadraticCurveTo(8,-333,-38,-357);c.closePath();c.fill();c.stroke();
 c.save();c.translate(0,-365);c.rotate(a.tilt);c.drawImage(heads,...headCells[a.expression]||headCells.calm,-132,-250,282,288);c.restore();
 c.restore();
 // Only front collar and chest occlude neck; the back hood cannot bisect the head.
 c.save();c.beginPath();c.moveTo(-155,-340);c.lineTo(-98,-387);c.lineTo(0,-347);c.lineTo(101,-381);c.lineTo(155,-340);c.lineTo(155,0);c.lineTo(-155,0);c.closePath();c.clip();body(c);c.restore();
 c.save();c.scale(dir,1);
 if(a.mode==='chin'||a.frontLeft)sleeve(c,[-100,-342],a.left,{side:a.leftSide,lengths:[105,105],hand:a.leftHand,angle:a.leftAngle,width:63,front:true,elbow:a.leftElbow,handSide:GOO_FAR_HAND});
 sleeve(c,[102,-342],a.right,{side:a.rightSide,hand:a.rightHand,angle:a.rightAngle,width:64,front:true,elbow:a.rightElbow,handSide:GOO_NEAR_HAND});
 c.restore();c.restore();
}
