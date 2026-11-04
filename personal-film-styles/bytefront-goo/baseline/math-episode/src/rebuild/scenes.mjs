import {setGooShot,clothStroke} from './goo.mjs';
import {identity} from './identity.mjs';
import {C,cue,travel,decisive,settle} from './motion.mjs';
import {P,tr,begin,finish,at,box,circle,label,lines,heading,caption,sheet,desk,pencil,researcher,closeHand,check,arrowTo} from './stage.mjs';
import {shape,ink,ellipse,spline,rect,rrect,plane,rays,sparkle,ss,seg,lerp,star,text} from './toon.mjs';
import {gooHand as drawHand,wristAtContact,GOO_NEAR_HAND} from './goo-hand.mjs';
import {lessonScenes} from './lessons.mjs';
import {advancedScenes} from './advanced.mjs';

function release(c,t,f){
 heading(c,tr('A new arrival','一份新成果'),tr('Mathematics, at scale','数学，开始批量产出'),{max:1700,size:66});
 // A physical paper feed reveals the count, not a disembodied number card.
 at(c,1120,510,1,()=>{box(c,-370,-200,740,340,P.teal,{radius:34,line:4.5});box(c,-315,-154,630,130,P.tealD,{radius:15,line:3});
 label(c,'OpenAI',0,-66,66,{kind:'slab',align:'center',fill:P.white});box(c,-290,48,580,28,P.ink,{radius:12,line:0});
 for(let i=0;i<3;i++){const out=travel(t,C.release.feed[0]+i*C.release.stagger,C.release.feed[1]+i*C.release.stagger);shape(c,[[-238+i*9,70], [240+i*9,70],[255+i*9,70+out*(210+i*12)],[-252+i*9,70+out*(210+i*12)]],{fill:P.white,line:3,seed:30+i});}
 if(t>1.05){label(c,'722',10,222,104,{kind:'slab',align:'center',plate:P.mustardL});label(c,tr('initial manuscripts','首批数学手稿'),10,281,35,{align:'center'});}circle(c,310,-86,14,t>1?P.mustard:P.coral,{line:2});});
 researcher(c,520,814,{s:1,frame:f,target:[160,-335],hand:'open'});
 label(c,'06 OCT 2026',1605,831,25,{align:'right'});
}
function study(c,t,f,{arrive=false}={}){
 label(c,tr('At the research desk…','回到研究桌前……'),110,126,70,{kind:'script',plate:P.white});
 desk(c,645,679,1100);
 // Researcher's index/pen touches the visible top sheet; marks grow from its tip.
 const u=cue(t,C.study.write),pen=[935+26*u,662-19*u];
 sheet(c,1155,520,{s:.76,title:tr('MY PROBLEM','我的课题'),rows:['… ?'],accent:P.blue,angle:-.08,w:360,h:320});
 shape(c,[[820,642],[1070,634],[1114,678],[836,679]],{fill:P.white,line:3,seed:31});
 if(u>0)ink(c,[[935,662],pen],3.4,{color:P.ink,upto:1});
 const target=[(pen[0]-740)/1.05-18,(pen[1]-814)/1.05-20];
 pencil(c,...pen,{angle:-.9,s:.65});
 const penPoint=[(pen[0]+Math.cos(-.9)*50-740)/1.05,(pen[1]+Math.sin(-.9)*50-814)/1.05];
 researcher(c,740,814,{s:1.05,frame:f,target,contact:{point:penPoint,kind:'writeGrip',branch:1},hand:'writeGrip',face:arrive&&t>2.6?'surprise':'think'});
 if(arrive){const k=cue(t,C.study.arrival);sheet(c,lerp(2130,1510,k),520,{s:.9,title:tr('A NEW PROOF','一份新证明'),rows:[tr('Same question?','同一道题？')],accent:P.coral,angle:lerp(.1,-.04,k),w:350,h:340});
 if(t>3.4){arrowTo(c,[1350,430],[1240,430],ss(seg(t,3.4,3.9)));label(c,'?',1585,305,114,{kind:'slab',plate:P.white});}}
 else{box(c,1340,330,330,250,P.white,{line:3});box(c,1340,330,330,52,P.coral,{line:3});label(c,tr('RESEARCH','研究记录'),1505,369,30,{align:'center',fill:P.white});label(c,'2',1505,479,86,{kind:'slab',align:'center'});label(c,tr('years','年'),1505,542,39,{align:'center'});}
 label(c,tr('A hypothetical student','一位假设的博士生'),115,861,27);
}
function calendar(c,t,f){
 heading(c,tr('Before the announcement','在新成果出现之前'),tr('Two years of work','两年的研究'),{size:72});
 const turn=travel(t,1.2,1.7);
 box(c,375,300,1130,510,P.white,{line:4.2});box(c,375,300,1130,85,P.coral,{line:4});label(c,tr('RESEARCH NOTEBOOK','研究手记'),940,360,47,{kind:'slab',align:'center',fill:P.white});
 for(let j=0;j<3;j++){const x=585+j*360;circle(c,x,535,77,[P.mustard,P.blue,P.avocado][j]);label(c,String(j+1),x,563,66,{kind:'slab',align:'center'});label(c,tr(['Question','Attempts','A first proof?'][j],['问题','尝试','首次证明？'][j]),x,684,38,{align:'center'});if(j<2)arrowTo(c,[x+105,535],[x+245,535],travel(t,.4+j*.55,.75+j*.55));}
 ink(c,[[515,744],[515+850*turn,744]],5,{color:P.tealD});
 label(c,tr('A plan built around one result','围绕一个结果制定的计划'),940,866,34,{align:'center'});
}
function paperDetail(c,t,f){
 heading(c,tr('Then, a new manuscript','然后，新手稿来了'),tr('The same problem?','会是同一道题吗？'),{size:68});
 sheet(c,700,555,{s:1.35,title:tr('MY DRAFT','我的草稿'),rows:[tr('First proof','首次证明'),'… ?'],accent:P.blue,w:430,h:350,angle:-.04});
 const u=cue(t,C.paperDetail.place),x=lerp(2260,1280,u);
 sheet(c,x,555,{s:1.35,title:tr('NEW MANUSCRIPT','新手稿'),rows:[tr('A claimed solution','声称给出解答')],accent:P.coral,w:430,h:350,angle:.035+.045*settle(t,C.paperDetail.place[1])});
 if(t<C.paperDetail.withdraw[1]){const withdraw=cue(t,C.paperDetail.withdraw),grip=[x+283+750*withdraw,343-410*withdraw];const kind=t<C.paperDetail.withdraw[0]?'grip':'open',wrist=wristAtContact(grip,Math.PI/2,kind,GOO_NEAR_HAND,2.35),end=[wrist[0],wrist[1]-110];clothStroke(c,spline([[2180,190],[end[0]+140,end[1]-95],end],false,7),100);drawHand(c,...wrist,Math.PI/2,kind,GOO_NEAR_HAND,2.35);}
 if(t>C.paperDetail.withdraw[1]){circle(c,985,620,58,P.mustard,{line:3});label(c,'?',985,647,70,{kind:'slab',align:'center'});}
 label(c,tr('A claim to examine — not a finished verdict','这是待检查的主张，还不是最终结论'),960,866,32,{align:'center'});
}
function reaction(c,t,f){
 const thought=travel(t,1.3,1.65),point=[lerp(105,50,thought),lerp(-363,-419,thought)];
 circle(c,1265,500,342,P.white,{line:3.4});
 // Redraw the actor over its medallion, with a stable thinking pose.
 researcher(c,1250,818,{s:1.06,frame:f,target:point,hand:t<1.55?'open':'grip',face:'think'});
 label(c,tr('Celebrate…','先庆祝……'),135,280,108,{kind:'script',plate:P.white,max:900});
 lines(c,tr('or call your supervisor?','还是先找导师？'),135,417,890,72,{kind:'slab',plate:P.mustardL});
 box(c,190,655,555,88,P.ink,{radius:40,line:0});label(c,tr('THE HUMAN QUESTION','人的问题'),467,712,34,{align:'center',fill:P.white});
}
function claims(c,t,f){
 heading(c,tr('One announcement, bigger questions','从一条新闻，到更大的问题'),tr('How hard is the problem?','问题究竟有多难？'),{size:66});
 const labels=['OpenAI','Anthropic'];for(let i=0;i<2;i++){const u=travel(t,.25+i*.65,.58+i*.65);at(c,520+i*860,555,Math.max(.001,u),()=>{sheet(c,0,0,{title:labels[i],rows:['ETH',tr('Research claim','研究主张')],accent:i?P.blue:P.coral,w:560,h:450});});}
 label(c,tr('The precise claim and its checks come next','接下来，分别看准确主张与检查范围'),960,865,34,{align:'center'});
}
export function switchProp(c,x,y,{on=false,position=on?1:0,s=1,labelText='A',stateLabelY=202,screenInk=false}={}){at(c,x,y,s,()=>{
 const lw=screenInk?1/s:1;
 box(c,-105,-128,210,256,P.white,{radius:22,line:4*lw,regK:lw});circle(c,0,0,54,P.tealD,{line:3.6*lw,regK:lw});
 const yy=lerp(53,-53,position);ink(c,[[0,0],[0,yy]],13+8*lw,{taper:false,wob:.05});ink(c,[[3,2],[3,yy]],13,{color:P.chrome,taper:false,wob:.05});shape(c,ellipse(0,yy,31,20,40),{fill:on?P.coral:P.mustard,line:3.4*lw,regK:lw,seed:98});
 label(c,labelText,0,-165,55,{kind:'slab',align:'center'});label(c,on?tr('ON','开'):tr('OFF','关'),0,stateLabelY,35,{align:'center'});});}
function switchIntro(c,t,f){
 label(c,tr('Start with','先从'),110,155,76,{kind:'script',plate:P.white});
 lines(c,tr('a few switches.','几个开关说起。'),110,265,830,83,{kind:'slab',plate:P.white});
 const on=t>=C.switchIntro.move[1],position=cue(t,C.switchIntro.move),detail={x:1250,y:477,s:2.05};
 switchProp(c,detail.x,detail.y,{s:detail.s,on,position,labelText:'',stateLabelY:171,screenInk:true});
 if(t>C.switchIntro.approach[0]&&t<C.switchIntro.withdraw[1]){const withdraw=cue(t,C.switchIntro.withdraw),y=lerp(-110,detail.y+53*detail.s,cue(t,C.switchIntro.approach))-106*detail.s*position-800*withdraw;closeHand(c,[detail.x+450*withdraw,y],{});}
 if(t>C.switchIntro.states){circle(c,520,617,103,P.blue);circle(c,790,617,103,P.coral);label(c,'0',520,654,86,{kind:'slab',align:'center'});label(c,'1',790,654,86,{kind:'slab',align:'center'});arrowTo(c,[1005,675],[921,640],ss(seg(t,C.switchIntro.states,C.switchIntro.states+.3)));}
}
// Questions remain unresolved; the person shifts from the incoming result to reflection.
function openingQuestion(c,t,f,{second_question}={}){
 const human=f>=second_question,thought=travel(f,second_question,second_question+10);
 heading(c,tr('After the announcement','消息公布之后'),human?tr('What can people add?','人还能贡献什么？'):tr('What has changed?','改变了什么？'),{size:76});
 sheet(c,1250,528,{s:1.2,title:tr('NEW MANUSCRIPT','一份新手稿'),rows:[tr('A claimed solution','声称给出解答')],accent:P.coral,w:520,h:390,angle:.025});
 label(c,'?',1250,678,102,{kind:'slab',align:'center'});
 researcher(c,615,815,{s:1.02,frame:f,target:[lerp(170,50,thought),lerp(-330,-419,thought)],hand:human?'grip':'open',face:'think'});
}
function switchLesson(c,t,f,{approach_start,contact,move_end,release_end,states}={}){
 label(c,tr('Two possible states','两种可能的状态'),110,145,45,{kind:'script',plate:P.white});
 lines(c,tr('One switch.','一个开关'),110,255,830,88,{kind:'slab',plate:P.white});
 const position=1-travel(f,Math.max(contact,move_end-6),move_end),detail={x:1250,y:477,s:2.05};
 switchProp(c,detail.x,detail.y,{s:detail.s,on:f<move_end,position,labelText:'',stateLabelY:171,screenInk:true});
 if(f>=approach_start&&f<release_end){
  const enter=travel(f,Math.max(approach_start,contact-12),contact),withdraw=travel(f,move_end+4,Math.min(release_end,move_end+18));
  const y=lerp(-110,detail.y-53*detail.s,enter)+106*detail.s*(1-position)-800*withdraw;
  closeHand(c,[detail.x+450*withdraw,y],{});
 }
 if(f>=states){
  circle(c,410,605,100,P.blue);circle(c,725,605,100,P.coral);
  label(c,'0',410,641,86,{kind:'slab',align:'center'});label(c,'1',725,641,86,{kind:'slab',align:'center'});
  label(c,tr('OFF','关'),410,762,34,{align:'center'});label(c,tr('ON','开'),725,762,34,{align:'center'});
 }
}
export const scenes={identity,openingQuestion,switchLesson,release,study,calendar,paperDetail,reaction,claims,switchIntro,...lessonScenes,...advancedScenes};
export function paint(c,shot,frame,lang,cap=''){
 setGooShot(shot);
 const poseFrame=Math.floor(frame/2)*2,local=Math.max(0,Math.min(shot.end-shot.start-1,poseFrame-shot.start));const t=shot.options?.action_origin===undefined?local/24:Math.max(0,(poseFrame-shot.options.action_origin)/24);
 begin(c,frame,lang,P[shot.ground],{burst:shot.burst??false,floor:shot.floor??true});
 if(!scenes[shot.scene])throw Error('Unknown scene '+shot.scene);scenes[shot.scene](c,t,poseFrame,shot.options||{});
 caption(c,cap);finish(c);
}
