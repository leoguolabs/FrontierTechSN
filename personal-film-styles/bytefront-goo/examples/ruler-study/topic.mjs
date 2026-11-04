import {P, box, label, researcher} from './rebuild/stage.mjs';
import {ink, shape, ss, seg} from './rebuild/toon.mjs';
import {handWorldMarker, GOO_NEAR_HAND} from './rebuild/goo-hand.mjs';
import {setGooObserver} from './rebuild/goo.mjs';

function ruler(c, shot, frame, language) {
  const clamp = 1400, end = 862, restY = 565, maxDrop = 77;
  const origin = [530, 856], scale = 1.03;
  const {contact, release} = shot.events;
  const approach = ss(seg(frame, contact-10, contact));
  const squeeze = ss(seg(frame, contact, release-3));
  const t = Math.max(0, frame-release) / 24;
  const lift = ss(seg(frame, release, release+4));
  const drop = frame < release ? maxDrop*squeeze : maxDrop*Math.exp(-1.55*t)*Math.cos(12.1*t);
  const yAt = x => restY + drop*Math.pow(Math.max(0, (clamp-x)/(clamp-end)), 2);
  const contactX = end-24*(1-approach)-9*lift;
  const contactY = restY + maxDrop*squeeze - 80*(1-approach)-135*lift;
  const actorPoint = [(contactX-origin[0])/scale, (contactY-origin[1])/scale];
  box(c,clamp,restY+20,360,55,P.kraftL,{radius:3});
  box(c,clamp+45,restY+75,44,233,P.kraft,{radius:3});
  box(c,clamp+276,restY+75,44,233,P.kraft,{radius:3});
  const curve = Array.from({length:55},(_,i)=>{const x=end+(1700-end)*i/54; return [x,yAt(x)];});
  shape(c,[...curve,...curve.toReversed().map(([x,y])=>[x,y+20])],{fill:P.tealL,line:3.3});
  for(let x=end+14,n=0;x<1690;x+=22,n++) ink(c,[[x,yAt(x)+2],[x,yAt(x)+(n%5===0?13:7)]],2,{color:P.tealDD});
  box(c,clamp+12,restY-48,262,46,P.coralD,{radius:4});
  box(c,clamp+12,restY-94,262,44,P.mustardL,{radius:4});
  label(c,language==='zh'?'固定端':'Fixed end',1510,restY-135,37,{align:'center'});
  if (frame >= release+2) {
    for(let x=end-32;x<clamp;x+=37) ink(c,[[x,restY],[x+20,restY]],2,{color:P.inkSoft});
    label(c,language==='zh'?'原来的位置':'Rest position',1120,restY+164,37,{align:'center'});
  }
  let actual;
  setGooObserver(p => {
    const local = handWorldMarker(p.right,p.rightAngle,p.rightHand,'tip',GOO_NEAR_HAND,1.14);
    actual = [origin[0]+scale*local[0],origin[1]+scale*local[1]];
  });
  researcher(c,...origin,{s:scale,frame,acting:'prop',face:frame<release?'think':'happy',
    contact:{kind:'press',branch:-1,point:actorPoint}});
  setGooObserver(null);
  if (Math.hypot(actual[0]-contactX,actual[1]-contactY) > .001) throw Error('Fingertip left authored path');
  if (frame>=contact && frame<=release && Math.hypot(actual[0]-end,actual[1]-yAt(end))>.001) throw Error('Ruler left fingertip');
}
export const topicScenes = {ruler};
