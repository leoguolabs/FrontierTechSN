import {createCanvas,GlobalFonts,loadImage} from '@napi-rs/canvas'
import {readFile,writeFile,mkdir} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {once} from 'node:events'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {BoardRenderer} from '../src/engine.mjs'
import {makeFilm} from '../src/film.mjs'
import {ExposureRenderer,exposurePlan,EXPOSURE} from '../src/exposure.mjs'

process.chdir(path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'))
const read=async p=>JSON.parse(await readFile(p,'utf8'))
const film=makeFilm(await read('content/narration.json'),await read('media/audio/manifest.json'),await read('media/asr/observations.json'))
const histogram={},plans=[]
for(let frame=0;frame<film.duration_frames;frame++){
  const p=exposurePlan(film,frame)
  histogram[p.count]=(histogram[p.count]||0)+1
  plans.push({frame,count:p.count,travel:p.travel,maximumGap:p.maximumGap})
}
await mkdir('review/previews/exposure-v2',{recursive:true})
GlobalFonts.registerFromPath('assets/fonts/Kalam-Regular.ttf','Marker')
GlobalFonts.registerFromPath('assets/fonts/Archivo.ttf','Sans')
const images={notebookCutout:await loadImage('assets/photos/notebook-cutout-v1.png')}
const renderer=new BoardRenderer({createCanvas,images}),exposure=new ExposureRenderer(renderer,createCanvas)
const canvas=createCanvas(1920,1080),ctx=canvas.getContext('2d')
const started=performance.now()
const selected=[26,432,633,770,1445,2443,2664,3758,3865]
for(const frame of selected){
  exposure.render(ctx,film,frame)
  await writeFile(`review/previews/exposure-v2/frame-${frame}.png`,canvas.toBuffer('image/png'))
}
// Two actual transitions, encoded for motion review; no changes to the accepted film.
const clips=[]
for(const [start,end] of [[615,665],[2420,2480]]){
  const output=`review/previews/exposure-v2/transition-${start}-${end-1}.mp4`
  const encoder=spawn('ffmpeg',['-y','-v','warning','-f','image2pipe','-vcodec','mjpeg',
    '-framerate','24','-i','-','-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
    '-an','-c:v','libx264','-preset','fast','-crf','17','-movflags','+faststart',output],{stdio:['pipe','inherit','inherit']})
  for(let frame=start;frame<end;frame++){
    exposure.render(ctx,film,frame)
    if(!encoder.stdin.write(canvas.toBuffer('image/jpeg',95)))await once(encoder.stdin,'drain')
  }
  encoder.stdin.end()
  const [code]=await once(encoder,'exit')
  if(code)throw Error(`Exposure clip encoding failed: ${code}`)
  clips.push({file:output,first:start,last:end-1})
  console.log(`Rendered ${output}`)
}
const report={status:'candidate_rendered_not_visually_accepted',settings:EXPOSURE,
  frames_analyzed:plans.length,sample_histogram:histogram,
  maximum_adjacent_sample_gap_pixels:Math.max(...plans.map(p=>p.maximumGap)),
  total_scene_samples:plans.reduce((n,p)=>n+p.count,0),
  selected_frames:selected,clips,elapsed_seconds:(performance.now()-started)/1000,
  scope:'Measures projected sample spacing across the actual camera path; motion clips still require visual inspection.'}
await writeFile('review/exposure-study.json',JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify(report,null,2))
