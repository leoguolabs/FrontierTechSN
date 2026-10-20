// Canvas-only, deterministic rendering. This module has no browser or service dependency.
export const W = 1920
export const H = 1080
export const BOARD = {w: 6400, h: 3600}
export const C = {paper:'#e4e0d6', ink:'#23272e', blue:'#1f4fc8', red:'#d33a21', grey:'#6c727b'}
export const clamp = x => Math.max(0, Math.min(1, x))
export const ease = x => { x=clamp(x); return x*x*x*(x*(x*6-15)+10) }
export const mix = (a,b,u) => a+(b-a)*u
export const rand = n => {const a=Math.sin(n*127.1+311.7)*43758.5453;return a-Math.floor(a)}

function rounded(ctx,x,y,w,h,r=8) {
  ctx.beginPath(); ctx.roundRect(x,y,w,h,r)
}
function segment(ctx,points,progress=1,color=C.ink,width=6,dash=[]) {
  if(progress<=0) return
  let length=0
  const lengths=points.slice(1).map((p,i)=>{const d=Math.hypot(p[0]-points[i][0],p[1]-points[i][1]);length+=d;return d})
  let remaining=length*clamp(progress)
  ctx.save();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.setLineDash(dash)
  ctx.beginPath();ctx.moveTo(...points[0])
  for(let i=0;i<lengths.length;i++){
    const f=Math.min(1,remaining/(lengths[i]||1))
    ctx.lineTo(mix(points[i][0],points[i+1][0],f),mix(points[i][1],points[i+1][1],f))
    remaining-=lengths[i];if(remaining<=0)break
  }
  ctx.globalAlpha*=.91;ctx.stroke();ctx.restore()
}
function circlePoints(x,y,r,rx=1,start=0,end=Math.PI*2){
  return Array.from({length:65},(_,i)=>{const a=mix(start,end,i/64);return[x+Math.cos(a)*r*rx,y+Math.sin(a)*r]})
}

export class BoardRenderer {
  constructor({createCanvas,images={},width=W,height=H}) {
    this.createCanvas=createCanvas;this.images=images;this.width=width;this.height=height
    this.photoCache=new Map()
    this.material=this.makeMaterial()
  }
  makeMaterial(){
    const canvas=this.createCanvas(BOARD.w,BOARD.h),ctx=canvas.getContext('2d')
    ctx.fillStyle=C.paper;ctx.fillRect(0,0,BOARD.w,BOARD.h)
    const fall=ctx.createRadialGradient(1900,950,100,2900,1600,4200)
    fall.addColorStop(0,'rgba(255,255,251,.35)');fall.addColorStop(.56,'rgba(231,227,211,.06)');fall.addColorStop(1,'rgba(91,87,68,.21)')
    ctx.fillStyle=fall;ctx.fillRect(0,0,BOARD.w,BOARD.h)
    // Latent erased lesson: large, faint fragments, never distracting new content.
    const ghost=this.createCanvas(BOARD.w/4,BOARD.h/4),g=ghost.getContext('2d')
    g.scale(.25,.25)
    for(let i=0;i<120;i++){
      const x=rand(i+10)*6300,y=rand(i+400)*3500,w=120+rand(i+750)*650
      g.globalAlpha=.012+rand(i+1200)*.014
      g.strokeStyle=[C.ink,C.blue,C.red][i%3];g.lineWidth=3+rand(i)*5
      if(i%4===0){g.beginPath();g.ellipse(x,y,w/3,w/5,rand(i)*2,0,6.28);g.stroke()}
      else if(i%4===1){g.strokeRect(x,y,w,w*.25)}
      else {g.beginPath();g.moveTo(x,y);g.bezierCurveTo(x+w*.3,y-20,x+w*.6,y+25,x+w,y-8);g.stroke()}
    }
    ctx.filter='blur(3px)';ctx.drawImage(ghost,0,0,BOARD.w,BOARD.h)
    ctx.globalAlpha=1;ctx.filter='none'
    for(let i=0;i<17000;i++){
      const x=rand(i+8000)*6400,y=rand(i+29000)*3600
      ctx.fillStyle=i%2?'rgba(255,255,255,.06)':'rgba(55,48,35,.025)'
      ctx.fillRect(x,y,1+rand(i+10)*2,1)
    }
    return canvas
  }
  marker(ctx,e,p=1){
    const {x=0,y=0,text='',size=100,color=C.ink}=e
    ctx.save();ctx.translate(x,y);ctx.rotate((e.rot||0)*Math.PI/180)
    ctx.font=`${size}px Marker`;ctx.textBaseline='alphabetic';ctx.fillStyle=color
    const full=Array.from(text),count=full.length*clamp(p)
    let cursor=0
    for(let i=0;i<full.length;i++){
      const char=full[i],advance=ctx.measureText(char).width
      const reveal=clamp(count-i)
      if(reveal>0){
        ctx.save();ctx.translate(cursor,(rand(i+text.length*51)-.5)*size*.018)
        ctx.rotate((rand(i+text.length*71)-.5)*.023)
        ctx.beginPath();ctx.rect(-4,-size*1.1,(advance+8)*reveal,size*1.4);ctx.clip()
        ctx.globalAlpha*=.91;ctx.fillText(char,0,0);ctx.restore()
      }
      cursor+=advance
    }
    ctx.restore()
  }
  magnet(ctx,x,y,r=25,color=C.ink,age=4){
    if(age<0)return
    const bounce=age<.5?Math.exp(-age*10)*Math.cos(age*23)*.3:0
    ctx.save();ctx.translate(x,y);ctx.scale(1+bounce,1+bounce)
    ctx.shadowColor='rgba(26,26,20,.32)';ctx.shadowBlur=13;ctx.shadowOffsetX=9;ctx.shadowOffsetY=16
    const grad=ctx.createRadialGradient(-r*.3,-r*.4,1,0,0,r)
    grad.addColorStop(0,color===C.ink?'#747779':color);grad.addColorStop(.5,color);grad.addColorStop(1,color===C.ink?'#11151b':'#86281b')
    ctx.fillStyle=grad;ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.fill()
    ctx.shadowColor='transparent';ctx.fillStyle='rgba(255,255,255,.23)'
    ctx.beginPath();ctx.ellipse(-r*.22,-r*.4,r*.33,r*.15,-.4,0,6.28);ctx.fill();ctx.restore()
  }
  paper(ctx,e,age){
    if(age<0)return
    const drop=age<.65?Math.exp(-age*8)*Math.cos(age*19):0
    ctx.save();ctx.translate(e.x,e.y-45*drop);ctx.rotate(((e.rot||0)+drop*3)*Math.PI/180)
    ctx.shadowColor='rgba(36,31,20,.28)';ctx.shadowBlur=10+Math.abs(drop)*25;ctx.shadowOffsetX=5+drop*15;ctx.shadowOffsetY=9+drop*35
    const grad=ctx.createLinearGradient(0,0,e.w,e.h);grad.addColorStop(0,'#fffef8');grad.addColorStop(1,e.fill||'#e7e5dc')
    ctx.fillStyle=grad;rounded(ctx,0,0,e.w,e.h,e.tag?9:1);ctx.fill()
    ctx.shadowColor='transparent';ctx.strokeStyle='rgba(101,99,86,.18)';ctx.lineWidth=2;ctx.stroke()
    if(e.lines){
      ctx.fillStyle=e.color||C.ink
      for(let i=0;i<e.lines.length;i++){
        const l=typeof e.lines[i]==='string'?{text:e.lines[i]}:e.lines[i]
        ctx.font=`${l.weight||e.weight||600} ${l.size||e.size||48}px Sans`
        ctx.fillStyle=l.color||e.color||C.ink
        const baseline=e.tag?e.h*.69:(e.pad||34)+(i+1)*(e.leading||65)-15
        ctx.fillText(l.text,e.pad||34,baseline)
      }
    }
    if(e.rule)segment(ctx,[[34,e.rule],[e.w-35,e.rule]],1,C.red,5)
    if(e.photo&&this.images[e.photo]){
      const im=this.images[e.photo];ctx.drawImage(im,18,18,e.w-36,e.h-36)
    }
    this.magnet(ctx,28,23,e.tag?20:18,e.red?C.red:C.ink,age-.1)
    if(!e.tag)this.magnet(ctx,e.w-28,23,18,C.ink,age-.18)
    ctx.restore()
  }
  photo(ctx,e,age){
    if(age<0||!this.images[e.asset])return
    const im=this.images[e.asset],drop=age<.65?Math.exp(-age*8)*Math.cos(age*18):0
    ctx.save();ctx.translate(e.x,e.y-60*drop);ctx.rotate(((e.rot||0)+drop*4)*Math.PI/180)
    // Clip the source photograph to a measured polygon in the video scene.
    // The original source bytes are preserved.
    ctx.shadowColor='rgba(28,25,20,.30)';ctx.shadowBlur=10+Math.abs(drop)*25;ctx.shadowOffsetX=8+drop*10;ctx.shadowOffsetY=13+drop*35
    if(e.alpha){
      if(age>=.7){
        const key=`${e.asset}:${e.w}:${e.h}`
        if(!this.photoCache.has(key)){
          const c=this.createCanvas(Math.ceil(e.w)+96,Math.ceil(e.h)+96),g=c.getContext('2d')
          g.shadowColor='rgba(28,25,20,.30)';g.shadowBlur=10;g.shadowOffsetX=8;g.shadowOffsetY=13
          g.drawImage(im,48,48,e.w,e.h);this.photoCache.set(key,c)
        }
        ctx.shadowColor='transparent';ctx.drawImage(this.photoCache.get(key),-48,-48)
      }else{ctx.drawImage(im,0,0,e.w,e.h);ctx.shadowColor='transparent'}
    }else{
      const polygon=e.polygon||[[0,0],[1,0],[1,1],[0,1]]
      ctx.beginPath();polygon.forEach((p,i)=>i?ctx.lineTo(p[0]*e.w,p[1]*e.h):ctx.moveTo(p[0]*e.w,p[1]*e.h));ctx.closePath()
      ctx.fillStyle='#c7c4ba';ctx.fill();ctx.shadowColor='transparent';ctx.clip()
      ctx.drawImage(im,0,0,e.w,e.h)
      ctx.fillStyle='rgba(220,203,173,.06)';ctx.fillRect(0,0,e.w,e.h)
    }
    this.magnet(ctx,e.w*.08,e.h*.47,22,C.ink,age-.25)
    this.magnet(ctx,e.w*.69,e.h*.12,22,C.ink,age-.3)
    ctx.restore()
  }
  person(ctx,e,p,t){
    const s=e.size/250,x=e.x,y=e.y,color=e.color||C.ink
    ctx.save();ctx.translate(x,y);ctx.scale(s,s)
    let paths=[
      circlePoints(0,-80,28),
      [[-28,-86],[-13,-112],[13,-110],[28,-86]],
      [[-4,-50],[-13,4],[-15,70],[26,70],[52,121]],
      [[-15,70],[-48,113],[-18,123]],
      [[-9,-27],[30,8],[68,3]],
      [[-13,-28],[-48,13],[-21,37]],
      [[40,29],[175,29]],[[155,29],[155,123]],
      [[-62,51],[-59,123]],[[-62,51],[-9,51]],
      [[79,22],[123,22],[133,3],[97,1],[79,22]]
    ]
    if(e.pose==='teacher'){
      paths=[...paths.slice(0,2),
        [[0,-51],[0,46],[-29,119]],[[0,46],[38,119]],
        [[0,-28],[40,-9],[90,-40]],[[0,-26],[-42,9]],
        [[88,-40],[130,-96]]]
    }
    const amount=p*paths.length
    paths.forEach((path,i)=>segment(ctx,path,clamp(amount-i),color,5.8))
    if(p>=1){
      ctx.fillStyle=color;ctx.beginPath();ctx.arc(11,-84,2.5,0,6.28);ctx.fill()
      segment(ctx,[[14,-70],[21,-73]],1,color,2.8)
      if(e.pose==='write'){
        const offset=Math.sin(t*8)*6
        segment(ctx,[[68,3],[78+offset,15],[86+offset,-5]],1,C.blue,4)
      }
    }
    ctx.restore()
  }
  flag(ctx,e,p){
    const x=e.x,y=e.y,s=e.size/300
    ctx.save();ctx.translate(x,y);ctx.scale(s,s)
    segment(ctx,[[0,195],[0,0],[280,6],[274,165],[0,159]],p,C.ink,5)
    if(p>.25){
      ctx.save();ctx.beginPath();ctx.rect(4,5,272*clamp((p-.25)/.4),157);ctx.clip()
      ctx.fillStyle=C.red;ctx.globalAlpha=.82;ctx.beginPath();ctx.moveTo(6,7);ctx.lineTo(275,10);ctx.lineTo(270,158);ctx.lineTo(5,153);ctx.fill()
      ctx.globalAlpha=1;ctx.fillStyle='#fffdf4';ctx.save();ctx.beginPath()
      ctx.arc(111,83,47,0,Math.PI*2);ctx.clip();ctx.beginPath()
      ctx.arc(111,83,47,0,Math.PI*2);ctx.closePath()
      ctx.moveTo(163,76);ctx.arc(125,76,38,0,Math.PI*2);ctx.closePath();ctx.fill('evenodd');ctx.restore()
      ctx.fillStyle='#fffdf4';ctx.beginPath()
      for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,r=i%2?11:29;const aX=179+Math.cos(a)*r,aY=80+Math.sin(a)*r;i?ctx.lineTo(aX,aY):ctx.moveTo(aX,aY)}
      ctx.closePath();ctx.fill();ctx.restore()
    }
    ctx.restore()
  }
  ruler(ctx,e,age){
    if(age<0)return
    const drop=Math.exp(-age*9)*Math.cos(age*24)
    ctx.save();ctx.translate(e.x,e.y-45*drop);ctx.rotate((e.rot||0)*Math.PI/180)
    ctx.shadowColor='rgba(20,20,18,.3)';ctx.shadowBlur=12;ctx.shadowOffsetX=7;ctx.shadowOffsetY=12
    const g=ctx.createLinearGradient(0,0,0,90)
    for(const [a,c] of [[0,'#dddeda'],[.12,'#9eaaa9'],[.42,'#d4d5cd'],[.7,'#999f9c'],[1,'#e4e5df']])g.addColorStop(a,c)
    ctx.fillStyle=g;ctx.fillRect(0,0,e.w,90);ctx.shadowColor='transparent'
    ctx.fillStyle='#4e5456';ctx.font='22px Sans';ctx.strokeStyle='#596168';ctx.lineWidth=1
    for(let x=12;x<e.w-10;x+=10){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,x%100===12?45:x%50===12?31:19);ctx.stroke();if(x%100===12)ctx.fillText(String(Math.round((x-12)/10)),x-7,69)}
    this.magnet(ctx,40,52,25,C.ink,age-.1);this.magnet(ctx,e.w-40,52,25,C.ink,age-.2);ctx.restore()
  }
  stamp(ctx,e,age){
    if(age<0)return
    const bounce=age<.4?Math.exp(-age*15)*Math.sin(age*38)*14:0
    ctx.save();ctx.translate(e.x,e.y+bounce);ctx.rotate((e.rot||-7)*Math.PI/180)
    ctx.strokeStyle=C.red;ctx.lineWidth=5;ctx.fillStyle=C.red
    ctx.strokeRect(0,0,e.w,e.h);ctx.strokeRect(10,10,e.w-20,e.h-20)
    ctx.font=`800 ${e.size||67}px Sans`;ctx.textAlign='center';ctx.textBaseline='middle'
    ctx.fillText(e.text,e.w/2,e.h/2+3)
    // Small enamel-coloured pits imitate an uneven rubber impression.
    ctx.fillStyle=C.paper
    for(let i=0;i<160;i++){const x=rand(i+e.x)*e.w,y=rand(i+e.y)*e.h;ctx.fillRect(x,y,2+rand(i)*4,1+rand(i+2)*3)}
    ctx.restore()
  }
  drawElement(ctx,e,t){
    const age=t-(e.at||0),p=e.dur?clamp(age/e.dur):age>=0?1:0
    if(age<0)return
    ctx.save()
    if(e.eraseAt!==undefined)ctx.globalAlpha*=mix(1,.065,ease((t-e.eraseAt)/.8))
    if(e.type==='marker')this.marker(ctx,e,p)
    if(e.type==='line')segment(ctx,e.points,p,e.color||C.ink,e.width||6,e.dash||[])
    if(e.type==='dimension'){
      const end=mix(e.x,e.x+e.w,p)
      segment(ctx,[[e.x,e.y],[end,e.y+1]],1,e.color||C.blue,8)
      segment(ctx,[[e.x+30,e.y-17],[e.x,e.y],[e.x+30,e.y+17]],1,e.color||C.blue,7)
      if(p>.98)segment(ctx,[[end-30,e.y-17],[end,e.y],[end-30,e.y+17]],1,e.color||C.blue,7)
    }
    if(e.type==='circle')segment(ctx,circlePoints(e.x,e.y,e.r,e.rx||1,-.25,Math.PI*2+.12),p,e.color||C.red,e.width||7)
    if(e.type==='paper')this.paper(ctx,e,age)
    if(e.type==='photo')this.photo(ctx,e,age)
    if(e.type==='person')this.person(ctx,e,p,t)
    if(e.type==='flag')this.flag(ctx,e,p)
    if(e.type==='ruler')this.ruler(ctx,e,age)
    if(e.type==='stamp')this.stamp(ctx,e,age)
    if(e.type==='magnet')this.magnet(ctx,e.x,e.y,e.r||24,e.color||C.ink,age)
    ctx.restore()
  }
  render(ctx,film,frame,{subtitles=true}={}){
    const t=frame/film.fps,cam=film.camera(frame)
    ctx.save();ctx.scale(this.width/W,this.height/H)
    ctx.fillStyle='#8f8b83';ctx.fillRect(0,0,W,H)
    ctx.translate(W/2,H*.47);ctx.rotate(cam.roll*Math.PI/180);ctx.scale(cam.z,cam.z);ctx.translate(-cam.x,-cam.y)
    ctx.shadowColor='rgba(17,16,13,.5)';ctx.shadowBlur=60;ctx.shadowOffsetX=25;ctx.shadowOffsetY=28
    ctx.fillStyle='#bebfb6';ctx.fillRect(-38,-38,BOARD.w+76,BOARD.h+76);ctx.shadowColor='transparent'
    ctx.drawImage(this.material,0,0)
    const steel=ctx.createLinearGradient(0,-30,0,20)
    steel.addColorStop(0,'#e2e2dc');steel.addColorStop(.45,'#aeb2b0');steel.addColorStop(1,'#696e6c')
    ctx.fillStyle=steel;ctx.fillRect(-35,-35,BOARD.w+70,35);ctx.fillRect(-35,0,35,BOARD.h+30);ctx.fillRect(BOARD.w,0,35,BOARD.h+30)
    for(const e of film.elements){
      const par=e.depth||0
      ctx.save();ctx.translate((cam.x-BOARD.w/2)*par*.0006,(cam.y-BOARD.h/2)*par*.0006)
      this.drawElement(ctx,e,t);ctx.restore()
    }
    // Reflection crosses the enamel without washing out the foreground objects.
    const sheen=ctx.createLinearGradient(1000+t*2,0,3800+t*2,2500)
    sheen.addColorStop(0,'rgba(255,255,255,0)');sheen.addColorStop(.47,'rgba(255,255,255,.025)');sheen.addColorStop(.50,'rgba(255,255,255,.075)');sheen.addColorStop(.58,'rgba(255,255,255,.01)');sheen.addColorStop(1,'rgba(255,255,255,0)')
    ctx.fillStyle=sheen;ctx.fillRect(0,0,BOARD.w,BOARD.h)
    const tray=ctx.createLinearGradient(0,BOARD.h,0,BOARD.h+105)
    tray.addColorStop(0,'#d4d6d0');tray.addColorStop(.2,'#acb0ae');tray.addColorStop(.5,'#737a78');tray.addColorStop(1,'#b4b6b1')
    ctx.fillStyle=tray;ctx.fillRect(-70,BOARD.h,BOARD.w+140,105)
    for(let i=0;i<4;i++){
      ctx.save();ctx.translate(1300+i*220,BOARD.h+35);ctx.rotate(-.025+i*.014)
      ctx.fillStyle='#eeeae0';rounded(ctx,0,0,160,24,6);ctx.fill()
      ctx.fillStyle=[C.ink,C.blue,C.red,C.ink][i];rounded(ctx,111,0,58,24,5);ctx.fill();ctx.restore()
    }
    ctx.restore()
    if(subtitles)this.subtitle(ctx,film,frame)
  }
  subtitle(ctx,film,frame){
    const cue=film.subtitles.find(c=>frame>=c.start&&frame<c.end)
    if(!cue)return
    ctx.save();ctx.scale(this.width/W,this.height/H)
    ctx.font='500 37px Sans';ctx.textAlign='center';ctx.textBaseline='middle'
    const width=Math.min(1650,ctx.measureText(cue.text).width+100),x=(W-width)/2
    ctx.shadowColor='rgba(42,39,31,.18)';ctx.shadowBlur=18;ctx.shadowOffsetY=6
    ctx.fillStyle='rgba(255,254,249,.94)';rounded(ctx,x,950,width,87,11);ctx.fill()
    ctx.shadowColor='transparent';ctx.fillStyle=C.blue;ctx.fillRect(x+18,968,4,49)
    ctx.fillStyle=C.ink;ctx.fillText(cue.text,W/2+8,994);ctx.restore()
  }
}
