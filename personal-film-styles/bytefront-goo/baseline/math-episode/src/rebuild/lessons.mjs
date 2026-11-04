import {C,cue,travel,decisive,settle} from './motion.mjs';
// New-subject lesson staging. Never distribute as a style starter.
import {P,tr,at,box,circle,label,lines,heading,sheet,desk,pencil,researcher,closeHand,check,arrowTo} from './stage.mjs';
import {shape,ink,ellipse,spline,plane,rays,sparkle,ss,seg,lerp} from './toon.mjs';
import {drawHand} from './hand.mjs';
import {switchProp} from './scenes.mjs';
import {branchTree,branchTable} from './branch_performance.mjs';
import {rulePerformance} from './rule_performance.mjs';

function tag(c,s,x,y,{w=600,fill=P.white,size=32}={}){box(c,x-w/2,y-35,w,70,fill,{line:2.8,radius:11});label(c,s,x,y+12,size,{align:'center',max:w-35});}
function folder(c,x,y,{s=1,open=false,title='',front=true}={}){at(c,x,y,s,()=>{shape(c,[[-230,-130],[-230,-180],[-105,-180],[-65,-135],[230,-135],[230,170],[-230,170]],{fill:P.kraftL,line:4,seed:221});if(front){shape(c,[[-250,-80],[250,-80],[230,170],[-230,170]],{fill:P.mustard,line:4,seed:222});if(title)label(c,title,0,75,50,{kind:'slab',align:'center',max:440});}});}
function grip(c,x,y){const wrist=[x,y-62];ink(c,spline([[2140,y-215],[x+190,y-180],wrist],false,8),54,{seed:223,taper:false,wob:.05});ink(c,spline([[2145,y-211],[x+195,y-176],[x+4,y-58]],false,8),44,{color:P.mustard,seed:224,taper:false,wob:.05});drawHand(c,...wrist,Math.PI/2,'grip',-1,2.2);}
export function filing(c,t,f,o={}){
 const mode=o.mode||'count';heading(c,tr('Read the unit','先看计数单位'),tr(mode==='count'?'What does 722 count?':mode==='group'?'Several papers, one family':mode==='overlap'?'Find the exact overlap':'Sheets and folders',mode==='count'?'722，到底数什么？':mode==='group'?'多篇手稿，一组成果':mode==='overlap'?'找到准确的交集':'手稿数，与分组数'),{size:65});
 if(mode==='units'){for(let i=0;i<3;i++)sheet(c,480+i*25,520-i*20,{title:i===2?'722':'',rows:i===2?[tr('manuscripts','篇手稿')]:[],accent:P.teal,w:430,h:400});folder(c,1390,550,{s:1.2,title:'372'});label(c,tr('sheets','纸张'),520,820,48,{kind:'slab',align:'center'});label(c,tr('families of results','组相关成果'),1390,820,43,{kind:'slab',align:'center'});return;}
 if(mode==='overlap'){researcher(c,380,815,{s:.95,frame:f,target:[170,-320],face:'think'});sheet(c,1035,550,{s:1.14,title:tr('YOUR QUESTION','你的问题'),rows:['… ?'],accent:P.blue,w:430,h:390});sheet(c,1515,550,{s:1.14,title:tr('THE RESULT','新的结果'),rows:['… ?'],accent:P.coral,w:430,h:390});if(t>1){arrowTo(c,[1245,540],[1290,540],ss(seg(t,1,1.5)));tag(c,tr('Compare the exact statements','逐字核对准确命题'),1260,858,{w:970});}return;}
 if(mode==='count'){for(let i=0;i<5;i++)sheet(c,440+i*22,530-i*16,{s:1.03,title:i===4?'722':'',rows:i===4?[tr('manuscripts','篇手稿')]:[],accent:P.teal,w:400,h:380});
 circle(c,1330,538,223,P.white);label(c,'722',1330,542,125,{kind:'slab',align:'center'});label(c,tr('independent problems?','个独立问题？'),1330,625,37,{align:'center'});if(t>1.5){check(c,1550,346,{yes:false,s:1.15});tag(c,tr('Manuscripts ≠ distinct solved problems','手稿数 ≠ 独立问题数'),960,855,{w:1160,size:35});}return;}
 const labels=[tr('Main result','主要结果'),tr('Supporting proof','补充证明'),tr('Another route','另一条路径')],u=cue(t,C.filing.place),base=lerp(570,1320,u);
 folder(c,1370,626,{s:1.1,front:false});
 for(let i=0;i<3;i++)sheet(c,base+i*34,lerp(450+i*35,520+i*28,u),{s:.7,title:labels[i],accent:[P.teal,P.blue,P.coral][i],w:350,h:350,angle:0});
 shape(c,[[1095,538],[1645,538],[1623,813],[1117,813]],{fill:P.mustard,line:4,seed:225});if(f>=(o.count_frame??0)){label(c,'372',1370,699,111,{kind:'slab',align:'center'});label(c,tr('families of related results','组相关成果'),1370,766,32,{align:'center'});}
 if(t>.15&&t<C.filing.withdraw[1]){const r=cue(t,C.filing.withdraw),a=1-cue(t,C.filing.approach);grip(c,base+175+750*r+1400*a,lerp(396,440,u)-600*r-200*a);}
 label(c,tr('Initial release · 6 October 2026','2026年10月6日首发'),170,862,28);
}
function binary(c,x,y,n,value,focus=false){box(c,x,y,104+n*66,68,focus?P.mustardL:P.white,{line:2.6});for(let i=0;i<n;i++){const v=(value>>(n-1-i))&1;circle(c,x+50+i*66,y+33,20,v?P.coral:P.blue,{line:2});label(c,String(v),x+50+i*66,y+43,27,{align:'center'});}}
export function branches(c,t,f,o={}){
 const mode=o.mode||'tree';if(mode==='tree')return branchTree(c,t,f,o);if(mode==='table')return branchTable(c,t,f,o);heading(c,tr('Two choices per switch','每个开关有两种选择'),tr(mode==='large'?'One more switch doubles it':mode==='warning'?'A count is not a runtime':'Follow the possibilities',mode==='large'?'每加一个开关，组合翻倍':mode==='warning'?'组合数不是运行时间':'沿着分支，看所有可能'),{size:65});
 if(mode==='large'){for(let i=0;i<2;i++){const x=510+i*900;circle(c,x,520,246,i?P.blue:P.mustardL);label(c,i?'20':'10',x,473,109,{kind:'slab',align:'center'});label(c,tr('switches','个开关'),x,546,40,{align:'center'});label(c,i?'1,048,576':'1,024',x,665,i?59:79,{kind:'slab',align:'center'});}arrowTo(c,[806,520],[1110,520],travel(t,.5,1.05));label(c,tr('possible combinations','种可能组合'),960,862,35,{align:'center'});return;}
 if(mode==='warning'){researcher(c,440,815,{s:1,frame:f,target:[170,-330],hand:'point'});circle(c,1195,520,252,P.white);label(c,'2ⁿ',1195,500,120,{kind:'slab',align:'center'});lines(c,tr('possible settings','种可能组合'),1195,590,490,44,{align:'center'});tag(c,tr('Not a measured runtime','不是实测运行时间'),1195,850,{w:850,size:38});return;}
}
const RULES_EN=['A ON  or  B ON  or  C OFF','A OFF  or  B ON  or  C ON','A ON  or  B OFF  or  C ON'];
const RULES_ZH=['A开  或  B开  或  C关','A关  或  B开  或  C开','A开  或  B关  或  C开'];
export function rules(c,t,f,o={}){
 if(['first','all','test','test_result'].includes(o.mode))return rulePerformance(c,t,f,o);
 if(o.mode==='test')t-=o.operation_shift||0;
 const mode=o.mode||'first',fail=mode==='test'&&t>=4;heading(c,tr('The puzzle has rules','给开关加上规则'),tr(mode==='hypothesis'?'What ETH conjectures':mode==='first'?'At least one must hold':mode==='find'?'Checking and finding differ':'Every rule must pass',mode==='hypothesis'?'指数时间假说猜想什么':mode==='first'?'至少一项成立':mode==='find'?'检查，与寻找':'每条规则都必须通过'),{size:64});
 if(mode==='hypothesis'){circle(c,500,540,230,P.white);label(c,'ETH',500,554,104,{kind:'slab',align:'center'});label(c,tr('Worst case','最坏情况'),500,633,40,{align:'center'});lines(c,tr('Some fixed exponential growth remains unavoidable.','某个固定的指数增长下界仍不可避免。'),1010,410,720,52,{kind:'slab'});tag(c,tr('A conjecture about growth','关于增长的猜想'),1330,815,{w:770});return;}
 if(mode==='find'){for(let i=0;i<2;i++){const x=530+i*860;circle(c,x,510,225,i?P.blue:P.mustardL);if(i){for(let j=0;j<8;j++){circle(c,x-100+(j%4)*66,465+Math.floor(j/4)*100,18,j===5?P.coral:P.white,{line:2});}label(c,'?',x,690,68,{kind:'slab',align:'center'});}else{switchProp(c,x,500,{s:.55,on:true,labelText:''});check(c,x+130,640,{s:1.1});}label(c,tr(i?'Find a working setting':'Check this setting',i?'找到可行组合':'检查已知组合'),x,825,38,{align:'center'});}return;}
 const all=mode!=='first';for(let i=0;i<3;i++)switchProp(c,315+i*260,540,{s:.72,on:mode==='test'?(i===0?t<2.9:i===1?t<4:true):true,position:mode==='test'?(i===0?1-ss(seg(t,2.5,2.9)):i===1?1-ss(seg(t,3.6,4)):1):1,labelText:String.fromCharCode(65+i)});
 const n=all?(o.progressive?Math.min(3,1+Math.floor(t/1.7)):3):1;for(let i=0;i<n;i++){box(c,1085,315+i*162,705,125,i===0&&fail?P.pink:P.white,{line:3});label(c,tr(RULES_EN[i],RULES_ZH[i]),1115,390+i*162,32,{max:600});if((mode==='test'&&t>1)||mode==='first'&&t>1.5)check(c,1740,380+i*162,{yes:!fail||i!==0,s:.55});}
 if(mode==='test'&&t>1.8&&t<5){let x=315,y;if(t<2.9){x=lerp(-220,315,ss(seg(t,1.8,2.5)));y=501.84+76.32*ss(seg(t,2.5,2.9));}else if(t<3.6){x=lerp(315,575,ss(seg(t,3.05,3.5)));y=578.16-80*Math.sin(Math.PI*seg(t,2.9,3.6))-76.32*ss(seg(t,3.1,3.6));}else{x=575-1300*ss(seg(t,4.25,5));y=501.84+76.32*ss(seg(t,3.6,4))-50*ss(seg(t,4.25,5));}closeHand(c,[x,y],{from:[-400,540]});}
 tag(c,tr(all?'OR within a card · AND between cards':'At least one, not exactly one',all?'卡内是“或” · 卡间是“且”':'至少一项，不是恰好一项'),960,871,{w:1320,size:34});
}
export const lessonScenes={filing,branches,rules};
