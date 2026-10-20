import {BoardRenderer} from './engine.mjs'
import {makeFilm} from './film.mjs'

const $=s=>document.querySelector(s)
const fetchJSON=async(url,fallback=null)=>{try{const r=await fetch(url);if(!r.ok)return fallback;return await r.json()}catch{return fallback}}
const [narration,audio,asr,timeline]=await Promise.all([
  fetchJSON('content/narration.json',[]),fetchJSON('media/audio/manifest.json',[]),
  fetchJSON('media/asr/observations.json',[]),fetchJSON('content/timeline.json')
])
const film=makeFilm(narration,audio,asr)
const frames=timeline?.duration_frames||film.duration_frames
const video=$('#film-video'),reference=$('#reference-video'),comparison=$('#compare-video')
const pretty=t=>`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`
$('#film-meta').textContent=`${pretty(frames/24)} · 1920 × 1080 · 24 FPS`
video.addEventListener('error',()=>{$('#video-message').hidden=false})
video.querySelector('source').addEventListener('error',()=>{$('#video-message').hidden=false})
video.addEventListener('loadedmetadata',()=>{$('#video-message').hidden=true})
const chapterNames={hook:'The question',measures:'Four different tests',practice:'Turkey: practice',exam:'The independent test',tutor:'A different tutor',physics:'Design matters',attempt:'Try it yourself',closing:'What remains'}
for(const shot of film.shots.filter(s=>chapterNames[s.region])){
  const b=document.createElement('button');b.className='chapter'
  const time=document.createElement('small');time.textContent=pretty(shot.start/24)
  b.append(time,chapterNames[shot.region]);b.onclick=()=>{video.currentTime=shot.start/24;video.play().catch(()=>{})}
  b.dataset.start=shot.start/24;$('#chapters').append(b)
}
video.addEventListener('timeupdate',()=>{
  let active=null
  for(const b of $('#chapters').children){b.classList.remove('active');if(+b.dataset.start<=video.currentTime)active=b}
  active?.classList.add('active')
})
const pairs={
  opening:{ref:40,region:'hook',offset:3,note:'A close detail establishes the physical world before the camera opens up.'},
  measurement:{ref:390,region:'practice',offset:11,note:'Blue measures; red judges. Objects and annotations share one board.'},
  judgment:{ref:420,region:'exam',offset:7,note:'Hold the evidence long enough to read it. Let the verdict arrive last.'},
  reveal:{ref:925,region:'closing',offset:null,note:'The complete board appears once, after the argument has been built.'}
}
const players={reference,compare:comparison}
const maxFrames={reference:959,compare:frames-1}
$('#compare-frame').max=frames-1
function seek(which,frame){
  const f=Math.max(0,Math.min(maxFrames[which],Math.round(frame)))
  players[which].pause();players[which].currentTime=f/24+.001
  $(`#${which}-frame`).value=f;$(`#${which}-label`).textContent=`${f} / ${maxFrames[which]}`
}
function pair(){
  const p=pairs[$('#moment').value],shot=film.shots.find(s=>s.region===p.region)
  seek('reference',p.ref);seek('compare',p.offset===null?frames-20:shot.start+p.offset*24)
  $('#comparison-note').textContent=p.note;$('#pair-play').textContent='Play both'
}
$('#moment').value='measurement';$('#moment').onchange=pair
for(const which of Object.keys(players)){
  $(`#${which}-frame`).oninput=e=>seek(which,+e.target.value)
  players[which].addEventListener('loadedmetadata',pair,{once:true})
  players[which].addEventListener('timeupdate',()=>{
    const f=Math.min(maxFrames[which],Math.floor(players[which].currentTime*24))
    $(`#${which}-frame`).value=f;$(`#${which}-label`).textContent=`${f} / ${maxFrames[which]}`
  })
}
document.querySelectorAll('[data-step]').forEach(b=>b.onclick=()=>{
  const [which,amount]=b.dataset.step.split(':');seek(which,+$(`#${which}-frame`).value+(+amount))
})
$('#pair-play').onclick=()=>{
  if(reference.paused&&comparison.paused){reference.play().catch(()=>{});comparison.play().catch(()=>{});$('#pair-play').textContent='Pause both'}
  else{reference.pause();comparison.pause();$('#pair-play').textContent='Play both'}
}
let sheet=0,atlasAnalysis=null
async function atlas(reset=false){
  const name=$('#atlas-film').value
  if(reset)sheet=0
  atlasAnalysis=await fetchJSON(name==='paired'?'review/comparison.json':`review/${name}-analysis.json`)
  if(!atlasAnalysis){$('#atlas-status').textContent='The full frame atlas has not been generated yet.';$('#atlas-image').removeAttribute('src');return}
  const total=atlasAnalysis.decoded_frames??atlasAnalysis.final_frames_compared??(name==='reference'?960:frames)
  const count=Math.ceil(total/20);sheet=Math.min(Math.max(sheet,0),count-1)
  const first=sheet*20,last=Math.min(total-1,first+19)
  $('#atlas-image').src=`review/atlases/${name}/${String(first).padStart(5,'0')}-${String(last).padStart(5,'0')}.jpg`
  $('#atlas-count').textContent=`${sheet+1} / ${count}`
  $('#atlas-prev').disabled=sheet===0;$('#atlas-next').disabled=sheet===count-1
  $('#atlas-status').textContent=`Frames ${first}–${last}. ${name==='paired'?'Each pair shows the function-matched reference on the left and the independent film on the right. ':''}Atlas thumbnails are 384 × 216; use the video frame controls for full-resolution inspection.`
}
$('.atlas').addEventListener('toggle',()=>{if($('.atlas').open)atlas()})
$('#atlas-film').onchange=()=>atlas(true);$('#atlas-prev').onclick=()=>{sheet--;atlas()};$('#atlas-next').onclick=()=>{sheet++;atlas()}
let renderer=null,initializing=false
const canvas=$('#live-canvas'),ctx=canvas.getContext('2d')
$('#live-frame').max=film.duration_frames-1
async function initLive(){
  if(renderer||initializing)return
  initializing=true;$('#live-status').textContent='Loading local fonts, photograph, and board material…'
  try{
    const marker=new FontFace('Marker','url(assets/fonts/Kalam-Regular.ttf)')
    const sans=new FontFace('Sans','url(assets/fonts/Archivo.ttf)')
    await Promise.all([marker.load(),sans.load()]);document.fonts.add(marker);document.fonts.add(sans)
    const im=new Image();im.src='assets/photos/notebook-cutout-v1.png';await im.decode()
    renderer=new BoardRenderer({createCanvas:(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c},images:{notebookCutout:im}})
    drawLive();$('#live-status').textContent='Live composition preview. The exported video adds sub-frame camera motion blur.'
  }catch(e){$('#live-status').textContent=`Preview could not load: ${e.message}`}
  initializing=false
}
function drawLive(){const f=+$('#live-frame').value;$('#live-label').textContent=f;if(renderer)renderer.render(ctx,film,f)}
$('.live-detail').addEventListener('toggle',()=>{if($('.live-detail').open)initLive()})
$('#live-frame').oninput=drawLive
$('#save-frame').onclick=()=>{if(!renderer)return;const a=document.createElement('a');a.download=`briefing-frame-${$('#live-frame').value}.png`;a.href=canvas.toDataURL('image/png');a.click()}
pair()
