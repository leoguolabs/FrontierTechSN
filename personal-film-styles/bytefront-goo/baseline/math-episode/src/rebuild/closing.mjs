import {identity} from './identity.mjs';
// Production-specific return to the student's desk. Questions are not certifications.
import {P,tr,at,box,circle,label,heading,sheet,desk,pencil,researcher} from './stage.mjs';
import {ink,ss,seg,lerp,text} from './toon.mjs';
const cue=(f,a,n=18)=>ss(seg(f,a,a+n));
const fade=(c,a,draw)=>{if(a<=0)return;c.save();c.globalAlpha*=a;draw();c.restore();};
export function closing(c,t,f,o){
 const arrival=cue(f,o.arrival_frame,20),checking=cue(f,o.check_frame,16),why=cue(f,o.why_frame,12),question=cue(f,o.question_frame,18);
 const turn=seg(f,o.brand_frame,o.brand_frame+32);
 heading(c,tr('Back at the research desk','回到研究桌前'),tr('Answers lead to new questions.','有了答案，继续追问。'),{size:68});
 circle(c,1190,525,310,P.white,{line:3});
 desk(c,735,760,980);
 // Closed notebook establishes a complete desk before the new manuscript arrives.
 box(c,1410,716,240,36,P.tealD,{line:3});box(c,1422,704,240,31,P.teal,{line:3});
 pencil(c,1460,699,{s:.8,angle:-.08});
 box(c,965,365,410,382,P.tealD,{line:4,radius:10});
 box(c,982,365,410,382,P.teal,{line:3,radius:8});
 ink(c,[[1010,382],[1010,727]],3,{color:P.tealD});
 label(c,tr('RESEARCH','研究手记'),1190,448,42,{kind:'slab',align:'center',fill:P.white,max:375});
 label(c,tr('What should I try next?','下一步，研究什么？'),1190,560,30,{align:'center',fill:P.white,max:375});
 ink(c,[[1080,638],[1300,638]],3,{color:P.white});
 const pose=cue(f,o.check_frame-14,20);
 researcher(c,480,815,{s:.95,frame:f,face:question>.5?'calm':'think',hand:'open',target:[lerp(70,170,pose),lerp(-415,-330,pose)]});
 // The entering sheet is a theatrical reveal; no physical hand contact is claimed.
 if(arrival>0)at(c,lerp(2250,1170,arrival),560,1,()=>{
  sheet(c,0,0,{title:tr('A CLAIM TO CHECK','待检查的主张'),blank:true,accent:P.blue,w:570,h:380});
  label(c,tr('For every real x','对每一个实数 x'),0,-28,36,{align:'center'});
  label(c,'x² ≥ 0',0,76,85,{kind:'slab',align:'center'});
  if(checking>0)ink(c,[[-185,-17],[-185+370*checking,-17]],5,{color:P.coralD});
  fade(c,why*(1-ss(seg(question,0,.4))),()=>label(c,tr('Why does it follow?','为什么成立？'),0,152,36,{kind:'script',align:'center'}));
  fade(c,ss(seg(question,.6,1)),()=>label(c,tr('What if conditions change?','如果改变条件呢？'),0,152,36,{kind:'script',align:'center'}));
 });
 label(c,tr('Check. Understand. Ask again.','检查，理解，再提问。'),1120,871,38,{align:'center'});
 // Close around the desk, then open the printed end card. Captions remain on their own track.
 if(turn>0){
  c.save();c.beginPath();c.rect(0,0,1920,1080);
  const r=1600*(1-ss(seg(turn,0,.5)));
  if(r>0)c.arc(1190,545,r,0,Math.PI*2,true);
  c.clip('evenodd');c.fillStyle=P.ink;c.fillRect(0,0,1920,1080);c.restore();
  if(turn>.5){const open=ss(seg(turn,.5,1));c.save();c.beginPath();c.arc(960,515,1300*open,0,Math.PI*2);c.clip();identity(c,(f-o.brand_frame)/24-.65,f,{ending:true});c.restore();}

 }
}
function langSize(){return tr(54,43);}
