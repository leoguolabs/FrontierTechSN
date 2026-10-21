import {W,H,BOARD} from './engine.mjs'

// Integrate a half-frame exposure. Sample spacing is measured in output pixels,
// including translation, zoom, roll and the renderer's raised-object parallax.
export const EXPOSURE = {shutterFrames:.5,maximumSampleGap:.75,maximumSamples:256}

function projected(point,cam,depth){
  const x=(point[0]-cam.x+(cam.x-BOARD.w/2)*depth*.0006)*cam.z
  const y=(point[1]-cam.y+(cam.y-BOARD.h/2)*depth*.0006)*cam.z
  const a=cam.roll*Math.PI/180,c=Math.cos(a),s=Math.sin(a)
  return [W/2+c*x-s*y,H*.47+s*x+c*y]
}

function visiblePoints(cam,depth){
  const a=-cam.roll*Math.PI/180,c=Math.cos(a),s=Math.sin(a),points=[]
  for(const x of [0,W/2,W])for(const y of [0,H*.47,H]){
    const dx=x-W/2,dy=y-H*.47
    points.push([
      (c*dx-s*dy)/cam.z+cam.x-(cam.x-BOARD.w/2)*depth*.0006,
      (s*dx+c*dy)/cam.z+cam.y-(cam.y-BOARD.h/2)*depth*.0006
    ])
  }
  return points
}

export function exposurePlan(film,frame){
  const center=film.camera(frame),half=EXPOSURE.shutterFrames/2
  const first=Math.max(0,frame-half),last=Math.min(film.duration_frames-1,frame+half)
  const probes=[0,26].flatMap(depth=>visiblePoints(center,depth).map(point=>({point,depth})))
  const a=film.camera(first),b=film.camera(last)
  const travel=Math.max(...probes.map(({point,depth})=>{
    const p=projected(point,a,depth),q=projected(point,b,depth)
    return Math.hypot(q[0]-p[0],q[1]-p[1])
  }))
  let count=travel<=EXPOSURE.maximumSampleGap?1:2**Math.ceil(Math.log2(travel/EXPOSURE.maximumSampleGap))
  while(count<=EXPOSURE.maximumSamples){
    // Midpoint quadrature. The first and last frames use the available half-window.
    const times=Array.from({length:count},(_,i)=>first+(i+.5)/count*(last-first))
    if(count===1)times[0]=frame
    let maximumGap=0
    for(let i=1;i<times.length;i++){
      const previous=film.camera(times[i-1]),current=film.camera(times[i])
      for(const {point,depth} of probes){
        const p=projected(point,previous,depth),q=projected(point,current,depth)
        maximumGap=Math.max(maximumGap,Math.hypot(q[0]-p[0],q[1]-p[1]))
      }
    }
    if(maximumGap<=EXPOSURE.maximumSampleGap)
      return {count,times,travel,maximumGap,window:[first,last]}
    // Accelerating and curved moves can exceed the endpoint estimate.
    count*=2
  }
  throw Error(`Exposure needs more than ${EXPOSURE.maximumSamples} samples at frame ${frame}`)
}

export class ExposureRenderer{
  constructor(renderer,createCanvas){
    this.renderer=renderer
    this.createCanvas=createCanvas
    this.sample=createCanvas(W,H)
    this.sampleContext=this.sample.getContext('2d')
    this.levels=[]
  }
  render(ctx,film,frame,{subtitles=true}={}){
    const plan=exposurePlan(film,frame)
    if(plan.count===1){
      this.renderer.render(ctx,film,frame,{subtitles})
      return plan
    }
    // Balanced pairwise averaging avoids the rounding drift of repeatedly
    // compositing with increasingly tiny alpha values into an 8-bit canvas.
    const occupied=[]
    for(const time of plan.times){
      this.renderer.render(this.sampleContext,film,time,{subtitles:false})
      let current=this.sample,level=0
      while(true){
        if(!this.levels[level]){
          const canvas=this.createCanvas(W,H)
          this.levels[level]={canvas,context:canvas.getContext('2d')}
        }
        const buffer=this.levels[level],target=buffer.context
        target.globalAlpha=occupied[level] ? .5 : 1
        target.drawImage(current,0,0)
        target.globalAlpha=1
        if(!occupied[level]){occupied[level]=true;break}
        occupied[level]=false
        current=buffer.canvas
        level++
      }
    }
    ctx.drawImage(this.levels[Math.log2(plan.count)].canvas,0,0)
    if(subtitles)this.renderer.subtitle(ctx,film,frame)
    return plan
  }
}
