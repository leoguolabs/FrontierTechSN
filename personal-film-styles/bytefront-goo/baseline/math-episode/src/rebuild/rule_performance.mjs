import {C,cue,travel,decisive,settle} from './motion.mjs';
// Story-specific Boolean explanation. The print grammar is reusable, the clauses are not.
import {P,tr,box,circle,label,heading,check,closeHand,lines} from './stage.mjs';
import {ink,ss,seg,lerp} from './toon.mjs';
import {switchProp} from './scenes.mjs';
const CLAUSES=[[true,true,false],[false,true,true],[true,false,true]];
export const evaluate=(state)=>CLAUSES.map(row=>row.map((required,i)=>state[i]===required));
const literal=(i,v)=>tr(`${'ABC'[i]} ${v?'ON':'OFF'}`,`${'ABC'[i]}${v?'开':'关'}`);
const ruleName=i=>tr(`RULE ${i+1}`,`规则${i+1}`);
function tag(c,text,y=860,w=1160){box(c,960-w/2,y-37,w,72,P.white,{line:2.8,radius:10});label(c,text,960,y+12,35,{align:'center',max:w-40});}
function clause(c,row,{x=240,y=360,w=1440,h=145,focus=-1,truth=null,active=false}={}){
 box(c,x,y,w,h,active?P.mustardL:P.white,{line:active?4.5:3,radius:11});
 const centers=[x+w*.16,x+w*.5,x+w*.84];
 for(let i=0;i<3;i++){
  if(focus===i)box(c,centers[i]-w*.12,y+23,w*.24,h-46,P.mustardL,{line:0,radius:8});
  label(c,literal(i,CLAUSES[row][i]),centers[i],y+h*.63,Math.min(59,w*.045),{kind:'slab',align:'center',max:w*.27});
  if(i<2)label(c,tr('or','或'),(centers[i]+centers[i+1])/2,y+h*.63,Math.min(43,w*.035),{kind:'script',align:'center'});
  if(truth){const tx=centers[i]+w*.115,ty=y+h*.4;circle(c,tx,ty,Math.min(25,h*.18),truth[i]?P.mustardL:P.pink,{line:2});check(c,tx,ty+3,{yes:truth[i],s:.48});}
 }
}
function rowStack(c,{count=3,focus=-1,orFocus=false,andFocus=false,status=null}={}){
 for(let i=0;i<count;i++){
  const y=280+i*178;
  circle(c,180,y+68,42,P.ink,{line:0});label(c,String(i+1),180,y+84,42,{align:'center',fill:P.white});
  clause(c,i,{x:260,y,w:1160,h:136,active:i===focus,focus:-1});
  if(orFocus){for(const x of [642,1037]){ink(c,[[x-30,y+106],[x+30,y+106]],4,{color:P.coralD});}}
  if(status!==null)check(c,1512,y+72,{yes:status[i],s:1.05});
 }
 if(andFocus){ink(c,[[1460,294],[1492,294],[1492,760],[1460,760]],4,{taper:false});label(c,tr('AND','且'),1650,548,66,{kind:'slab',align:'center'});}
}
export function rulePerformance(c,t,f,o={}){
 const mode=o.mode;
 if(mode==='first'){
  heading(c,tr('The puzzle has rules','给开关加上规则'),tr('One rule · three conditions','一条规则 · 三个条件'),{size:65});
  label(c,tr('Example setting: all three ON','示例组合：三个开关全开'),960,270,34,{align:'center'});
  const focus=f<o.cues.b?0:f<o.cues.c?1:2;
  for(let i=0;i<3;i++){
   const x=410+i*550;
   switchProp(c,x,480,{s:1.05,on:true,labelText:'',screenInk:true});
   box(c,x-195,724,390,86,focus===i&&f<o.cues.judge?P.mustardL:P.white,{line:3});
   label(c,literal(i,CLAUSES[0][i]),x,781,53,{kind:'slab',align:'center'});
   if(f>=o.cues.judge)check(c,x+155,700,{yes:i<2,s:.75});
  }
  for(const x of [685,1235])label(c,tr('or','或'),x,780,43,{kind:'script',align:'center'});
  if(f>=o.cues.judge)tag(c,tr('Two true conditions. The rule passes.','两项成立，这条规则通过。'));
  return;
 }
 if(mode==='all'){
  const goal=o.phase==='goal';
  heading(c,tr('The same switches, more rules','同一组开关，更多规则'),goal?tr('Every rule must pass','每条规则都必须通过'):tr('OR inside · AND between','内部是“或” · 之间是“且”'),{size:64});
  if(goal){
   // A compact rulebook plus an unresolved decision, not a claim that this example is impossible.
   for(let i=2;i>=0;i--){const y=285+i*32;box(c,150+i*26,y,820,390,P.white,{line:3,radius:8});}
   label(c,tr('RULEBOOK','规则册'),590,371,58,{kind:'slab',align:'center'});
   for(let i=0;i<3;i++){circle(c,280,455+i*70,24,P.ink,{line:0});label(c,String(i+1),280,464+i*70,27,{align:'center',fill:P.white});
    label(c,tr('up to 3 conditions','最多三个条件'),570,468+i*70,38,{align:'center'});}
   label(c,'?',1450,440,145,{kind:'slab',align:'center'});
   if(f>=o.cues.working)lines(c,tr('One setting that passes them all?','是否存在一种组合，全部通过？'),1450,537,670,47,{kind:'slab',align:'center'});
   if(f>=o.cues.none)label(c,tr('…or establish that none works','……或确定不存在'),1450,730,34,{align:'center',max:700});
   if(f>=o.cues.name)tag(c,'3-SAT',868,370);
  }else{
   const focus=f<o.cues.third?1:f<o.cues.or?2:-1;
   rowStack(c,{focus,orFocus:f>=o.cues.or&&f<o.cues.and,andFocus:f>=o.cues.and});
   if(f>=o.cues.and)tag(c,tr('The same setting must satisfy all three','同一种组合，必须同时满足三条规则'));
  }
  return;
 }
 if(mode==='test_result'){
  heading(c,tr('Read the consequence','看清操作的结果'),tr('No condition holds in rule 1','第一条：没有一项成立'),{size:65});
  const state=[false,false,true],truth=evaluate(state);
  label(c,tr('A OFF · B OFF · C ON','A关 · B关 · C开'),960,293,46,{kind:'slab',align:'center'});
  clause(c,0,{x:180,y:365,w:1560,h:215,truth:truth[0]});
  for(let i=0;i<3;i++){const x=420+i*540;circle(c,x,698,65,i===0?P.pink:P.mustardL,{line:3});check(c,x,702,{yes:truth[i].some(Boolean),s:1.25});label(c,ruleName(i),x,812,38,{kind:'slab',align:'center'});}
  tag(c,tr('One failed rule rejects this setting','只要一条失败，这种组合就不合格'),875);
  return;
 }
 if(mode==='test'){
  const u=t-(o.operation_shift||0),state=[u<2.9,u<4,true],truth=evaluate(state);
  heading(c,tr('Try this setting','实际试一试'),tr('Change the switches. Check the rules.','拨动开关，再检查规则'),{size:61});
  const xs=[285,665,1045],y=510,s=1.16;
  for(let i=0;i<3;i++){switchProp(c,xs[i],y,{s,on:state[i],position:i===0?1-cue(u,C.rule.a):i===1?1-cue(u,C.rule.b):1,labelText:'',stateLabelY:190,screenInk:true});label(c,'ABC'[i],xs[i]-145,y+220,43,{kind:'slab',align:'center'});}
  for(let i=0;i<3;i++){const yy=300+i*170,pass=truth[i].some(Boolean);box(c,1310,yy,460,142,pass?P.white:P.pink,{line:3});label(c,ruleName(i),1445,yy+63,38,{kind:'slab',align:'center'});check(c,1655,yy+67,{yes:pass,s:1.1});for(let j=0;j<3;j++){circle(c,1430+j*100,yy+112,15,truth[i][j]?P.mustardL:P.pink,{line:2});check(c,1430+j*100,yy+114,{yes:truth[i][j],s:.29});}}
  tag(c,tr('A ON  or  B ON  or  C OFF','A开  或  B开  或  C关'),862,1160);
  // Same contact/result moments as the retained switch Foley; larger geometry recomputes contact.
  if(u>C.rule.approach[0]&&u<C.rule.withdraw[1]){
   let x,yh;
   if(u<2.9){x=lerp(-240,xs[0],cue(u,C.rule.approach));yh=y-53*s+106*s*cue(u,C.rule.a);}
   else if(u<3.6){x=lerp(xs[0],xs[1],cue(u,C.rule.route));yh=y+53*s-25*Math.sin(Math.PI*seg(u,...C.rule.route))-106*s*cue(u,C.rule.route);}
   else {x=xs[1]-1500*cue(u,C.rule.withdraw);yh=y-53*s+106*s*cue(u,C.rule.b)-50*cue(u,C.rule.withdraw);}
   closeHand(c,[x,yh],{from:[-400,510],bend:55});
  }
 }
}
