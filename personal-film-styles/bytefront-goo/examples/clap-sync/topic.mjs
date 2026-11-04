import {P,box,label,at,circle} from './rebuild/stage.mjs';
import {ink,shape,ss,seg} from './rebuild/toon.mjs';

function slate(c,shot,f){
  const contact=shot.events.contact;
  const approach=ss(seg(f,contact-13,contact));
  const rebound=(f>contact&&f<contact+8)?Math.sin(Math.PI*(f-contact)/8):0;
  at(c,631,476,1,()=>{
    box(c,0,0,665,275,P.ink,{radius:12});
    label(c,'SOUND  /  PICTURE',333,149,49,{kind:'slab',align:'center',fill:P.white});
    ink(c,[[54,192],[609,192]],4,{color:P.paper});
    at(c,0,0,1,()=>{
      box(c,0,-62,665,62,P.ink,{radius:5});
      for(let i=0;i<7;i++){
        const x=13+91*i;
        shape(c,[[x,-58],[x+45,-58],[x+18,-4],[x-6,-4]],{fill:P.white,line:0});
      }
    },-.285*(1-approach)-.013*rebound);
    circle(c,11,-5,13,P.mustard,{line:2});
    if(f>=contact&&f<contact+12){
      for(const [x,y] of [[37,-49],[61,-14],[48,23]])ink(c,[[675+x*.35,y*.35],[675+x,y]],5,{color:P.coralD});
    }
  });
}
function tracks(c,shot,f){
  const u=ss(seg(f,shot.events.match-18,shot.events.match));
  const x=1190+200*(1-u);
  box(c,346,289,1240,485,P.white,{radius:14});
  label(c,'PICTURE',396,423,36,{kind:'slab'});label(c,'SOUND',396,640,36,{kind:'slab'});
  for(let n=0;n<7;n++)box(c,677+n*103,338,92,118,n===5?P.mustard:P.blueL,{radius:4});
  ink(c,[[1190,307],[1190,717]],3,{color:P.coralD});
  const pts=[];for(let xx=677;xx<=1510;xx+=4){
    const d=xx-x;
    const y=619+(d>=0?67*Math.exp(-d/34)*Math.cos(d*.47):0)+3*Math.sin(xx*.1);
    pts.push([xx,y]);
  }
  ink(c,pts,4,{color:P.tealD});
  if(u===1) label(c,'SYNC',1400,534,35,{kind:'slab',fill:P.tealD});
}
export const topicScenes={slate,tracks};
