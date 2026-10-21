import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {createCanvas} from '@napi-rs/canvas'
import {exposurePlan,ExposureRenderer,EXPOSURE} from '../src/exposure.mjs'
import {makeFilm} from '../src/film.mjs'

const staticFilm={duration_frames:100,camera:()=>({x:3200,y:1800,z:1,roll:0})}
assert.deepEqual(exposurePlan(staticFilm,40).times,[40])

const fastFilm={...staticFilm,camera:f=>({x:3200+60*f,y:1800,z:1,roll:0})}
const fast=exposurePlan(fastFilm,40)
assert.ok(fast.count>3,'A fast pan must not fall back to three ghosted outlines')
assert.ok(fast.maximumGap<=EXPOSURE.maximumSampleGap)
assert.deepEqual(fast.window,[39.75,40.25],'180 degrees at 24 fps spans half a frame')
assert.ok(Math.abs(fast.times.reduce((a,b)=>a+b,0)/fast.count-40)<1e-9)
assert.ok(fast.times.every(t=>t>39.75&&t<40.25))
assert.ok(exposurePlan(fastFilm,0).times.every(t=>t>=0))
assert.ok(exposurePlan(fastFilm,99).times.every(t=>t<=99))

// A constant-velocity exposure of a linear brightness ramp should retain its
// midpoint brightness. Subtitles must be drawn once, after all scene samples.
const calls=[],fake={
  render(ctx,film,f,options){
    calls.push({f,options})
    const v=Math.round(120+(f-40)*100)
    ctx.fillStyle=`rgb(${v},${v},${v})`;ctx.fillRect(0,0,1920,1080)
  },
  subtitle(ctx){
    calls.push({subtitle:true})
    ctx.fillStyle='#ff0000';ctx.fillRect(0,0,10,10)
  }
}
const out=createCanvas(1920,1080),ctx=out.getContext('2d')
new ExposureRenderer(fake,createCanvas).render(ctx,fastFilm,40)
assert.equal(calls.filter(c=>c.subtitle).length,1)
assert.ok(calls.slice(0,-1).every(c=>c.options.subtitles===false))
const center=ctx.getImageData(100,100,1,1).data
assert.ok(Math.abs(center[0]-120)<=2,`Exposure changed midpoint brightness: ${center[0]}`)
assert.deepEqual([...ctx.getImageData(1,1,1,1).data],[255,0,0,255])

const read=async p=>JSON.parse(await readFile(new URL(`../${p}`,import.meta.url),'utf8'))
const film=makeFilm(await read('content/narration.json'),await read('media/audio/manifest.json'),await read('media/asr/observations.json'))
const close=film.shots.at(-1).end
const a=film.camera(close-.00001),b=film.camera(close+.00001)
assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<.001,'Closing breath attenuation must not jump')
const plans=Array.from({length:film.duration_frames},(_,f)=>exposurePlan(film,f))
assert.ok(plans.every(p=>p.maximumGap<=EXPOSURE.maximumSampleGap))
console.log(JSON.stringify({passed:true,frames:plans.length,
  maximumSampleGap:Math.max(...plans.map(p=>p.maximumGap)),
  checks:['stationary sharpness','fast pan sampling','half-frame window','edge clamping',
    'balanced exposure brightness','sharp overlay ordering','closing camera continuity','complete camera path']}))
