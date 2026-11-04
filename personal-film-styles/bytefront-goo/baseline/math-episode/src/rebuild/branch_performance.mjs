// Authored for this mathematical explanation; not a generic style template.
import {P,tr,box,circle,label,heading} from './stage.mjs';
import {ink,ss,seg,lerp} from './toon.mjs';
import {switchProp} from './scenes.mjs';

const bits=(value,n)=>Array.from({length:n},(_,i)=>(value>>(n-1-i))&1);
function footer(c,text){box(c,430,831,1060,73,P.white,{line:2.8,radius:11});label(c,text,960,881,35,{align:'center',max:1000});}
export function branchTree(c,t,f,o={}){
 const ev=o.growth_events;
 const n=ev?(f>=ev.third?3:f>=ev.second?2:1):(o.n||1);
 const count=ev?(f>=ev.eight?8:f>=ev.four?4:2):(o.count||2**n);
 const g2=ev?ss(seg(f,ev.second,ev.second+18)):n>=2?1:0;
 const g3=ev?ss(seg(f,ev.third,ev.third+18)):n>=3?1:0;
 const summary=o.summary||f>=(o.summary_frame??Infinity);
 heading(c,tr('Two choices per switch','每个开关有两种选择'),summary?tr('Each new level doubles it','每多一层，组合翻倍'):tr('Follow the branches','沿着分支，看所有可能'),{size:65});
 const ys=[lerp(lerp(520,340,g2),300,g3),lerp(660,510,g3),740];
 const active=(o.focus_events||[]).reduce((v,e)=>f>=e.frame?e.prefix:v,[]);
 const x=(j,k)=>260+(j+.5)*1500/(2**k),r=54;
 const selected=path=>active.length>0&&path.slice(0,Math.min(path.length,active.length)).every((b,i)=>b===active[i]);
 for(let k=1;k<=n;k++){
  const grow=k===1?1:k===2?g2:g3,y=ys[k-1];
  if(k>1){
   for(let j=0;j<2**k;j++){
    const px=x(Math.floor(j/2),k-1),py=ys[k-2],cx=x(j,k),cy=y;
    const dx=cx-px,dy=cy-py,d=Math.hypot(dx,dy);
    const a=[px+dx/d*r,py+dy/d*r],b=[cx-dx/d*r,cy-dy/d*r];
    ink(c,[a,b],selected(bits(j,k))?5.8:3.4,{color:selected(bits(j,k))?P.coralD:P.inkSoft,upto:grow,taper:false,wob:.18});
   }
  }
  const reveal=k===1?1:ss(seg(grow,.6,1));
  if(reveal>0){
   c.save();c.globalAlpha*=reveal;
   label(c,String.fromCharCode(64+k),112,y+20,56,{kind:'slab',align:'center'});
   for(let j=0;j<2**k;j++){
    const cx=x(j,k),path=bits(j,k);if(selected(path))circle(c,cx,y,r+14,null,{line:4.5,lineColor:P.ink});
    circle(c,cx,y,r,j%2?P.coral:P.blue,{line:3.8});label(c,String(j%2),cx,y+17,48,{align:'center'});
   }
   c.restore();
  }
 }
 footer(c,summary?'2 × 2 × 2 = 8':count<2**n?tr('How many possible settings?','现在有多少种组合？'):tr(`${count} possible settings`,`${count}种组合`));
}
export function branchTable(c,t,f,o={}){
 heading(c,tr('Three switches · eight settings','三个开关 · 八种组合'),tr('One row, one setting','一排，就是一种组合'),{size:65});
 const start=o.change_start,end=o.change_end,u=ss(seg(f,start,end)),value=f>=end?1:0;
 label(c,tr('The selected setting','正在查看的组合'),560,270,39,{kind:'script',align:'center'});
 for(let i=0;i<3;i++)switchProp(c,250+i*310,505,{s:1.1,on:i===2&&f>=end,position:i===2?u:0,labelText:String.fromCharCode(65+i),screenInk:true});
 const bx=[1280,1445,1610];for(let i=0;i<3;i++)label(c,String.fromCharCode(65+i),bx[i],260,38,{kind:'slab',align:'center'});
 for(let j=0;j<8;j++){
  const y=292+j*68,selected=j===value;box(c,1160,y,570,56,selected?P.mustardL:P.white,{line:selected?3.8:2.5,radius:9});
  for(let i=0;i<3;i++){const b=bits(j,3)[i];circle(c,bx[i],y+27,21,b?P.coral:P.blue,{line:2.2});label(c,String(b),bx[i],y+39,34,{align:'center'});}
 }
 if(f>=(o.overview_frame??Infinity))ink(c,[[1758,296],[1782,296],[1782,820],[1758,820]],4,{taper:false});
 footer(c,tr('8 distinct settings · no repeated row','8种不同组合 · 每种只出现一次'));
}
