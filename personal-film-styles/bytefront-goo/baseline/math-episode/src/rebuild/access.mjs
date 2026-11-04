// Production-specific access sequence; reveal actual resources at spoken cues.
import {P,tr,at,box,circle,label,heading,sheet,desk,researcher} from './stage.mjs';
import {ink,ss,seg,lerp,text} from './toon.mjs';
const cue=(f,a,n=16)=>ss(seg(f,a,a+n));
function reveal(c,u,draw){if(u<=0)return;c.save();c.globalAlpha*=u;draw();c.restore();}
function watch(c,x,y,s=1){at(c,x,y,s,()=>{circle(c,0,0,105,P.white);for(let i=0;i<12;i++){let a=i*Math.PI/6;ink(c,[[Math.sin(a)*85,-Math.cos(a)*85],[Math.sin(a)*95,-Math.cos(a)*95]],3);}ink(c,[[0,-68],[0,0],[60,30]],5);circle(c,0,0,7,P.coral,{line:0});});}
function computer(c,x,y,s=1,mark='…'){at(c,x,y,s,()=>{box(c,-195,-135,390,250,P.tealD,{line:4,radius:14});box(c,-169,-111,338,190,P.white,{line:3});label(c,mark,0,24,76,{kind:'slab',align:'center'});box(c,-238,116,476,30,P.chrome,{line:4});});}
function teaching(c,x,y,s=1){at(c,x,y,s,()=>{researcher(c,-66,100,{s:.32,target:[155,-320],frame:55,mentor:true});researcher(c,80,100,{s:.28,dir:-1,target:[70,-415],frame:55});});}
function manuscript(c,x,y,s=1,kind='paper'){at(c,x,y,s,()=>{sheet(c,0,0,{title:kind==='method'?tr('METHOD','方法'):tr('PAPER','论文'),blank:true,w:250,h:285,accent:P.coral});label(c,kind==='method'?'A → ?':'x² ≥ 0',0,38,43,{kind:'slab',align:'center'});ink(c,[[-78,72],[78,72]],3,{color:P.coral});});}
function notebook(c,x,y,s=1){at(c,x,y,s,()=>{box(c,-105,-137,210,274,P.blue,{line:3.5});ink(c,[[-84,-120],[-84,116]],3,{color:P.blueD});box(c,-64,-61,142,92,P.white,{line:2.5});label(c,tr('RULES','标准'),7,-4,29,{kind:'slab',align:'center'});});}
function overview(c,f,o){
 heading(c,tr('Published answers and usable resources','公开答案，与可用资源'),tr('What else does research need?','继续研究，还需要什么？'),{size:69});
 const m=cue(f,o.move_frame,18),x=lerp(960,375,m),s=lerp(1.28,.85,m);
 at(c,x,530,s,()=>{sheet(c,0,0,{title:tr('PUBLIC PAPER','公开论文'),accent:P.teal,w:420,h:420});});
 label(c,tr('Available to read','可以阅读'),x,lerp(865,820,m),39,{kind:'slab',align:'center'});
 const names=[tr('Time','时间'),tr('Training','训练'),tr('Compute','算力')];
 for(let i=0;i<3;i++){
  const u=cue(f,o.resource_frames[i],12),xx=910+i*370;
  if(u<=0)continue;
  at(c,xx,520,.82+.18*u,()=>{circle(c,0,0,146,[P.mustardL,P.blue,P.pink][i]);if(i===0)watch(c,0,0,.88);else if(i===1)teaching(c,0,0,1);else computer(c,0,0,.57);});
  reveal(c,u,()=>label(c,names[i],xx,765,39,{kind:'slab',align:'center',max:330}));
 }
 reveal(c,cue(f,o.summary_frame,12),()=>{
  label(c,'≠',660,555,78,{align:'center'});
  label(c,tr('Reading a paper does not supply these resources.','公开论文，不会自动提供这些资源。'),1080,866,34,{align:'center',max:1510});
 });
}
function policy(c,f,o){
 heading(c,tr('A call from the advisory group','顾问组提出的倡议'),tr('Who gets to keep asking?','谁能继续提出问题？'),{size:72});
 const u=cue(f,o.tools_frame,20);
 circle(c,1250,530,285,P.white,{line:3});desk(c,805,760,880);
 box(c,1075,375,370,385,P.teal,{line:4});
 label(c,tr('NEXT QUESTION','下一个问题'),1260,476,32,{kind:'slab',align:'center',max:345});label(c,'?',1260,610,112,{kind:'slab',align:'center'});
 if(u>0)computer(c,lerp(2180,1240,u),627.14,.91,'?');
 researcher(c,450,815,{s:.95,target:[lerp(70,170,u),lerp(-415,-330,u)],face:'think',frame:f});
 label(c,tr('Research autonomy','研究自主权'),450,870,37,{kind:'slab',align:'center',max:670});
 reveal(c,u,()=>label(c,tr('Access to tools and computation','获取工具与计算资源'),1250,870,37,{align:'center',max:960}));
}
function activities(c,f,o){
 heading(c,tr('From the announcement to the research desk','从公开承诺，到研究桌前'),tr('What support reaches the work?','研究者实际得到了什么？'),{size:67});
 const q=cue(f,o.question_frame,16),work=cue(f,o.work_frames[0],16);
 researcher(c,360,815,{s:.92,target:[lerp(70,165,q),lerp(-415,-330,q)],face:q>.5?'think':'calm',frame:f});
 const names=[tr('Evaluate results','评估成果'),tr('Learn tools','学习工具'),tr('Shared standards','共同标准')];
 // A small printed stage, with an actual paper, tool and notebook for each stated aim.
 if(q<1){c.save();c.beginPath();c.rect(620+1260*q,255,1260*(1-q),650);c.clip();
  for(let i=0;i<3;i++){
   const u=cue(f,o.aim_frames[i],12),x=820+i*420;
   if(u<=0)continue;
   at(c,x,495,.86+.14*u,()=>{circle(c,0,0,163,[P.mustardL,P.blue,P.pink][i]);if(i===0)manuscript(c,0,0,.81);else if(i===1)computer(c,0,0,.64);else notebook(c,0,0,.81);});
   reveal(c,u,()=>label(c,names[i],x,752,31,{kind:'slab',align:'center',max:390}));
  }
  label(c,tr('The initiative’s stated aims','倡议提出的支持方向'),1230,857,35,{align:'center'});c.restore();
 }
 if(q>0){c.save();c.beginPath();c.rect(620,255,1260*q,650);c.clip();
  if(work<1){reveal(c,1-work,()=>{
   desk(c,750,760,1040);computer(c,1100,638.82,.83,'?');
   sheet(c,1540,570,{title:tr('SUPPORT','实际支持'),blank:true,accent:P.coral,w:320,h:370});label(c,'?',1540,650,99,{kind:'slab',align:'center'});
   label(c,tr('Judge what is actually available.','要看实际能用上什么。'),1250,857,39,{align:'center',max:1060});
  });}
  // Retire the desk before a new row appears; never crossfade printed words.
  for(let i=0;i<3;i++){
   const u=cue(f,Math.max(o.work_frames[0]+16,o.work_frames[i]),12),x=820+i*420;
   if(u<=0)continue;
   at(c,x,495,.86+.14*u,()=>{circle(c,0,0,163,[P.mustardL,P.blue,P.pink][i]);if(i===0)manuscript(c,0,0,.81);else if(i===1)teaching(c,0,0,1.15);else manuscript(c,0,0,.81,'method');});
   reveal(c,u,()=>label(c,[tr('Explain','解释'),tr('Teach','教学'),tr('Reuse','复用')][i],x,752,43,{kind:'slab',align:'center'}));
  }
  reveal(c,cue(f,o.time_frame,12),()=>{watch(c,880,850,.31);label(c,tr('All of this takes time.','这些工作，都需要时间。'),1270,862,38,{align:'center',max:900});});
  c.restore();
 }
}
function latin(c,s,x,y,size,{slab=false,max=1700}={}){
 const font=`${size}px "${slab?'Alfa Slab One':'Jost'}"`;c.font=font;
 if(c.measureText(s).width>max)throw Error(`Funding label overflow: ${s}`);
 text(c,s,x,y,{font,align:'center',fill:P.ink});
}
function funding(c,f,o){
 heading(c,tr('Resources for continued research','支持继续研究的资源'),tr('An announced commitment','一项公开承诺'),{size:76});
 const m=cue(f,o.foundation_frame,18),a=cue(f,o.amount_frame,16),x=lerp(960,525,m);
 circle(c,x,535,255,P.white);
 latin(c,'15 OCT 2026',x,lerp(555,660,a),lerp(53,31,a),{slab:true,max:490});
 reveal(c,cue(f,o.amount_frame+12,10),()=>latin(c,'$15M',x,548,113,{slab:true}));
 reveal(c,cue(f,o.foundation_frame+7,12),()=>latin(c,'Simons Foundation',1350,410,47,{slab:true,max:850}));
 reveal(c,cue(f,o.partner_frames[0],12),()=>latin(c,'Anthropic',1135,523,41,{max:390}));
 reveal(c,cue(f,o.partner_frames[1],12),()=>latin(c,'+ OpenAI',1530,523,41,{max:390}));
 reveal(c,cue(f,o.qualifier_frame,12),()=>{
  label(c,tr('Combined funding','资金与资源'),1350,654,43,{kind:'slab',align:'center',max:840});
  label(c,tr('and resources','的合计承诺'),1350,715,43,{kind:'slab',align:'center',max:840});
 });
 reveal(c,cue(f,o.manager_frame,12),()=>label(c,tr('Funding managed by the Simons Foundation','资助由西蒙斯基金会管理'),960,865,37,{align:'center',max:1680}));
}
export function accessRestaged(c,t,f,o){if(o.mode==='supports')overview(c,f,o);else if(o.mode==='fund')funding(c,f,o);else if(o.access_part==='policy')policy(c,f,o);else activities(c,f,o);}
