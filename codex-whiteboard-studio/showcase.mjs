import {comparisonBeats,referenceFrame} from './src/comparison.mjs'
const $=id=>document.getElementById(id)
const main=$('film-player'),candidate=$('candidate-player'),reference=$('reference-player')
const slider=$('frame-slider'),number=$('frame-number'),select=$('beat-select')
const read=async path=>{const r=await fetch(path);if(!r.ok)throw new Error(`${path}: ${r.status}`);return r.json()}
const time=t=>`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`
let timeline,beats=[],playing=false,raf=0,activeBeat
function showFrame(frame,{seek=true}={}){
  if(!timeline)return
  frame=Math.max(0,Math.min(timeline.duration_frames-1,Math.round(frame)))
  const t=frame/24,{beat:b,frame:rf}=referenceFrame(frame,beats),rt=rf/24
  if(seek){candidate.currentTime=t+1/48;reference.currentTime=rt+1/48}
  slider.value=number.value=String(frame);select.value=b.id
  $('candidate-frame').textContent=`FRAME ${String(frame).padStart(4,'0')} / ${t.toFixed(3)} s`
  $('reference-frame').textContent=`FRAME ${String(rf).padStart(4,'0')} / ${rt.toFixed(3)} s`
  $('beat-note').textContent=b.note;activeBeat=b
}
function stop(){playing=false;candidate.pause();reference.pause();cancelAnimationFrame(raf);$('play-comparison').textContent='Play moment'}
function update(){
  if(!playing)return
  if(candidate.currentTime>=activeBeat.end-.04){stop();showFrame(Math.floor(activeBeat.end*24)-1);return}
  showFrame(Math.floor(candidate.currentTime*24),{seek:false})
  const actual=Math.floor(reference.currentTime*24)
  $('reference-frame').textContent=`FRAME ${String(actual).padStart(4,'0')} / ${(actual/24).toFixed(3)} s`
  raf=requestAnimationFrame(update)
}
slider.addEventListener('input',()=>{stop();showFrame(+slider.value)})
number.addEventListener('change',()=>{stop();showFrame(+number.value)})
number.addEventListener('keydown',event=>{
  if(event.key==='Enter'){event.preventDefault();stop();showFrame(+number.value)}
})
$('previous-frame').onclick=()=>{stop();showFrame(+slider.value-1)}
$('next-frame').onclick=()=>{stop();showFrame(+slider.value+1)}
select.onchange=()=>{stop();showFrame(Math.round(beats.find(b=>b.id===select.value).start*24))}
$('play-comparison').onclick=async()=>{
  if(!activeBeat)return
  if(playing){stop();return}
  if(candidate.currentTime>=activeBeat.end-.05)showFrame(Math.round(activeBeat.start*24))
  main.pause();playing=true;$('play-comparison').textContent='Pause'
  reference.playbackRate=(activeBeat.re-activeBeat.rs)/(activeBeat.end-activeBeat.start)
  try{await Promise.all([candidate.play(),reference.play()]);update()}catch(error){stop();$('beat-note').textContent=`Video is not ready: ${error.message}`}
}
main.addEventListener('play',stop)
candidate.addEventListener('ended',stop)
try{
  timeline=await read('media/timeline.json')
  $('film-duration').textContent=`${time(timeline.duration)} MIN`
  slider.max=number.max=timeline.duration_frames-1
  beats=comparisonBeats(timeline,await read('content/comparison.json'))
  select.replaceChildren(...beats.map(b=>Object.assign(document.createElement('option'),{value:b.id,textContent:b.label})))
  const chapterLabels=[['hook','The question'],['study','Two scoreboards'],['counter','Design matters'],['practice','A practical loop'],['closing','What remains']]
  for(const [id,label]of chapterLabels){
    const b=beats.find(b=>b.id===id),button=document.createElement('button'),stamp=document.createElement('small')
    stamp.textContent=time(b.start);button.append(stamp,document.createTextNode(label))
    button.onclick=()=>{main.currentTime=b.start;main.play();$('screen').scrollIntoView({behavior:'smooth'})}
    $('chapters').append(button)
  }
  candidate.addEventListener('loadedmetadata',()=>showFrame(0),{once:true})
  if(candidate.readyState>=1)showFrame(0)
}catch(error){$('beat-note').textContent='The frame lab becomes available after a local render.'}
try{
  const report=await read('review/delivery.json')
  $('candidate-count').textContent=Number(report.decoded_frames).toLocaleString()
  $('review-state').textContent=report.status_label||'Recorded'
}catch{}
try{
  const {claims}=await read('content/sources.json'),seen=new Set()
  for(const claim of claims){
    if(seen.has(claim.source))continue;seen.add(claim.source)
    const item=document.createElement('article');item.className='source'
    const id=document.createElement('b');id.textContent=claim.id
    const body=document.createElement('div'),link=document.createElement('a'),kind=document.createElement('p')
    link.href=claim.source;link.textContent=claim.claim+' ↗';kind.textContent=claim.type
    body.append(link,kind);item.append(id,body);$('source-list').append(item)
  }
}catch{}
