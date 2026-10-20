import {createCanvas,GlobalFonts} from '@napi-rs/canvas'
import {readFile,writeFile} from 'node:fs/promises'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {makeFilm} from '../src/film.mjs'
process.chdir(path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'))
const read=async p=>JSON.parse(await readFile(p,'utf8'))
const narration=await read('content/narration.json'),audio=await read('media/audio/manifest.json')
let asr=[];try{asr=await read('media/asr/observations.json')}catch{}
const f=makeFilm(narration,audio,asr),errors=[]
GlobalFonts.registerFromPath('assets/fonts/Archivo.ttf','Sans')
const ctx=createCanvas(1920,1080).getContext('2d')
const labels=[]
for(const e of f.elements.filter(e=>e.type==='paper'&&e.lines?.length)){
  for(const [i,value] of e.lines.entries()){
    const l=typeof value==='string'?{text:value}:value
    ctx.font=`${l.weight||e.weight||600} ${l.size||e.size||48}px Sans`
    const metrics=ctx.measureText(l.text),width=metrics.width,available=e.w-(e.pad||34)-18
    const bottom=(e.tag?e.h*.69:(e.pad||34)+(i+1)*(e.leading||65)-15)+metrics.actualBoundingBoxDescent
    labels.push({id:e.id,text:l.text,width,available,bottom,height:e.h})
    if(width>available)errors.push(`Label overflow: ${e.id} "${l.text}" ${width.toFixed(1)} > ${available}`)
    if(bottom>e.h)errors.push(`Label baseline overflow: ${e.id} "${l.text}"`)
  }
}
ctx.font='500 37px Sans'
for(const cue of f.subtitles){
  if(cue.start<0||cue.end<=cue.start||cue.end>f.duration_frames)errors.push(`Invalid caption timing: ${cue.text}`)
  if(ctx.measureText(cue.text).width>1550)errors.push(`Caption overflow: ${cue.text}`)
}
for(const s of f.shots){
  if(!Number.isInteger(s.start)||!Number.isInteger(s.end))errors.push(`Non-integer shot: ${s.id}`)
  if(s.voiceEnd>s.end-6)errors.push(`Speech exceeds visual hold: ${s.id}`)
  const cues=f.subtitles.filter(c=>c.shotId===s.id)
  if(cues.length&&cues.map(c=>c.text).join(' ')!==s.text)
    errors.push(`Caption text or punctuation differs from authored narration: ${s.id}`)
}
for(let frame=0;frame<f.duration_frames;frame++){
  const c=f.camera(frame)
  if(!Object.values(c).every(Number.isFinite)||c.z<=0)errors.push(`Invalid camera at ${frame}`)
}
if(f.elements.filter(e=>e.type==='person').length<10)errors.push('Expected meaningful people drawings.')
if(!f.elements.some(e=>e.type==='flag'))errors.push('Missing Turkish flag.')
const report={frames:f.duration_frames,fps:f.fps,labels:labels.length,people:f.elements.filter(e=>e.type==='person').length,
  audio_complete:audio.length===narration.length,transcription_complete:asr.length===narration.length,
  errors,label_measurements:labels,scope:'Geometry and timeline checks; not visual acceptance.'}
await writeFile('review/structural-validation.json',JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify({...report,label_measurements:undefined},null,2))
if(errors.length)process.exitCode=1
