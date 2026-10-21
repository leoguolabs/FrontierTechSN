import {createCanvas,GlobalFonts,loadImage} from '@napi-rs/canvas'
import {readFile,writeFile,mkdir,access} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {once} from 'node:events'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {BoardRenderer} from '../src/engine.mjs'
import {makeFilm} from '../src/film.mjs'
import {ExposureRenderer,EXPOSURE} from '../src/exposure.mjs'

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')
process.chdir(root)
GlobalFonts.registerFromPath('assets/fonts/Kalam-Regular.ttf','Marker')
GlobalFonts.registerFromPath('assets/fonts/Archivo.ttf','Sans')
const narration=JSON.parse(await readFile('content/narration.json','utf8'))
let audio=[]
try {audio=JSON.parse(await readFile('media/audio/manifest.json','utf8'))} catch {}
let observations=[]
try {observations=JSON.parse(await readFile('media/asr/observations.json','utf8'))} catch {}
const film=makeFilm(narration,audio,observations)
const stills=process.argv.includes('--stills')
const pictureOnly=process.argv.includes('--picture-only')
if(!stills&&!pictureOnly&&audio.length!==narration.length)throw new Error('Complete voice manifest required for production render')
const images={}
for(const [name,file] of [['notebook','notebook.jpg'],['notebookCutout','notebook-cutout-v1.png']]){
  try {images[name]=await loadImage(`assets/photos/${file}`)} catch {throw new Error(`Missing required photograph: ${file}`)}
}
await mkdir('review/previews',{recursive:true})
await mkdir('media',{recursive:true})
await writeFile('content/timeline.json',JSON.stringify(film,(key,value)=>typeof value==='function'?undefined:value,2)+'\n')
const canvas=createCanvas(1920,1080)
const renderer=new BoardRenderer({createCanvas,images})
const exposure=new ExposureRenderer(renderer,createCanvas)
const ctx=canvas.getContext('2d')
if(stills){
  const frames=[0,26,...film.shots.map(s=>Math.min(s.end-30,s.start+Math.round((s.end-s.start)*.7))),film.duration_frames-1]
  for(const frame of frames){
    exposure.render(ctx,film,frame)
    await writeFile(`review/previews/frame-${String(frame).padStart(5,'0')}.jpg`,canvas.toBuffer('image/jpeg',95))
  }
  await writeFile('review/previews/index.json',JSON.stringify(frames))
  console.log(JSON.stringify({frames,duration:film.duration_frames/film.fps,voiceComplete:audio.length===narration.length}))
} else {
  const output=process.env.OUTPUT||'media/picture-v1.mp4'
  await writeFile('media/picture-timeline.json',JSON.stringify(film,(key,value)=>typeof value==='function'?undefined:value,2)+'\n')
  const ff=spawn('ffmpeg',['-y','-v','warning','-f','image2pipe','-vcodec','mjpeg','-framerate',String(film.fps),'-i','-',
    '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
    '-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p',
    '-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
    '-movflags','+faststart',output],{stdio:['pipe','inherit','inherit']})
  const start=performance.now()
  const sampleHistogram={}
  let maximumSampleGap=0,totalSceneSamples=0
  for(let f=0;f<film.duration_frames;f++){
    const plan=exposure.render(ctx,film,f,{subtitles:!pictureOnly})
    sampleHistogram[plan.count]=(sampleHistogram[plan.count]||0)+1
    maximumSampleGap=Math.max(maximumSampleGap,plan.maximumGap)
    totalSceneSamples+=plan.count
    const bytes=canvas.toBuffer('image/jpeg',95)
    if(!ff.stdin.write(bytes))await once(ff.stdin,'drain')
    if(f%120===0)console.log(`${f}/${film.duration_frames} frames; ${((performance.now()-start)/1000).toFixed(1)}s`)
  }
  ff.stdin.end();const [code]=await once(ff,'exit');if(code)throw new Error(`ffmpeg ${code}`)
  await writeFile(process.env.RENDER_REPORT||'review/render.json',JSON.stringify({output,frames:film.duration_frames,
    duration:film.duration_frames/film.fps,elapsedSeconds:(performance.now()-start)/1000,
    exposure:EXPOSURE,sampleHistogram,maximumSampleGap,totalSceneSamples,pictureOnly},null,2)+'\n')
}
