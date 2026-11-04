import {C,cue,travel,decisive,settle} from './motion.mjs';
// Math-in-AI production scenes: these claims and compositions stay outside the style library.
import {P,tr,at,box,circle,label,lines,heading,sheet,desk,pencil,researcher,closeHand,pencilHand,check,arrowTo} from './stage.mjs';
import {shape,ink,ellipse,spline,plane,rays,sparkle,ss,seg,lerp,arrow} from './toon.mjs';
import {drawHand} from './hand.mjs';
import {recall} from './recap.mjs';
import {closing} from './closing.mjs';
import {accessRestaged} from './access.mjs';
const move=(t,a,b)=>travel(t,a,a+(b-a)*.62);
function badge(c,s,x,y,{w=650,size=35,fill=P.white}={}){box(c,x-w/2,y-40,w,80,fill,{radius:12,line:3});label(c,s,x,y+14,size,{align:'center',max:w-36});}
function clock(c,x,y,s=1,hand=0){at(c,x,y,s,()=>{circle(c,0,0,119,P.white);for(let i=0;i<12;i++){const a=i*Math.PI/6;ink(c,[[Math.sin(a)*97,-Math.cos(a)*97],[Math.sin(a)*106,-Math.cos(a)*106]],3);}ink(c,[[0,0],[55,-55]],5);ink(c,[[0,0],[70*Math.sin(hand),-70*Math.cos(hand)]],4,{color:P.coral});circle(c,0,0,7,P.ink,{line:0});});}
function laptop(c,x,y,{s=1,screen='?',active=false}={}){at(c,x,y,s,()=>{box(c,-220,-165,440,290,P.tealD,{radius:18,line:4});box(c,-192,-139,384,228,P.white,{radius:8,line:3});label(c,screen,0,-10,70,{kind:'slab',align:'center',max:350});shape(c,[[-220,125],[220,125],[290,181],[-285,181]],{fill:P.chrome,line:4,seed:301});for(let i=0;i<3;i++)ink(c,[[-160-i*10,141+i*10],[170+i*10,141+i*10]],2.2,{color:P.inkSoft});circle(c,0,110,5,active?P.mustard:P.pink,{line:0});});}
function tile(c,x,y,s,{w=240,fill=P.white,size=66}={}){box(c,x-w/2,y-70,w,140,fill,{radius:12,line:3.6});label(c,s,x,y+23,size,{kind:'slab',align:'center',max:w-24});}
function handMark(c,t,{x=900,y=560,until=2.5,length=120,color=P.coral}={}){const u=move(t,.8,until),retract=move(t,until+.35,until+1.35);if(u>0)ink(c,[[x,y],[x+length*u,y]],6,{color});if(t>.2&&t<until+1.35){const tip=[x+length*u+300*retract,y-700*retract];closeHand(c,[tip[0]-16,tip[1]-55],{kind:'grip'});pencil(c,...tip,{s:1.1,angle:-.95});}}
export function growth(c,t,f,o={}){
 const mode=o.mode||'rates';
 if(mode==='dates'){heading(c,tr('Read the dates carefully','分清发现日与公开日'),tr('Discovery and announcement','核心发现，与公开宣布'),{size:67});for(let i=0;i<2;i++){const x=550+i*840;sheet(c,x,525,{title:i?'Anthropic':'OpenAI',rows:['16 OCT',tr('reported discovery','声称核心发现')],accent:i?P.blue:P.coral,w:530,h:400});label(c,i?'27 OCT 2026':'26 OCT 2026',x,812,45,{kind:'slab',align:'center'});}if(t>2.5){arrowTo(c,[550,710],[550,755],move(t,2.5,3));arrowTo(c,[1390,710],[1390,755],move(t,2.5,3));}return;}
 if(mode==='laptop'){label(c,tr('And my laptop?','那我的电脑呢？'),120,180,88,{kind:'script',plate:P.white});laptop(c,650,550,{s:1.25,screen:'…'});clock(c,1390,500,1.5,.45);badge(c,tr('Practical speed needs measurements','实际速度，需要实测'),1375,807,{w:820,size:36});if(t>2.3){check(c,1430,719,{yes:false,s:.7});}return;}
 if(mode==='overheads'){
  heading(c,tr('A different question','换一个问题'),tr('What must the machine do?','机器究竟要做多少工作？'),{size:67});
  const u=ss(seg(f,o.overhead_frame,o.overhead_frame+12)),v=ss(seg(f,o.scale_frame,o.scale_frame+38));
  // An uncalibrated, labelled mechanism sketch. No measured benchmark or speedup.
  // The input is a complete first state, not half of an empty equation.
  // Make room for the extra term only when narration introduces it.
  box(c,lerp(610,210,u),340,lerp(700,1500,u),330,P.white,{line:4});
  if(u>0)at(c,lerp(650,535,u),505,Math.max(.001,u),()=>{box(c,-285,-130,570,260,P.coral,{line:3});label(c,tr('Overhead','额外开销'),0,0,58,{kind:'slab',align:'center',max:540});label(c,tr('can be large','可能很大'),0,70,39,{align:'center'});});
  if(u>.8){c.save();c.globalAlpha=ss((u-.8)/.2);label(c,'+',930,535,95,{kind:'slab',align:'center'});c.restore();}
  const inputShift=lerp(-380,0,u);
  label(c,tr('Work on the input','处理输入'),1340+inputShift,424,45,{kind:'slab',align:'center',max:630});
  for(let i=0;i<7;i++){const shown=i<2+Math.floor(v*5);box(c,1060+inputShift+i*77,470,60,125,shown?P.teal:P.white,{line:2.7});}
  label(c,tr('Problem size','问题规模'),330,766,38,{kind:'slab',align:'center'});
  arrow(c,[540,750],[1660,750],{u:v,bend:0,w:4,head:24,fill:P.coral});circle(c,lerp(540,1590,v),750,17,P.tealD,{line:2});
  if(v>.95)label(c,tr('Advantage may appear only at huge sizes','优势可能要到极大规模才出现'),1120,836,36,{align:'center',max:1260});
  label(c,tr('Concept sketch · not measured values','概念示意，不代表实测数值'),960,891,27,{align:'center'});return;
 }
 if(mode==='evidence'){
  heading(c,tr('What the result does not establish','结果尚未说明什么'),tr('Two questions. Different evidence.','两个问题，需要不同证据'),{size:66});
  const compare=f>=o.comparison_frame;
  // Start with the missing practical result. Bring the growth claim alongside it
  // at the explicit comparison in the narration, as in the reference's paired outcomes.
  const shift=ss(seg(f,o.comparison_frame,o.comparison_frame+14)),rx=lerp(960,1430,shift);
  sheet(c,rx,540,{title:tr('PRACTICAL RUNTIME','实际运行时间'),blank:true,accent:P.teal,w:680,h:520});
  clock(c,rx,510,.76,.45);label(c,'?',rx+160,560,98,{kind:'slab',align:'center'});
  label(c,tr('No performance conclusion','尚无实际速度结论'),rx,704,35,{align:'center',max:630});
  if(compare){const u=ss(seg(f,o.comparison_frame,o.comparison_frame+14));at(c,490,540,Math.max(.001,u),()=>{
   sheet(c,0,0,{title:tr('THEORETICAL GROWTH','理论增长规律'),blank:true,accent:P.coral,w:680,h:520});
   arrowTo(c,[-230,70],[230,70],1);arrowTo(c,[-230,70],[-230,-90],1);
   ink(c,[[-210,55],[-120,48],[-25,24],[65,-10],[150,-57],[215,-115]],5,{color:P.coralD});
   label(c,tr('Study the time bound','检查时间界'),0,164,35,{align:'center',max:625});
  });}
  if(shift>=1)badge(c,tr('A growth result is not a stopwatch reading','增长规律的结果，不等于秒表读数'),960,863,{w:1490,size:36});return;
 }
 if(mode==='eventually'){heading(c,tr('The word that does the work','关键在这个词'),tr('Eventually','最终'),{size:96});ink(c,[[225,660],[1700,660]],5);arrowTo(c,[1600,660],[1730,660],1);for(let i=0;i<5;i++){const x=320+i*290;ink(c,[[x,645],[x,675]],3);label(c,String(10**i),x,732,38,{align:'center'});}const p=move(t,.6,4.5);circle(c,lerp(320,1590,p),660,24,P.coral);label(c,tr('Increasing problem size','不断增大的问题规模'),960,848,39,{align:'center'});badge(c,tr('A limit statement ≠ a stopwatch reading','极限增长规律 ≠ 秒表读数'),960,390,{w:1360});return;}
 if(mode==='subexp'){heading(c,tr('The claim concerns growth','主张讨论增长规律'),tr('Every fixed multiplier greater than one','每一种大于一的固定倍率'),{size:64});
 const rates=['2','1.1','1.01'];for(let i=0;i<3;i++){circle(c,425+i*540,450,157,[P.mustardL,P.white,P.blue][i]);label(c,rates[i],425+i*540,482,76,{kind:'slab',align:'center'});}
 label(c,tr('… and every other fixed multiplier > 1','……以及其他所有大于一的固定倍率'),960,696,41,{align:'center'});badge(c,tr('Eventually slower than each of these exponential rates','最终，都要比对应的指数增长更慢'),960,846,{w:1500,size:38});return;}
 heading(c,tr('A growth question','比较增长规律'),tr(mode==='subexp'?'Slower than every fixed exponential':'Two rates, both exponential',mode==='subexp'?'慢于每一种固定倍率的指数':'两种速度，都仍是指数'),{size:61});
 const x0=295,y0=765,w=1300,h=475;arrow(c,[x0,y0],[1700,y0],{bend:0,w:4,head:24,fill:P.coral});arrow(c,[x0,y0],[x0,255],{bend:0,w:4,head:24,fill:P.coral});label(c,tr('size','规模'),1710,822,34,{align:'right'});label(c,tr('work','计算量'),218,278,33,{align:'right'});
 const u=move(t,.4,3.8),pts=[];for(let i=0;i<=80*u;i++){const k=i/80;pts.push([x0+w*k,y0-h*(2**(6*k)-1)/63]);}if(pts.length>1)ink(c,pts,6,{color:P.coral});const pts2=[];for(let i=0;i<=80*u;i++){const k=i/80;pts2.push([x0+w*k,y0-h*(1.1**(6*k)-1)/63]);}if(pts2.length>1)ink(c,pts2,6,{color:P.tealD});
 label(c,'2ⁿ',1550,290,61,{kind:'slab',fill:P.coralD});label(c,'1.1ⁿ',1580,720,55,{kind:'slab',fill:P.tealD});
 if(mode==='subexp'){const pp=[];for(let i=0;i<=80*u;i++){const k=i/80;pp.push([x0+w*k,y0-h*.28*k]);}if(pp.length>1)ink(c,pp,5,{color:P.blueD});label(c,tr('schematic only','仅为概念示意'),405,858,28);badge(c,'2^(o(n))',1320,658,{w:540,size:52,fill:P.mustardL});}else badge(c,tr('A smaller fixed multiplier is still exponential','固定倍率再小，仍然是指数增长'),960,868,{w:1390,size:34});
}
export function square(c,t,f,o={}){
 const mode=o.mode||'claim';
 if(mode==='claim'||mode==='wording'){label(c,tr('Try this claim…','试试这句话……'),115,150,85,{kind:'script',plate:P.white});sheet(c,1050,520,{s:1.3,title:tr('EVERY REAL NUMBER','所有实数'),rows:[],blank:true,accent:P.coral,w:940,h:390});label(c,'x² > 0',1050,585,99,{kind:'slab',align:'center'});if(mode==='wording'){circle(c,500,710,83,P.blue);label(c,'0',500,741,75,{kind:'slab',align:'center'});arrowTo(c,[595,682],[825,620],move(t,.5,1.3));badge(c,tr('Zero was allowed all along','零，本来就在允许范围内'),1080,855,{w:1040});}else if(t>2)label(c,'?',1565,775,100,{kind:'slab',plate:P.mustardL});return;}
 if(mode==='examples'){
  heading(c,tr('Test a few numbers','先试几个数'),tr('Examples build a pattern','例子让我们看到规律'),{size:68});
  const first=o.reveal_frames?.[0]??f+100000,definitionAlpha=1-ss(seg(f,first,first+8));
  if(definitionAlpha>0){c.save();c.globalAlpha=definitionAlpha;tile(c,960,540,'x × x = x²',{w:1050,size:89,fill:P.white});label(c,tr('Multiply a number by itself','一个数，乘以它自己'),960,690,44,{align:'center'});c.restore();}
  const a=['1 × 1 = 1','2 × 2 = 4','−3 × −3 = 9'];
  for(let i=0;i<3;i++){const onset=o.reveal_frames?.[i]??f+100000;const u=ss(seg(f,onset,onset+8));if(u>0)at(c,960,350+i*190,u,()=>{tile(c,0,0,a[i],{w:1050,size:67,fill:P.white});check(c,647,0,{s:.7});});}return;
 }
 if(mode==='guess'){label(c,tr('A hundred successes…','试对了一百次……'),120,170,76,{kind:'script',plate:P.white});for(let i=0;i<20;i++)circle(c,340+(i%10)*135,330+Math.floor(i/10)*135,35,i<Math.floor(t*8)?P.avocado:P.white,{line:2.6});circle(c,970,710,112,P.white);label(c,'?',970,751,92,{kind:'slab',align:'center'});label(c,tr('Can one allowed case break it?','有没有一个允许的数，会让它失败？'),960,875,40,{align:'center'});return;}
 if(mode==='zero'){heading(c,tr('The allowed exception','一个允许的反例'),tr('Zero changes the verdict','零，让结论改变'),{size:73});const u=cue(t,C.square.place),x=lerp(-250,570,u);tile(c,x,520,'0',{w:280,size:105,fill:P.blue});if(t<C.square.withdraw[1]&&t>.2){const r=cue(t,C.square.withdraw);closeHand(c,[x-130-850*r,515+120*r],{from:[-220,600]});}if(t>=C.square.place[1]){label(c,'× 0 = 0',1110,560,111,{kind:'slab',align:'center'});check(c,1455,720,{yes:false});label(c,'0 > 0',1070,745,67,{kind:'slab',align:'center'});}badge(c,tr('One counterexample defeats “every”','一个反例，就能推翻“所有”'),960,867,{w:1310});return;}
 heading(c,tr('From testing to proof','从试例子，到证明'),tr('Cover every allowed case','覆盖全部允许的情况'),{size:72});circle(c,500,520,227,P.mustardL);label(c,'100',500,535,114,{kind:'slab',align:'center'});label(c,tr('examples','个例子'),500,620,42,{align:'center'});circle(c,1430,520,227,P.white);label(c,'∞',1430,557,155,{align:'center'});arrowTo(c,[790,520],[1130,520],move(t,.6,1.5));badge(c,tr('A pattern suggests. A proof explains why.','例子提示规律，证明解释为什么。'),960,859,{w:1430,size:35});
}
function proofSheet(c,x,y,{changed=false,active=false,compact=false}={}){sheet(c,x,y,{blank:true,title:tr(changed?'REVISED STATEMENT':'ORIGINAL STATEMENT',changed?'修改后的命题':'原命题'),rows:[],accent:changed?P.teal:P.coral,w:compact?630:700,h:430});label(c,tr(changed?'Every nonzero real x':'Every real x',changed?'所有非零实数 x':'所有实数 x'),x,y-30,compact?37:42,{align:'center',max:compact?595:660});label(c,'x² > 0',x,y+85,69,{kind:'slab',align:'center'});if(active)check(c,x+245,y+165,{yes:changed,s:.75});}
export function formal(c,t,f,o={}){
 const mode=o.mode||'machine';
 if(mode==='checklogic'){
  heading(c,tr('Inspect the reasoning','检查推理过程'),tr('A gap between steps','步骤之间，可能有缺口'),{size:70});
  sheet(c,960,540,{title:tr('SUPPLIED STATEMENT','送入的命题'),blank:true,accent:P.blue,w:1450,h:560});
  const xs=[480,960,1440];
  for(let i=0;i<3;i++){
   box(c,xs[i]-160,455,320,150,P.white,{line:3});
   label(c,tr(`STEP ${i+1}`,`步骤 ${i+1}`),xs[i],546,45,{kind:'slab',align:'center',max:295});
  }
  arrow(c,[660,530],[780,530],{bend:0,w:4,head:22,fill:P.tealD});
  // The missing justification is shown as a gap, never as a checked inference.
  ink(c,[[1140,530],[1178,530]],4,{color:P.coralD});
  arrow(c,[1242,530],[1260,530],{bend:0,w:4,head:18,fill:P.coralD});
  const u=ss(seg(f,o.gap_frame,o.gap_frame+10));
  if(u>0){c.save();c.globalAlpha=u;circle(c,1210,530,49,null,{line:4,color:P.coralD});label(c,'?',1210,547,51,{kind:'slab',align:'center'});label(c,tr('Needs justification','需要论证依据'),1210,695,38,{align:'center',max:640});c.restore();}
  const v=ss(seg(f,o.statement_frame,o.statement_frame+10));
  if(v>0){ink(c,[[645,350],[645+630*v,350]],5,{color:P.coralD});badge(c,tr('Also check: is this the intended statement?','还要检查：这是原本要证明的命题吗？'),960,865,{w:1510,size:36});}
  label(c,tr('Schematic of proof checking','证明检查的概念示意'),960,775,27,{align:'center'});return;
 }
 if(mode==='changed'){
  heading(c,tr('Look at the allowed numbers','看清允许取哪些数'),tr('One condition changes the domain','一个条件，改变了取值范围'),{size:64});
  // Consequence/detail after the two written statements, retaining left/right identity.
  // Both lines share a scale and continue beyond the labelled ticks. The right
  // domain already excludes zero; emphasis follows speech, never changing truth.
  const leftFocus=ss(seg(f,o.include_frame,o.include_frame+8));
  const rightFocus=ss(seg(f,o.exclude_frame,o.exclude_frame+8));
  for(let i=0;i<2;i++){
   const x=510+i*900,accent=i?P.tealD:P.coralD;
   label(c,tr(i?'REVISED STATEMENT':'ORIGINAL STATEMENT',i?'修改后的命题':'原命题'),x,310,36,{kind:'slab',align:'center',max:760});
   label(c,tr(i?'Every nonzero real number':'Every real number',i?'所有非零实数':'所有实数'),x,383,39,{align:'center',max:760});
   box(c,x-365,448,730,180,P.white,{line:3});
   // Two rays make continuation at both ends explicit; no discrete-dot sample.
   arrow(c,[x-20,514],[x-320,514],{bend:0,w:4,head:20,fill:accent});
   arrow(c,[x+20,514],[x+320,514],{bend:0,w:4,head:20,fill:accent});
   if(!i)ink(c,[[x-24,514],[x+24,514]],4,{color:accent});
   for(let n=-2;n<=2;n++){
    const xx=x+n*130;if(n)ink(c,[[xx,503],[xx,525]],3,{color:accent});
    label(c,String(n).replace('-','−'),xx,589,39,{align:'center'});
   }
   circle(c,x,514,i?18:14,i?P.white:accent,{line:3.5});
   const focus=i?rightFocus:leftFocus;
   if(focus>0){
    arrow(c,[x+105,665],[x+24,544],{u:focus,bend:0,w:3.7,head:19,fill:accent});
    c.save();c.globalAlpha=focus;
    label(c,tr(i?'Zero is excluded':'Zero is included',i?'零被排除':'包含零'),x,748,43,{kind:'slab',align:'center',max:770});c.restore();
   }
  }
  if(f>=o.result_frame)badge(c,tr('A proof of the revised claim does not prove the original','证明修改后的命题，不等于证明原命题'),960,860,{w:1600,size:34});
  return;
 }
 if(mode==='scope'){
  const drawMachine=()=>{
   heading(c,tr('A proof assistant','证明助手'),tr('Check the supplied statement','检查送进去的命题'),{size:70});
   sheet(c,390,510,{s:.87,title:tr('STATEMENT','命题'),rows:[tr('Assumptions','前提'),tr('Steps','步骤')],accent:P.blue,w:480,h:410});
   laptop(c,1110,545,{s:1.15,screen:'Lean',active:f>=o.checked_frame});
   arrowTo(c,[640,490],[815,490],move(t,.5,1.5));
   if(f>=o.checked_frame){check(c,1510,550,{s:1.5});badge(c,tr('Valid under the supplied assumptions','在送入的前提下成立'),960,855,{w:1330,size:38});}
  };
  const u=ss(seg(f,o.human_frame,o.human_frame+12));
  if(u<1)drawMachine();
  if(u>0){
   c.save();if(u<1){c.beginPath();c.ellipse(1110,510,2200*u,2200*u,0,0,Math.PI*2);c.clip();}
   // An internal iris changes the task, without declaring meaning verified.
   c.fillStyle=P.paper;c.fillRect(-20,-20,1960,1120);
   heading(c,tr('A second check','还要进行另一项核对'),tr('Does the meaning match?','表达的意思，一致吗？'),{size:72});
   researcher(c,385,807,{s:1,target:[170,-320],hand:'open',frame:f});
   sheet(c,1240,525,{title:tr('SUPPLIED STATEMENT','送入的命题'),blank:true,accent:P.blue,w:1090,h:530});
   label(c,tr('Which assumptions?','用了哪些前提？'),1240,476,50,{kind:'slab',align:'center',max:1010});
   const v=ss(seg(f,o.claim_frame,o.claim_frame+12));
   if(v>0){c.save();c.globalAlpha=v;label(c,tr('The same claim as the paper?','还是论文原来的主张吗？'),1240,621,46,{kind:'slab',align:'center',max:1010});c.restore();}
   if(f>=o.documentation_frame)label(c,tr('Distinction noted in Anthropic’s documentation','Anthropic 的说明中指出了这一区别'),1240,739,28,{align:'center',max:1010});
   c.restore();
  }return;
 }
 if(mode==='machine'){heading(c,tr('A proof assistant','证明助手'),tr('Check the supplied statement','检查送进去的命题'),{size:70});sheet(c,390,510,{s:.87,title:tr('STATEMENT','命题'),rows:[tr('Assumptions','前提'),tr('Steps','步骤')],accent:P.blue,w:480,h:410});laptop(c,1110,545,{s:1.15,screen:'Lean',active:t>2});arrowTo(c,[640,490],[815,490],move(t,.5,1.5));if(t>2.3){check(c,1510,550,{s:1.5});badge(c,tr('Check the meaning, too','还要核对表达的意思'),960,855,{w:1150,size:40});}return;}
 if(mode==='translation'){label(c,tr('Imagine a translation','想象一次翻译'),125,157,87,{kind:'script',plate:P.white});for(let i=0;i<2;i++){const x=510+i*900;sheet(c,x,510,{title:tr(i?'TRANSLATION':'QUESTION',i?'翻译':'问题'),rows:[i?'… !':'… ?'],accent:i?P.teal:P.coral,w:590,h:430});}arrowTo(c,[855,510],[1075,510],move(t,.8,1.6));badge(c,tr('A flawless answer needs the right question','答得完美，也得是同一道题'),960,857,{w:1300});return;}
 const condition=f>=(o.condition_frame??-1),valid=f>=(o.truth_frame??-1);
 heading(c,tr('Keep the statements side by side','把两个命题放在一起'),tr('Correct proof, of which statement?','证明正确，但证明的是哪一句？'),{size:62});
 proofSheet(c,510,520,{changed:false,active:true,compact:true});
 if(condition){proofSheet(c,1410,520,{changed:true,active:valid,compact:true});const u=ss(seg(f,o.condition_frame??0,(o.condition_frame??0)+16));ink(c,[[1150,515],[1150+380*u,515]],5,{color:P.tealD});}
 else {sheet(c,1410,520,{blank:true,title:tr('REVISED STATEMENT','修改后的命题'),accent:P.teal,w:630,h:430});label(c,'?',1410,595,100,{kind:'slab',align:'center'});}
 if(condition)badge(c,tr('“Nonzero” excludes the counterexample','“非零”排除了刚才的反例'),960,856,{w:1330});

}
export function reviewScene(c,t,f,o={}){
 const mode=o.mode||'compare';
 if(mode==='definitions'){
 heading(c,tr('Read beneath the headline','把标题下面的内容读清楚'),tr('What exactly is being claimed?','究竟主张了什么？'),{size:68});
 sheet(c,580,540,{title:tr('THE STATEMENT','准确命题'),blank:true,accent:P.coral,w:710,h:530});
 const names=[tr('Definitions','定义'),tr('Earlier results','已有结论'),tr('Exact conclusion','准确结论')];
 for(let i=0;i<3;i++){const y=435+i*145,u=move(t,.5+i*.8,1+i*.8);label(c,names[i],580,y,46,{align:'center',kind:'slab'});if(u>0){ink(c,[[300,y+25],[300+560*u,y+25]],5,{color:[P.coral,P.blueD,P.tealD][i]});arrowTo(c,[960,y],[1145,y],u);}}
 const questions=[tr('Which objects?','讨论什么对象？'),tr('Which dependencies?','依赖哪些结论？'),tr('The same in both versions?','两种表达一致吗？')];questions.forEach((q,i)=>badge(c,q,1470,420+i*145,{w:650,size:35,fill:i===2?P.mustardL:P.white}));
 badge(c,tr('Compare the paper with the formal statement','把论文与形式化命题对照起来'),960,875,{w:1460,size:35});return;
 }
 if(mode==='jobs'){
 heading(c,tr('Three complementary jobs','三件互相补充的工作'),tr('Argument, checking, examination','论证、检查、审查'),{size:65});
 const names=[tr('PAPER','论文'),tr('FORMAL MATERIAL','形式化材料'),tr('PUBLIC EXAMINATION','公开审查')],rows=[[tr('Argument','论证过程')],[tr('Logical steps','逻辑步骤')],[tr('Scope and limits','范围与局限')]];
 for(let i=0;i<3;i++){const u=move(t,.3+i*.75,.7+i*.75);if(u>0)at(c,370+i*590,520,Math.max(.01,u),()=>{sheet(c,0,0,{title:names[i],rows:rows[i],accent:[P.coral,P.blue,P.teal][i],w:490,h:430});});}
 badge(c,tr('Examine each team’s argument separately','两家公司的论证，需要分别检查'),960,860,{w:1430,size:37});return;
 }
 if(mode==='understanding'){
 heading(c,tr('Different questions, one research process','不同问题，互相补充'),tr('Validity, meaning, and reuse','有效性、含义与复用'),{size:70});
 const xs=[400,960,1520],titles=[tr('VALID?','有效吗？'),tr('WHICH CLAIM?','哪条命题？'),tr('WHY?','为什么？')],rows=[tr('Check the steps','检查推理步骤'),tr('Read the assumptions','读清成立条件'),tr('Explain the idea','解释关键想法')];
 for(let i=0;i<3;i++){circle(c,xs[i],500,205,[P.blue,P.white,P.mustardL][i]);label(c,titles[i],xs[i],507,i===1?43:57,{kind:'slab',align:'center',max:390});label(c,rows[i],xs[i],760,36,{align:'center'});if(i<2)arrowTo(c,[xs[i]+220,500],[xs[i]+340,500],move(t,.8+i,1.6+i));}
 badge(c,tr('Understanding lets others challenge, reuse and improve','理解，让别人能够质疑、复用和改进'),960,875,{w:1510,size:35});return;
 }
 if(mode==='bound'){heading(c,tr('Verification has a scope','核查有具体范围'),tr('Read the exact time bound','核对准确的时间界'),{size:68});sheet(c,520,520,{title:tr('REVISED PAPER','修订论文'),rows:[tr('Sharper bound','更强的时间界')],accent:P.coral,w:620,h:440});sheet(c,1400,520,{title:tr('FORMAL MATERIAL','形式化材料'),rows:[tr('Weaker bound','较弱的时间界')],accent:P.blue,w:620,h:440});arrowTo(c,[880,520],[1040,520],move(t,1,2));badge(c,tr('Still sufficient for the claimed refutation','仍足以支持其声称的反驳'),960,851,{w:1390,size:35});return;}
 if(mode==='public'){label(c,tr('Public examination','公开检查'),115,164,98,{kind:'script',plate:P.white});researcher(c,460,814,{s:.9,target:[170,-330],frame:f});researcher(c,1450,814,{s:.9,dir:-1,mentor:true,shirt:P.coral,target:[170,-330],frame:f+31});sheet(c,960,550,{title:'ETH',rows:[tr('Open questions','待检查的问题')],accent:P.blue,w:560,h:390});badge(c,tr('Participation is not certification','参与检查，不代表已经认证'),960,872,{w:1320,size:38});return;}
 if(mode==='limit'){label(c,tr('What this film does','本片的范围'),115,167,91,{kind:'script',plate:P.white});researcher(c,520,814,{s:1,target:[155,-320],hand:'open',frame:f});lines(c,tr('Explain published claims and the scope of checks.','解释公开主张与核查范围。'),930,370,790,60,{kind:'slab'});badge(c,tr('No independent reconstruction of every proof','未独立重建完整研究证明'),1290,795,{w:1000,size:34});return;}
 heading(c,tr('Three complementary jobs','三件互相补充的工作'),tr('Argument, checking, understanding','论证、检查、理解'),{size:65});const names=[tr('PAPER','论文'),tr('FORMAL STEPS','形式化步骤'),tr('EXAMINATION','公开检查')];for(let i=0;i<3;i++){const u=move(t,.3+i*.75,.7+i*.75);if(u>0)at(c,370+i*590,520,Math.max(.01,u),()=>{sheet(c,0,0,{title:names[i],rows:[['… → ?','✓ → ✓','? → !'][i]],accent:[P.coral,P.blue,P.teal][i],w:465,h:430});});}badge(c,tr('Definitions · assumptions · exact claim','定义 · 前提 · 准确命题'),960,855,{w:1320,size:37});
}
export function direction(c,t,f,o={}){
 const mode=o.mode||'desk';
 if(mode==='desk'&&o.mentor_focus){
 label(c,tr('Ask with your supervisor…','和导师一起追问……'),110,150,82,{kind:'script',plate:P.white});
 researcher(c,370,816,{s:.86,target:[155,-335],face:'think',frame:f});researcher(c,1570,814,{s:1.13,dir:-1,mentor:true,shirt:P.coral,target:[160,-335],hand:'open',frame:f+20});
 const qs=[tr('A different method?','不同的方法？'),tr('Another case?','别的情况？'),tr('What have we learned?','已经学到了什么？')];qs.forEach((q,i)=>{const u=move(t,.5+i*.75,1+i*.75);if(u>0)at(c,960,350+i*183,Math.max(.01,u),()=>badge(c,q,0,0,{w:830,size:42,fill:[P.white,P.blueL,P.mustardL][i]}));});
 badge(c,tr('Turn accumulated knowledge into a new question','把已有积累，变成下一个问题'),960,883,{w:1390,size:35});return;
 }
 if(mode==='retain'){
 heading(c,tr('What remains useful?','哪些东西仍然有用？'),tr('Keep the reasoning. Recheck the premise.','保留推理，重查前提'),{size:63});
 sheet(c,450,540,{title:tr('PREMISE','前提'),rows:['ETH','?'],accent:P.coral,w:500,h:440});
 sheet(c,1280,540,{title:tr('CONDITIONAL ARGUMENT','条件推理'),rows:[tr('IF … THEN …','如果……那么……')],accent:P.teal,w:760,h:440});
 arrowTo(c,[755,520],[845,520],move(t,.5,1.4));if(t>1.4){check(c,1530,675,{s:.8});label(c,tr('can remain valid','仍可能有效'),1280,667,37,{align:'center'});}
 badge(c,tr('Methods can remain useful when a premise is challenged','前提受挑战，方法和技术仍可能有用'),960,866,{w:1490,size:35});return;
 }
 if(mode==='conditional'){heading(c,tr('What happens to older work?','旧研究会怎样？'),tr('Revisit the premise','重新检查前提'),{size:77});tile(c,520,510,'ETH',{w:445,fill:P.mustardL,size:91});tile(c,1410,510,tr('Hard problem','困难问题'),{w:620,fill:P.white,size:53});arrowTo(c,[795,510],[1040,510],1);label(c,tr('IF','如果'),520,341,49,{kind:'script'});label(c,tr('THEN','那么'),1410,341,49,{kind:'script',align:'center'});if(t>1.5){circle(c,709,647,55,P.coral);label(c,'?',709,669,61,{kind:'slab',align:'center'});}badge(c,tr('The implication can survive a challenged premise','前提受挑战，不等于条件推理失效'),960,848,{w:1470});return;}
 if(mode==='toolbox'){label(c,tr('Two years do not vanish','两年的积累不会消失'),115,155,77,{kind:'script',plate:P.white});box(c,400,435,1130,345,P.teal,{radius:25,line:4});box(c,785,365,360,80,P.tealD,{radius:20,line:4});for(let i=0;i<3;i++){const u=move(t,.4+i*.6,1+i*.6);const x=590+i*370,y=lerp(680,435,u);sheet(c,x,y,{title:tr(['Skill','Method','Insight'][i],['技能','方法','理解'][i]),rows:[],accent:[P.coral,P.blue,P.mustard][i],w:270,h:300});}box(c,400,635,1130,145,P.teal,{radius:15,line:4});label(c,tr('A NEW RESEARCH PLAN','新的研究计划'),960,735,54,{kind:'slab',align:'center'});return;}
 if(mode==='routes'){heading(c,tr('Questions to investigate','值得继续调查的问题'),tr('Where can this method go?','这套方法，还能走向哪里？'),{size:69});circle(c,340,535,103,P.mustardL);label(c,'?',340,575,97,{kind:'slab',align:'center'});const names=[tr('Clearer proof','更清楚的论证'),tr('More general result','更一般的结果'),tr('New assumptions','不同的前提')];for(let i=0;i<3;i++){const y=300+i*230;arrowTo(c,[470,535],[1080,y+25],move(t,.5+i*.45,1.4+i*.45));badge(c,names[i],1430,y+25,{w:660,size:40});}label(c,tr('Possibilities to investigate—not a ready-made thesis','这些是待研究的方向，不是现成论文'),960,875,31,{align:'center'});return;}
 label(c,tr('Back at the desk','回到研究桌前'),110,145,86,{kind:'script',plate:P.white});desk(c,520,680,1200);sheet(c,980,564,{s:.8,title:tr('NEXT PLAN','下一步'),rows:['… ?'],accent:P.coral,w:450,h:340});researcher(c,610,815,{s:.92,target:[170,-320],frame:f,face:'think'});researcher(c,1560,815,{s:.96,dir:-1,mentor:true,shirt:P.coral,target:[160,-335],hand:'open',frame:f+20});badge(c,tr('Compare the result. Reassess the plan.','核对结果，再调整计划。'),960,867,{w:1210,size:35});
}
export function revise(c,t,f,o={}){
 const mode=o.mode||'question';
 if(mode==='meaning_detail'){
 heading(c,tr('Read the difference','读出这一笔的区别'),tr('One stroke changes the conclusion','一道横线，改变结论'),{size:70});
 sheet(c,505,530,{blank:true,title:tr('STRICTLY POSITIVE','严格大于零'),accent:P.coral,w:650,h:460});sheet(c,1420,530,{blank:true,title:tr('NONNEGATIVE','大于或等于零'),accent:P.teal,w:650,h:460});
 for(const x of [505,1420]){label(c,'x²',x-120,562,83,{kind:'slab',align:'center'});label(c,'>',x,562,83,{kind:'slab',align:'center'});label(c,'0',x+112,562,83,{kind:'slab',align:'center'});}ink(c,[[1393,580],[1448,580]],6);
 label(c,tr('Zero fails','零不满足'),505,684,39,{align:'center'});label(c,tr('Zero fits','零满足'),1420,684,39,{align:'center'});arrowTo(c,[875,520],[1050,520],move(t,.6,1.5));
 badge(c,tr('Explain why the written change works','不仅会改写，还要解释为什么成立'),960,868,{w:1460,size:37});return;
 }
 if(mode==='reuse'){label(c,tr('Understanding makes reuse possible','理解，才让复用成为可能'),110,155,79,{kind:'script',plate:P.white});const names=[tr('Explain','解释'),tr('Simplify','简化'),tr('Adapt','改造')];for(let i=0;i<3;i++){const x=420+i*540;circle(c,x,520,183,[P.mustardL,P.white,P.blue][i]);label(c,names[i],x,538,52,{kind:'slab',align:'center'});if(i<2)arrowTo(c,[x+205,520],[x+330,520],move(t,.5+i,1.2+i));}badge(c,tr('Change an assumption. Explain the consequence.','改一个条件，说清楚后果。'),960,858,{w:1410});return;}
 if(mode==='algorithm'){heading(c,tr('Ask about the idea','追问关键想法'),tr('Why does it save work?','为什么能省计算？'),{size:75});laptop(c,570,535,{s:1.1,screen:'?'});for(let i=0;i<3;i++)badge(c,tr(['Key idea','Transfer','Practical use'][i],['关键想法','迁移方法','实际应用'][i]),1370,330+i*215,{w:710,size:47,fill:[P.mustardL,P.white,P.blue][i]});return;}
 const u=cue(t,C.revise.write),changed=mode==='stroke'&&t>=C.revise.write[1]||mode==='meaning';label(c,tr(mode==='question'?'Bring zero back in.':'One extra stroke.',mode==='question'?'把零，再放回来。':'只多一道横线。'),115,162,87,{kind:'script',plate:P.white});
 box(c,300,295,1320,460,P.white,{line:4});label(c,tr('EVERY REAL NUMBER','所有实数'),960,350,44,{kind:'slab',align:'center'});label(c,'x²',705,593,146,{kind:'slab',align:'center'});label(c,'>',990,593,146,{kind:'slab',align:'center'});label(c,'0',1260,593,146,{kind:'slab',align:'center'});
 if(mode==='stroke'){if(u>0)ink(c,[[944,624],[944+97*u,624]],8,{color:P.ink});if(t>C.revise.approach[0]&&t<C.revise.withdraw[1]){const r=cue(t,C.revise.withdraw),approach=1-cue(t,C.revise.approach);const tip=[944+97*u+1050*r+1150*approach,624-130*r-120*approach];pencilHand(c,tip);}}else if(mode==='meaning')ink(c,[[944,624],[1041,624]],8);
 if(changed){check(c,1500,665,{s:.8});badge(c,tr('Zero now satisfies the conclusion','零，现在也满足结论'),960,864,{w:1240,size:39});}else badge(c,tr('Change the conclusion so zero fits','怎样改结论，才能把零包含进来？'),960,864,{w:1310,size:36});
}
export function access(c,t,f,o={}){
 if(o.restage===2){accessRestaged(c,t,f,o);return;}
 const mode=o.mode||'desks';
 if(mode==='fund'){heading(c,tr('Resources for continued work','支持继续研究的资源'),tr('An announced commitment','一项公开承诺'),{size:76});circle(c,525,535,255,P.white);label(c,'$15M',525,552,113,{kind:'slab',align:'center'});label(c,'15 OCT 2026',525,655,31,{align:'center'});lines(c,tr('Combined funding and resources','资金与资源的合计承诺'),1040,390,700,55,{kind:'slab'});label(c,'Simons Foundation',1380,653,44,{align:'center'});label(c,'Anthropic + OpenAI',1380,723,35,{align:'center'});return;}
 if(mode==='supports'){label(c,tr('Access to the process','也要能参与过程'),115,160,88,{kind:'script',plate:P.white});const names=[tr('Time','时间'),tr('Training','训练'),tr('Compute','算力')];for(let i=0;i<3;i++){const x=430+i*540,u=move(t,.3+i*.5,.8+i*.5);at(c,x,520,Math.max(.001,u),()=>{circle(c,0,0,187,[P.mustardL,P.blue,P.white][i]);if(i===0)clock(c,0,-15,.7,.3);else if(i===1)sheet(c,0,-15,{s:.45,title:'… → !',w:390,h:330});else laptop(c,0,-15,{s:.5,screen:'…'});label(c,names[i],0,276,47,{kind:'slab',align:'center'});});}return;}
 if(mode==='autonomy'){heading(c,tr('Who can keep asking?','谁能继续提出问题？'),tr('Research autonomy','研究自主权'),{size:77});researcher(c,450,815,{s:1,target:[155,-320],frame:f});lines(c,tr('Tools and computation must reach researchers.','工具和计算资源，需要真正到达研究者手里。'),930,340,760,56,{kind:'slab'});badge(c,tr('Evaluate actual support received','看研究者实际获得的支持'),1260,830,{w:1030});return;}
 label(c,tr('The same public paper…','拿到同一篇公开论文……'),110,150,84,{kind:'script',plate:P.white});for(let i=0;i<2;i++){const x=450+i*1000;desk(c,x-300,650,610);sheet(c,x-60,540,{s:.55,title:tr('PAPER','论文'),w:360,h:360});laptop(c,x+130,540,{s:.48,screen:i?'?':'…',active:!i});label(c,tr(i?'Tools still needed':'Experiments continue',i?'还需要工具与算力':'可以继续实验'),x,827,38,{align:'center'});}ink(c,[[960,260],[960,840]],3,{color:P.inkSoft,breaks:.15});label(c,tr('Illustration, not a survey','情境示意，并非调查统计'),960,890,27,{align:'center'});
}
export function recap(c,t,f,o={}){
 if(o.restage===3&&o.mode==='end'){closing(c,t,f,o);return;}
 if(o.restage===2&&o.mode!=='end'){recall(c,t,f,o);return;}
 const mode=o.mode||'card',active=o.active??4;const names=[tr('Result','具体结论'),tr('Assumptions','成立条件'),tr('Checks','核查范围'),tr('Contribution','新增贡献')];
 if(mode==='end'){label(c,tr('Keep asking good questions.','继续提出好问题。'),110,190,87,{kind:'script',plate:P.white});researcher(c,560,815,{s:1.02,target:[155,-320],hand:'open',frame:f});sheet(c,1260,515,{title:tr('THE NEXT QUESTION','下一个问题'),rows:['… ?'],accent:P.blue,w:630,h:410});label(c,tr('Ooh, Lemme See!','让我捅咕捅咕'),1260,809,48,{kind:'slab',align:'center'});return;}
 label(c,tr('Keep four questions beside the headline.','把四个问题，放在标题旁。'),110,135,65,{kind:'script',plate:P.white});for(let i=0;i<4;i++){const x=510+(i%2)*900,y=380+Math.floor(i/2)*330,shown=i<active;box(c,x-355,y-105,710,220,shown?[P.mustardL,P.white,P.blue,P.pink][i]:P.paper,{line:3.5});circle(c,x-270,y-15,43,P.white,{line:3});label(c,String(i+1),x-270,y,37,{kind:'slab',align:'center'});if(shown)label(c,names[i],x+40,y+3,45,{kind:'slab',align:'center',max:545});}
 label(c,tr(mode==='hold'?'Pause and keep this card.':'What is missing from the headline?',mode==='hold'?'可以暂停，留下这张四问卡。':'标题里，哪一个问题还没有回答？'),960,879,34,{align:'center'});
}
export const advancedScenes={growth,square,formal,reviewScene,direction,revise,access,recap};
