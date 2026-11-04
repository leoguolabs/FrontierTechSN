import {createCanvas,GlobalFonts} from '@napi-rs/canvas';
import fs from 'node:fs';
import path from 'node:path';
import {PAL as P,shape,ink,ellipse,spline,rect,rrect,plane,rays,sparkle,text,setClock,paperFinish,ss,seg,lerp,arrow,reg,move} from './toon.mjs';
import {drawHand} from './hand.mjs';
import {goo,GOO,clothStroke} from './goo.mjs';
import {gooHand,wristAtContact,GOO_NEAR_HAND} from './goo-hand.mjs';
export {P};
let language='en';
export const tr=(en,zh)=>language==='zh'?zh:en;
export function fonts(root){for(const f of JSON.parse(fs.readFileSync(path.join(root,'fonts/manifest.json'))))if(!GlobalFonts.registerFromPath(path.join(root,f.file),f.family))throw Error(f.file);}
export function begin(c,frame,lang,ground=P.paper,{burst=false,floor=true}={}){
 language=lang;setClock(frame/24);c.resetTransform();c.scale(c.canvas.width/1920,c.canvas.height/1080);
 c.fillStyle=ground;c.fillRect(0,0,1920,1080);
 if(burst)rays(c,1020,665,26,2400,P.white,{alpha:.19,rot:-.06});
 if(floor){plane(c,[[0,813],[1920,813],[1920,1080],[0,1080]],P.paper,{alpha:.19,grain:0});ink(c,[[80,813],[430,813],[805,814],[1840,813]],2.2,{breaks:.35,seed:404,alpha:.6});}
}
export function finish(c){paperFinish(c,c.canvas.width,c.canvas.height,1);}
export function at(c,x,y,s,fn,rot=0){c.save();c.translate(x,y);c.rotate(rot);c.scale(s,s);fn();c.restore();}
export function box(c,x,y,w,h,fill=P.white,opts={}){shape(c,rrect(x,y,w,h,opts.radius??6),{fill,line:opts.line??3.5,seed:opts.seed??14,grain:.25,...opts});}
export function circle(c,x,y,r,fill=P.white,opts={}){shape(c,ellipse(x,y,r,r,64),{fill,line:3.7,seed:37,grain:.23,...opts});}
export function label(c,s,x,y,size=42,{kind='sans',align='left',fill=P.ink,plate=null,max=1700}={}){
 const family=language==='en'&&/[≠≥∞✓→]/.test(s)?'Noto Sans SC':language==='zh'?(kind==='slab'||kind==='script'?'Math Serif SC Heavy':'Noto Sans SC'):(kind==='slab'?'Alfa Slab One':kind==='script'?'Oleo Script':'Jost');
 const font=`${language==='zh'&&kind!=='sans'?'800 ':''}${size}px "${family}"`;c.font=font;
 if(s.includes('ⁿ')){const base=s.replace('ⁿ',''),bw=c.measureText(base).width,nw=size*.37,xx=align==='center'?x-(bw+nw)/2:align==='right'?x-bw-nw:x;label(c,base,xx,y,size,{kind,fill,plate,max});label(c,'n',xx+bw,y-size*.57,size*.55,{kind,fill,max});return;}
 if(c.measureText(s).width>max)throw Error(`Overflow ${s}: ${c.measureText(s).width} > ${max}`);
 text(c,s,x,y,{font,align,fill,plate});
}
export function lines(c,s,x,y,width,size=42,opts={}){
 const units=language==='zh'?Array.from(s):s.split(' '),join=language==='zh'?'':' ';let line='',rows=[];
 const family=language==='zh'?(opts.kind==='slab'?'Math Serif SC Heavy':'Noto Sans SC'):(opts.kind==='slab'?'Alfa Slab One':'Jost');c.font=`${language==='zh'&&opts.kind==='slab'?'800 ':''}${size}px "${family}"`;
 for(const unit of units){const candidate=line?line+join+unit:unit;if(line&&c.measureText(candidate).width>width){rows.push(line);line=unit}else line=candidate;}if(line)rows.push(line);
 rows.forEach((row,i)=>label(c,row,x,y+i*size*1.24,size,{...opts,max:width}));return rows.length;
}
export function heading(c,kicker,title,{x=110,y=88,size=64,max=1660}={}){label(c,kicker,x,y,28,{kind:'script',max});lines(c,title,x,y+78,max,size,{kind:'slab',plate:P.white});}
export function caption(c,s){if(!s)return;
 const family=language==='zh'?'Noto Sans SC':'Jost',size=language==='zh'?39:42;c.font=`${size}px "${family}"`;let width=c.measureText(s).width;
 if(width>1640){const units=language==='zh'?Array.from(s):s.split(' '),join=language==='zh'?'':' ';let best=1,diff=1e9;for(let i=1;i<units.length;i++){const a=units.slice(0,i).join(join),b=units.slice(i).join(join),v=Math.max(c.measureText(a).width,c.measureText(b).width);if(v<diff){diff=v;best=i}}const a=units.slice(0,best).join(join),b=units.slice(best).join(join);width=diff;if(width>1640)throw Error('Caption exceeds two lines');box(c,960-width/2-42,912,width+84,122,P.white,{line:2.8,radius:12});label(c,a,960,959,size,{align:'center'});label(c,b,960,1008,size,{align:'center'});return;}
 const x=960-width/2-58;box(c,x,941,width+116,80,P.white,{line:2.8,radius:13});sparkle(c,x+28,981,14,{fill:P.coral});sparkle(c,x+width+88,981,14,{fill:P.coral});label(c,s,960,997,size,{align:'center'});
}
export function sheet(c,x,y,{s=1,title='',rows=[],blank=false,accent=P.teal,angle=0,w=340,h=400}={}){at(c,x,y,s,()=>{box(c,-w/2,-h/2,w,h,P.white,{radius:3,line:3.3});if(title)lines(c,title,0,-h/2+65,w-40,language==='zh'?35:33,{align:'center',kind:'slab'});ink(c,[[-w/2+30,-h/2+110],[w/2-30,-h/2+110]],4,{color:accent});rows.forEach((row,i)=>label(c,row,0,-h/2+170+i*60,32,{align:'center',max:w-45}));if(!rows.length&&!blank)for(let i=0;i<4;i++)ink(c,[[-w/2+35,-h/2+155+i*43],[w/2-40-(i%2)*25,-h/2+155+i*43]],2.2,{color:P.inkSoft,breaks:.1});},angle);}
export function desk(c,x=570,y=665,w=1050){shape(c,[[x+70,y+15],[x+104,y+20],[x+52,813],[x+18,813]],{fill:P.kraft,line:3.7});shape(c,[[x+w-105,y+17],[x+w-70,y+17],[x+w-22,813],[x+w-57,813]],{fill:P.kraft,line:3.7});shape(c,[[x,y],[x+w,y],[x+w+22,y+26],[x-15,y+26]],{fill:P.mustardL,line:4,seed:82});}
export function pencil(c,x,y,{angle=-.9,s=1}={}){at(c,x,y,s,()=>{shape(c,[[0,0],[15,-8],[132,-8],[132,8],[15,8]],{fill:P.mustard,line:2.8,seed:89,grain:.1});shape(c,[[0,0],[20,-8],[20,8]],{fill:P.kraftL,line:2.5});ink(c,[[0,0],[8,0]],3);box(c,132,-8,20,16,P.coral,{line:2});},angle);}

// New fictional researcher: geometric face, round glasses, teal cardigan.
// Coordinates are planted at the feet. The arm uses fixed 110/105 lengths.
export function armJoints(shoulder,target,side=1,lengths=[110,105]){
 const [l1,l2]=lengths,dx=target[0]-shoulder[0],dy=target[1]-shoulder[1],distance=Math.hypot(dx,dy);
 if(distance>l1+l2+.01||distance<Math.abs(l1-l2))throw Error(`Unreachable hand target ${distance}`);
 const a=Math.atan2(dy,dx),off=Math.acos(Math.max(-1,Math.min(1,(l1*l1+distance*distance-l2*l2)/(2*l1*distance))));
 return [shoulder,[shoulder[0]+l1*Math.cos(a+off*side),shoulder[1]+l1*Math.sin(a+off*side)],target];
}
function arm(c,shoulder,target,shirt,hand='open',side=1,lengths=[110,105]){
 const [,elbow]=armJoints(shoulder,target,side,lengths);
 // Round only the elbow; straight bones must not become an S-shaped rubber hose.
 const a=[lerp(elbow[0],shoulder[0],.13),lerp(elbow[1],shoulder[1],.13)],b=[lerp(elbow[0],target[0],.13),lerp(elbow[1],target[1],.13)];
 const points=[shoulder,a];for(let i=1;i<=6;i++){const u=i/6;points.push([(1-u)**2*a[0]+2*(1-u)*u*elbow[0]+u*u*b[0],(1-u)**2*a[1]+2*(1-u)*u*elbow[1]+u*u*b[1]]);}points.push(target);
 ink(c,points,25,{seed:61,taper:false,wob:.07});const o=reg(61,.6);ink(c,move(points,...o),17,{color:shirt,seed:62,taper:false,wob:.04});
 const angle=Math.atan2(target[1]-elbow[1],target[0]-elbow[0]);ink(c,[[target[0]-Math.sin(angle)*10,target[1]+Math.cos(angle)*10],[target[0]+Math.sin(angle)*10,target[1]-Math.cos(angle)*10]],2.7);drawHand(c,...target,angle,hand,-1,.75);
}
function legacyMentor(c,x,y,{s=1,dir=1,target=[170,-330],hand='open',face='calm',shirt=P.teal,frame=0,mentor=false}={}){at(c,x,y,s,()=>{c.scale(dir,1);
 c.save();c.globalAlpha=.14;shape(c,ellipse(0,0,94,10),{fill:P.ink,line:0,off:[0,0],grain:0});c.restore();
 shape(c,[[-43,-280],[-4,-280],[-13,-20],[-44,-20]],{fill:'#3B4766',line:3.8,seed:42});shape(c,[[5,-280],[44,-280],[45,-20],[14,-20]],{fill:'#3B4766',line:3.8,seed:43});
 shape(c,spline([[-47,-18],[-16,-20],[-2,-6],[-3,0],[-54,0]],true,4),{fill:P.hair,line:0,grain:0,off:[0,0]});shape(c,spline([[12,-18],[42,-19],[68,-6],[67,0],[10,0]],true,4),{fill:P.hair,line:0,grain:0,off:[0,0]});
 // Outward elbow branch, visible from shoulder to cuff. Hand rests beside thigh.
 const rest=ss(seg(target[1],-420,-320));
 arm(c,[-43,-376],[-78-4*rest,-210+3*rest],shirt,'relaxed',1,[91,87]);
 shape(c,spline([[-52,-374],[-31,-401],[31,-400],[53,-377],[43,-277],[-44,-277]],true,6),{fill:shirt,line:3.8,seed:50,shade:[{pts:[[27,-405],[70,-405],[70,-260],[23,-260]],color:P.tealD,alpha:.3}]});
 shape(c,[[-21,-402],[20,-402],[0,-357]],{fill:P.white,line:2.6,seed:51});ink(c,[[0,-357],[0,-282]],2.1);for(let j=0;j<3;j++)shape(c,ellipse(10,-338+j*22,2.4,2.4),{fill:P.ink,line:0,grain:0,off:[0,0]});
 shape(c,rrect(-19,-425,39,34,7),{fill:P.skin,line:3,seed:52});
 const head=spline([[-49,-499],[-40,-535],[-1,-551],[37,-533],[49,-503],[46,-481],[76,-466],[48,-453],[38,-429],[6,-418],[-29,-433],[-48,-464]],true,5);shape(c,head,{fill:P.skin,line:3.7,seed:67,breaks:.12});
 shape(c,spline([[-49,-478],[-63,-516],[-39,-548],[-15,-563],[12,-556],[42,-550],[50,-527],[30,-516],[-3,-523],[-20,-500],[-32,-487]],true,5),{fill:mentor?'#655C55':P.hair,line:0,seed:68});
 shape(c,ellipse(-39,-476,13,19),{fill:P.skin,line:2.8,seed:69});ink(c,[[-43,-481],[-35,-470]],2.4);
 const blink=frame%173<4;for(const ex of [4,36]){shape(c,ellipse(ex,-490,15,17,30),{fill:null,line:2.5,grain:0,seed:72});if(blink)ink(c,[[ex-5,-491],[ex+5,-491]],3);else shape(c,ellipse(ex+3,-489,3.3,5),{fill:P.ink,line:0,grain:0,off:[0,0]});}ink(c,[[19,-494],[22,-494]],2.3);ink(c,[[-3,-510],[14,-513]],3.1);ink(c,[[30,-514],[44,-510]],3.1);
 if(face==='surprise')shape(c,ellipse(25,-445,7,9),{fill:P.coralD,line:2.8,grain:0});else if(face==='think')ink(c,[[11,-443],[31,-445]],3.2);else ink(c,spline([[9,-445],[23,-440],[35,-449]],false,5),3.2);
 arm(c,[40,-379],target,shirt,hand,1);
 });}
export function closeHand(c,tip,{from=[2040,230],kind='press',shirt=GOO.hoodie,bend=95}={}){
 const angle=Math.PI/2,scale=2.4,wrist=wristAtContact(tip,angle,kind,GOO_NEAR_HAND,scale),end=[wrist[0],wrist[1]-112];
 const left=from[0]<960,elbow=[end[0]+(left?-110:110),end[1]-75*bend/95],line=spline([from,[end[0]+(left?-290:420),end[1]-bend],elbow,end],false,8);
 clothStroke(c,line,104);gooHand(c,...wrist,angle,kind,GOO_NEAR_HAND,scale);
}
export function check(c,x,y,{s=1,yes=true}={}){if(yes)ink(c,[[x-24*s,y],[x-5*s,y+22*s],[x+40*s,y-37*s]],7*s,{color:P.tealD});else{ink(c,[[x-22*s,y-22*s],[x+22*s,y+22*s]],7*s,{color:P.coralD});ink(c,[[x+22*s,y-22*s],[x-22*s,y+22*s]],7*s,{color:P.coralD});}}
export function arrowTo(c,a,b,u=1){arrow(c,a,b,{u,bend:.1,w:4,head:24,fill:P.coral});}

export function pencilHand(c,tip){
 // Forearm enters from below and travels with the hand. It cannot stretch from
 // a fixed left-screen anchor while the pencil approaches from the right.
 const angle=-.8,scale=2.4,grip=[tip[0]+Math.cos(-.9)*95,tip[1]+Math.sin(-.9)*95],wrist=wristAtContact(grip,angle,'writeGrip',GOO_NEAR_HAND,scale),end=[wrist[0]-Math.cos(angle)*100,wrist[1]-Math.sin(angle)*100];
 const curve=spline([[wrist[0]-240,1180],[wrist[0]-180,wrist[1]+230],[end[0]-60,end[1]+65],end],false,8);
 clothStroke(c,curve,104);pencil(c,...tip,{angle:-.9,s:1.4});gooHand(c,...wrist,angle,'writeGrip',GOO_NEAR_HAND,scale);
}

export function researcher(c,x,y,options={}){return options.mentor?legacyMentor(c,x,y,options):goo(c,x,y,options);}
