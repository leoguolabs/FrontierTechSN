import {P,tr,researcher,box,circle,label,lines} from './stage.mjs';
import {ink,ss,seg,lerp} from './toon.mjs';
import {gooPointTip} from './goo.mjs';
// Language-specific brand card, with the same live rig used in the story.
// The button contact is the declared endpoint of the pointing fingertip.
export function identity(c,t,f,{ending=false}={}){
 c.fillStyle='#F6EEDC';c.fillRect(0,0,1920,1080);
 const action=ss(seg(t,.18,.65)),release=ss(seg(t,1.04,1.32));
 const wrist=[lerp(154,235,action)-22*release,lerp(-330,-250,action)-56*release];
 const tip=gooPointTip([235,-250]),bx=430+tip[0]*1.04,by=811+tip[1]*1.04;
 box(c,bx-65,by-66,156,184,P.blue,{line:4,radius:24});
 circle(c,bx,by,42,P.coral,{line:4});
 researcher(c,430,811,{s:1.04,frame:f,target:wrist,hand:'press',acting:'prop',face:t>.7?(t>1.6?'happy':'surprise'):'think'});
 if(t>.67){const k=ss(seg(t,.67,.85));for(let i=0;i<3;i++){const a=-1.8+i*.55;ink(c,[[bx+Math.cos(a)*70,by+25+Math.sin(a)*70],[bx+Math.cos(a)*(70+38*k),by+25+Math.sin(a)*(70+38*k)]],5,{color:P.mustard});}}
 label(c,tr('Goo','咕仔'),1250,318,71,{kind:'slab',align:'center'});
 if(tr(true,false)){
  label(c,'Ooh,',1250,443,112,{kind:'slab',align:'center'});
  label(c,'Lemme See!',1250,568,112,{kind:'slab',align:'center',max:990});
 }else{
  label(c,'让我捅咕捅咕',1250,499,105,{kind:'slab',align:'center',max:1100});
 }
 ink(c,[[1030,624],[1470,624]],5,{color:P.coral});
 label(c,ending?tr('See you next time.','下期接着聊。'):tr('A little curiosity goes a long way.','好奇一点，再多问一句。'),1250,714,38,{align:'center',max:1120});
}
