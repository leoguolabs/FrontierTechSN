// Production-specific recall: reuse the film's objects, not just four nouns.
import {P,tr,at,box,circle,label,heading,sheet,researcher,arrowTo} from './stage.mjs';
import {ink,ss,seg,lerp,arrow} from './toon.mjs';
const cue=(f,a,n=16)=>ss(seg(f,a,a+n));
const fade=(c,a,draw)=>{if(a<=0)return;c.save();c.globalAlpha*=a;draw();c.restore();};
function watch(c,x,y,s=1){at(c,x,y,s,()=>{circle(c,0,0,105,P.white);for(let i=0;i<12;i++){const a=i*Math.PI/6;ink(c,[[Math.sin(a)*88,-Math.cos(a)*88],[Math.sin(a)*98,-Math.cos(a)*98]],3);}ink(c,[[0,-66],[0,0],[58,30]],5);circle(c,0,0,6,P.coral,{line:0});});}
function computer(c,x,y,s=1){at(c,x,y,s,()=>{box(c,-195,-135,390,250,P.tealD,{line:4,radius:14});box(c,-169,-111,338,190,P.white,{line:3});label(c,'?',0,29,92,{kind:'slab',align:'center'});box(c,-238,116,476,30,P.chrome,{line:4});});}
function growth(c,x,y,u=1,s=1){at(c,x,y,s,()=>{arrow(c,[-165,100],[177,100],{bend:0,w:4,head:24,fill:P.coral});arrow(c,[-165,100],[-165,-125],{bend:0,w:4,head:24,fill:P.coral});const pts=[];for(let i=0;i<=32*u;i++){const k=i/32;pts.push([-150+305*k,88-190*k*k]);}if(pts.length>1)ink(c,pts,6,{color:P.coralD});});}
function manuscript(c,x,y,s=1,fan=1){at(c,x,y,s,()=>{for(let i=2;i>=0;i--)sheet(c,i*22*fan,-i*16*fan,{title:i?'':tr('MANUSCRIPT','手稿'),w:330,h:370,accent:P.coral});});}
function idea(c,x,y,s=1){at(c,x,y,s,()=>{sheet(c,0,0,{title:tr('METHOD','方法'),blank:true,w:330,h:370,accent:P.teal});label(c,'A → B',0,34,52,{kind:'slab',align:'center'});ink(c,[[-105,103],[105,103]],4,{color:P.coral});});}
function mini(c,i,x,y,s=1){at(c,x,y,s,()=>{if(i===0)manuscript(c,-16,10,.6,1);else if(i===1)growth(c,0,10,1,.68);else if(i===2)computer(c,0,0,.59);else idea(c,0,10,.62);});}
function overview(c,f,o){
 const names=[tr('Result','具体结论'),tr('Assumptions','成立条件'),tr('Checks','核查范围'),tr('Contribution','新增贡献')];
 heading(c,tr('Four questions to keep','留下这四个问题'),tr('Read beyond the headline.','再往标题里，多问一步。'),{size:72});
 for(let i=0;i<4;i++){
  const x=330+i*420,u=cue(f,o.reveal_frames[i],14);
  // The objects already exist as quiet silhouettes; the spoken item turns them into recall.
  circle(c,x,485,173,P.white,{line:3});
  fade(c,.15+.85*u,()=>mini(c,i,x,485));
  circle(c,x-128,345,42,u>.5?P.ink:P.white,{line:3});
  label(c,String(i+1),x-128,360,38,{kind:'slab',align:'center',fill:u>.5?P.white:P.ink});
  label(c,names[i],x,724,36,{kind:'slab',align:'center',max:400});
 }
 label(c,tr('Pause here. Keep the four questions.','可以暂停，留下这张四问卡。'),960,855,38,{align:'center'});
}
export function recall(c,t,f,o={}){
 const q=o.active||1;
 if(o.mode==='hold'){overview(c,f,o);return;}
 const titles=[tr('What exactly was solved?','具体解决了什么？'),tr('Under what assumptions?','在哪些条件下成立？'),tr('Who checked which part?','谁检查了哪一部分？'),tr('What does the work add?','增加了什么贡献？')];
 heading(c,tr(`QUESTION ${q} OF 4`,`四问 · 第 ${q} 问`),titles[q-1],{size:72});
 const a=cue(f,o.primary_frame,24),b=cue(f,o.secondary_frame,18);
 if(q===1){
  manuscript(c,lerp(940,505,b),550,1.1,a);
  fade(c,a,()=>label(c,tr('Manuscript count','手稿数量'),lerp(940,505,b),824,40,{kind:'slab',align:'center',max:670}));
  fade(c,b,()=>{
   sheet(c,1370,540,{title:tr('EXACT STATEMENT','准确命题'),blank:true,w:670,h:430,accent:P.teal});
   label(c,'ETH',1370,478,65,{kind:'slab',align:'center'});
   label(c,tr('Growth of computation','计算量的增长'),1370,609,40,{align:'center',max:610});
   label(c,tr('A mathematical result','一个数学结论'),1370,824,40,{kind:'slab',align:'center',max:740});
   fade(c,ss(seg(b,.9,1)),()=>label(c,'≠',940,565,83,{align:'center'}));
  });
  label(c,tr('Manuscript count and the later ETH claim','手稿数量，与后来公布的 ETH 主张'),960,892,26,{align:'center'});return;
 }
 if(q===2){
  sheet(c,lerp(960,540,b),540,{title:'ETH',blank:true,w:680,h:505,accent:P.coral});
  growth(c,lerp(960,540,b),550,a,1.06);
  fade(c,a,()=>label(c,tr('Worst-case growth','最坏情况的增长'),lerp(960,540,b),748,36,{align:'center',max:650}));
  fade(c,b,()=>{watch(c,1410,520,1.25);label(c,tr('This run','这次运行'),1410,748,39,{kind:'slab',align:'center'});fade(c,ss(seg(b,.9,1)),()=>label(c,'≠',960,550,84,{align:'center'}));});
  label(c,tr('Concept sketch · no measured values','概念示意，不代表实测数值'),960,870,28,{align:'center'});return;
 }
 if(q===3){
  computer(c,385,536,.85);
  sheet(c,1020,535,{title:tr('SUPPLIED STATEMENT','送入的命题'),blank:true,w:660,h:470,accent:P.teal});
  label(c,'x² ≥ 0',1020,560,86,{kind:'slab',align:'center'});
  fade(c,a,()=>{arrowTo(c,[600,540],[670,540],a);ink(c,[[860,599],[860+320*a,599]],6,{color:P.coral});});
  label(c,tr('What was checked?','核查了什么？'),1020,730,34,{align:'center'});
  fade(c,b,()=>{researcher(c,1635,817,{s:.84,dir:-1,target:[160,-325],hand:'open',frame:f});label(c,tr('Public review','公开检查'),1635,864,31,{align:'center'});});
  label(c,tr('Match the evidence to the statement.','让证据对上准确命题。'),880,862,37,{align:'center',max:1260});return;
 }
 // Method -> explanation -> adaptation are questions to investigate, not certified outcomes.
 const methodX=lerp(960,430,a),explain=cue(f,o.primary_frame+20,12);
 idea(c,methodX,540,1.04);
 label(c,tr('Key idea','关键想法'),methodX,823,42,{kind:'slab',align:'center'});
 fade(c,explain,()=>{arrowTo(c,[650,525],[790,525],explain);sheet(c,1030,540,{title:tr('EXPLAIN','解释'),blank:true,w:380,h:390,accent:P.blue});label(c,tr('WHY?','为什么？'),1030,588,68,{kind:'slab',align:'center'});label(c,tr('Understand it?','理解了吗？'),1030,823,39,{align:'center'});});
 fade(c,b,()=>{arrowTo(c,[1250,525],[1370,525],b);sheet(c,1590,540,{title:tr('ADAPT','继续使用'),blank:true,w:360,h:390,accent:P.coral});label(c,'A → ?',1590,588,54,{kind:'slab',align:'center'});label(c,tr('Build on it?','能继续使用吗？'),1590,823,36,{align:'center',max:490});});
}
