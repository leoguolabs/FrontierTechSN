import fs from 'node:fs';
import path from 'node:path';
import {once} from 'node:events';
import {createCanvas} from '@napi-rs/canvas';
import {begin,finish,fonts,P,caption,heading,researcher,box,lines} from '../src/rebuild/stage.mjs';
import {setGooShot} from '../src/rebuild/goo.mjs';
import {identity} from '../src/rebuild/identity.mjs';
import {topicScenes} from '../src/topic.mjs';
import {paintEvidence} from '../src/evidence.mjs';

const root=path.resolve(import.meta.dirname,'..');
const [widthArg,stillPath,frameArg,studyPath]=process.argv.slice(2);
const width=Number(widthArg||960), plan=JSON.parse(fs.readFileSync(path.resolve(root,studyPath??'content/timeline.json')));
const canvas=createCanvas(width,width*9/16), c=canvas.getContext('2d');
fonts(root);
async function draw(frame){
  const shot=plan.shots.find(s=>frame>=s.start && frame<s.end);
  if(!shot) throw Error('Frame outside timeline '+frame);
  if(shot.scene==='evidence'){
    const subtitle=plan.captions.find(q=>q.start<=frame&&frame<q.end);
    await paintEvidence(c,{...shot.evidence,start:shot.start,end:shot.end},frame,plan.language,root,subtitle?.text??'');
    return;
  }
  const bodyFrame=Math.max(shot.start,2*Math.floor(frame/2));
  begin(c,bodyFrame,plan.language,P[shot.ground]??P.paper,{burst:shot.ground==='mustard',floor:shot.scene==='host'});
  setGooShot({...shot,id:shot.paragraph,options:shot.options??{},scene:shot.beat??shot.scene});
  if(shot.scene==='host'){
    heading(c,shot.kicker,shot.title);
    researcher(c,460,817,{s:1.04,frame:bodyFrame,face:shot.face??'think',acting:shot.acting});
    box(c,800,322,880,340,P.white,{radius:15});
    lines(c,shot.label,1240,527,790,51,{kind:'slab',align:'center'});
  } else if(shot.scene==='brand'){
    identity(c,(bodyFrame-shot.start)/24,bodyFrame,{ending:!!shot.ending});
  } else {
    const paint=topicScenes[shot.scene];
    if(!paint) throw Error('Author scene in src/topic.mjs: '+shot.scene);
    heading(c,shot.kicker,shot.title);
    paint(c,shot,frame,plan.language);
  }
  finish(c);
  c.resetTransform();c.scale(width/1920,width/1920);
  const subtitle=plan.captions.find(q=>q.start<=frame&&frame<q.end);
  caption(c,subtitle?.text??'');
}
if(stillPath){
  await draw(Number(frameArg??0));fs.writeFileSync(stillPath,canvas.toBuffer('image/png'));
}else{
  for(let frame=0;frame<plan.duration_frames;frame++){
    await draw(frame);
    if(!process.stdout.write(canvas.data())) await once(process.stdout,'drain');
  }
}
