import {createCanvas,GlobalFonts} from '@napi-rs/canvas'
import {readFile,writeFile} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {once} from 'node:events'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {BoardRenderer} from '../src/engine.mjs'
import {makeFilm} from '../src/film.mjs'
process.chdir(path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'))
const read=async p=>JSON.parse(await readFile(p,'utf8'))
const narration=await read('content/narration.json')
const audio=await read('media/audio/manifest.json'),asr=await read('media/asr/observations.json')
if(audio.length!==narration.length||asr.length!==narration.length)throw Error('All voice and transcription records are required.')
for(const a of audio){
  const o=asr.find(s=>s.id===a.id)
  if(!o||o.audio_sha256!==a.audio_sha256)throw Error(`Missing or stale speech review: ${a.id}`)
  if(o.differences.length)throw Error(`Unresolved transcription difference: ${a.id}`)
}
const film=makeFilm(narration,audio,asr),picture=await read('media/picture-timeline.json')
// A late voice arrival may not silently retime an already rendered picture.
const geometry=f=>JSON.stringify({frames:f.duration_frames,keys:f.keys,elements:f.elements,events:f.events,
  shots:f.shots.map(s=>({id:s.id,start:s.start,end:s.end}))})
if(geometry(film)!==geometry(picture))throw Error('Actual audio changed picture timing. Re-render the picture before mixing.')
const record=await read('review/render.json')
if(!record.pictureOnly)throw Error('Render with --picture-only before overlaying captions.')
await writeFile('content/timeline.json',JSON.stringify(film,(k,v)=>typeof v==='function'?undefined:v,2)+'\n')
const clock=(f,separator='.')=>{
  const ms=Math.round(f/24*1000),s=Math.floor(ms/1000)
  return `${String(Math.floor(s/3600)).padStart(2,'0')}:${String(Math.floor(s/60)%60).padStart(2,'0')}:${String(s%60).padStart(2,'0')}${separator}${String(ms%1000).padStart(3,'0')}`
}
await writeFile('media/captions.vtt','WEBVTT\n\n'+film.subtitles.map((c,i)=>`${i+1}\n${clock(c.start)} --> ${clock(c.end)}\n${c.text}`).join('\n\n')+'\n')
await writeFile('media/captions.srt',film.subtitles.map((c,i)=>`${i+1}\n${clock(c.start,',')} --> ${clock(c.end,',')}\n${c.text}`).join('\n\n')+'\n')
GlobalFonts.registerFromPath('assets/fonts/Archivo.ttf','Sans')
const canvas=createCanvas(1920,1080),ctx=canvas.getContext('2d')
const cache=new Map(),subtitle=BoardRenderer.prototype.subtitle
function bytesAt(f){
  const cue=film.subtitles.find(c=>f>=c.start&&f<c.end),key=cue?.start??-1
  if(!cache.has(key)){
    ctx.clearRect(0,0,1920,1080)
    subtitle.call({width:1920,height:1080},ctx,film,f)
    cache.set(key,canvas.toBuffer('image/png'))
  }
  return cache.get(key)
}
const ff=spawn('ffmpeg',['-y','-v','warning','-framerate','24','-f','image2pipe','-vcodec','png','-i','-',
  '-an','-c:v','qtrle','-pix_fmt','argb','media/captions-alpha.mov'],{stdio:['pipe','inherit','inherit']})
for(let f=0;f<film.duration_frames;f++){
  if(!ff.stdin.write(bytesAt(f)))await once(ff.stdin,'drain')
}
ff.stdin.end();const [code]=await once(ff,'exit')
if(code)throw Error(`Caption encoding failed: ${code}`)
console.log(`${film.subtitles.length} cues aligned to verified speech; ${film.duration_frames} alpha frames.`)
