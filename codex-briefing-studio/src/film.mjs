import {C,ease,mix,clamp} from './engine.mjs'
export const FPS=24

// Recognition supplies timing; the authored script supplies wording and punctuation.
function timedSourceWords(text,observed){
  const tokens=value=>value.toLowerCase().replaceAll('48','forty eight').replaceAll('17','seventeen')
    .replaceAll('%',' percent').replaceAll('practise','practice').match(/[a-z]+/g)||[]
  const actual=observed.flatMap(word=>{
    const parts=tokens(word.word)
    return parts.map((token,i)=>({token,start:mix(word.start,word.end,i/parts.length),
      end:mix(word.start,word.end,(i+1)/parts.length)}))
  })
  let offset=0
  const result=text.split(/\s+/).map(word=>{
    const expected=tokens(word),slice=actual.slice(offset,offset+expected.length)
    if(!expected.length||expected.some((token,i)=>token!==slice[i]?.token))
      throw Error(`Cannot align authored caption word: ${word}`)
    offset+=expected.length
    return {word,start:slice[0].start,end:slice.at(-1).end}
  })
  if(offset!==actual.length)throw Error('Extra recognized words remain after caption alignment')
  return result
}

export function makeFilm(narration,audio=[],observations=[]) {
  const records=new Map(audio.map(a=>[a.id,a]))
  let cursor=14
  const shots=narration.map((line,i)=>{
    const record=records.get(line.id)
    const seconds=record?.duration||line.text.split(/\s+/).length/2.65
    const start=cursor
    const duration=Math.ceil(seconds*FPS)
    const minimum={hook:9,measures:12,practice:15,exam:11,tutor:12,scope:10,physics:14,
      thinking:10,recognition:9,example:9,attempt:13,recall:11,transfer:11,closing:9}[line.region]
    cursor+=Math.max(duration+(i===3?32:22),minimum*FPS)
    return {...line,start,end:cursor,voiceStart:start+6,voiceEnd:start+6+duration,
      audio:record?.path||null}
  })
  const end=cursor+132
  const byRegion=Object.fromEntries(shots.map(s=>[s.region,s]))
  const time=(region,offset=0)=>(byRegion[region].start/FPS)+offset
  const elements=[],events=[]
  const add=e=>{
    e.id=e.id||`${e.type}-${elements.length}`
    elements.push(e)
    if(e.at>0)events.push({id:e.id,frame:Math.round(e.at*FPS),kind:e.type,duration:Math.round((e.dur||.3)*FPS)})
    return e
  }
  const text=(text,x,y,size=100,at=0,extra={})=>add({type:'marker',text,x,y,size,at,dur:Math.max(.4,text.length*.045),...extra})
  const line=(points,at=0,extra={})=>add({type:'line',points,at,dur:.65,...extra})
  const paper=(x,y,w,h,lines,at=0,extra={})=>add({type:'paper',x,y,w,h,lines,at,depth:8,...extra})
  const person=(x,y,size,at=0,extra={})=>add({type:'person',x,y,size,at,dur:1.3,...extra})
  const dimension=(x,y,w,at,extra={})=>add({type:'dimension',x,y,w,at,dur:.7,...extra})
  const circle=(x,y,r,at,extra={})=>add({type:'circle',x,y,r,at,dur:.7,...extra})

  // The opening object remains in place throughout the film.
  add({type:'photo',asset:'notebookCutout',x:210,y:120,w:1120,h:747,at:-1,rot:-3,alpha:true,depth:8})
  paper(520,340,600,185,[{text:'3x + 6 = 21',size:68},{text:'x = 5',size:61}],-.5,{rot:-3,pad:32,leading:77})
  text('FINISHED',1450,340,145,.10,{color:C.blue,dur:.55})
  dimension(1300,440,840,.05,{dur:.28})
  person(1510,680,410,.8,{pose:'write'})
  text('Can you do it alone?',1600,590,90,3.2,{eraseAt:time('example')})
  paper(520,337,605,190,[],time('hook',4),{rot:-3})
  text('?',760,477,105,time('hook',4.5),{color:C.red})
  add({type:'stamp',x:2200,y:740,w:450,h:133,text:'CHECK AGAIN',size:50,at:time('hook',5.2),rot:-6,eraseAt:time('example')})

  // Four distinct tests, expressed as people and physical labels.
  const measures=['WITH HELP','ALONE','LATER','NEW PROBLEM']
  measures.forEach((label,i)=>{
    const x=330+i*800,at=time('measures',.3+i*1.1)
    paper(x,1040,660,135,[{text:label,size:65}],at,{tag:true,pad:66,leading:88})
    person(x+220,900,210,at-.2,{pose:i===0?'teacher':'write'})
    if(i>0)line([[x-110,1010],[x-35,1010]],at,{color:C.blue,width:7})
    text(['performance','independence','retention','transfer'][i],x+10,1270,76,at+1)
  })
  line([[400,1320],[2960,1320]],time('measures',6),{color:C.grey,width:3})

  // Study context: flag and learners appear in the same board space as the evidence.
  add({type:'flag',x:2810,y:210,size:360,at:time('practice',.3),dur:1.2})
  text('TURKEY',3200,315,100,time('practice',.7))
  text('~1,000 students',3200,440,88,time('practice',1.5))
  person(2900,660,265,time('practice',2),{pose:'write'})
  person(3240,660,265,time('practice',2.4),{pose:'write'})
  person(3580,660,265,time('practice',2.8),{pose:'write'})
  paper(3380,790,680,250,[{text:'MATHS EXPERIMENT',size:48},{text:'Randomized groups',size:48},{text:'Bastani et al.',size:41}],time('practice',3),{rot:2,leading:67})

  text('SAME STUDY. TWO TESTS.',410,1480,112,time('practice',4))
  // The blue rulers share one normalization, not a percentage-point claim.
  line([[650,1550],[650,2530]],time('practice',5),{color:C.blue,width:4,dash:[25,20],dur:1.2})
  line([[1650,1550],[1650,2530]],time('practice',5),{color:C.blue,width:4,dash:[25,20],dur:1.2})
  add({type:'ruler',x:638,y:1540,w:1220,at:time('practice',5.5),depth:11})
  text('control index = 100',1900,1610,72,time('practice',6),{color:C.grey})
  paper(450,1710,785,155,[{text:'PRACTICE WITH AI',size:68}],time('practice',6.4),{tag:true,pad:66,leading:98})
  paper(1320,1690,560,180,[{text:'3x + 6 = 21',size:61},{text:'x = 5',size:54}],time('practice',6.55),{rot:-2,leading:75})
  person(2690,1660,210,time('practice',6.6),{pose:'write'})
  dimension(650,1945,1480,time('practice',6.65),{dur:.6})
  text('148',2160,1974,112,time('practice',7.3),{color:C.blue})
  text('+48%',2420,1950,150,time('practice',7.4),{color:C.blue})
  text('relative to control',2410,2040,65,time('practice',8.2))

  paper(450,2180,800,155,[{text:'EXAM WITHOUT AI',size:67}],time('exam',.4),{tag:true,pad:66,leading:98})
  paper(1300,2150,535,170,[{text:'3x + 6 = 21',size:61},{text:'x = ?',size:54}],time('exam',.7),{rot:2,leading:72})
  person(2770,2180,210,time('exam',1),{pose:'write'})
  dimension(650,2430,830,time('exam',1.7),{dur:1.0})
  line([[1480,2430],[1650,2430]],time('exam',2.7),{color:C.red,width:7,dash:[15,13]})
  text('83',1510,2530,110,time('exam',2.8),{color:C.blue})
  text('−17%',1870,2470,160,time('exam',3.2),{color:C.red})
  add({type:'stamp',x:2410,y:2370,w:650,h:145,text:'WEAKER ALONE',size:61,at:time('exam',4),rot:-5})
  text('Better practice ≠ better exam',450,2690,105,time('exam',5),{color:C.ink})

  // A tutor isn't placed on a fabricated numerical bar.
  paper(420,2800,650,145,[{text:'TEACHER HINTS',size:66}],time('tutor',.4),{tag:true,pad:65,leading:94})
  person(1190,2850,275,time('tutor',.7),{pose:'teacher'})
  paper(1440,2760,470,245,[{text:'What is the',size:55},{text:'first step?',size:55}],time('tutor',1.8),{rot:-3,leading:80})
  person(2110,2860,275,time('tutor',2.4),{pose:'write'})
  line([[1300,2790],[1430,2790]],time('tutor',2),{color:C.blue})
  text('Penalty largely removed',2400,2850,89,time('tutor',4))
  text('Exam gain: not established',2400,2970,81,time('tutor',6),{color:C.grey})

  // The counterexample is deliberately a separate study, without a common axis.
  paper(3320,1150,870,370,[
    {text:'A DIFFERENT DESIGN',size:65},
    {text:'College physics tutor',size:62},
    {text:'Higher immediate scores',size:55,color:C.blue},
    {text:'Kestin et al. · 2025',size:42}
  ],time('physics',.5),{rot:-1.5,leading:84})
  person(3400,1730,270,time('physics',1.6),{pose:'teacher'})
  person(3770,1730,270,time('physics',2.2),{pose:'write'})
  text('F = ma',3560,1600,68,time('physics',4),{color:C.blue})
  circle(3660,1575,42,time('physics',5),{rx:2.4,color:C.blue,width:4})
  paper(3290,2070,910,340,[
    {text:'WHAT THESE TESTS SHOW',size:58},
    {text:'Immediate performance',size:60},
    {text:'Not months of retention',size:54},
    {text:'Not permanent damage',size:54}
  ],time('scope',.3),{rot:1.4,leading:76})
  line([[3340,2450],[4140,2450]],time('scope',2),{color:C.grey,width:4})
  text('Design matters.',3330,2590,125,time('physics',7),{color:C.ink})

  // A person chooses a method. The distinction is later erased to a visible ghost.
  text('I can follow it ≠ I know it',425,3130,100,time('recognition',.5),{eraseAt:time('recall')})
  line([[430,3160],[1770,3160]],time('recognition',2),{color:C.red,width:6,eraseAt:time('recall')})
  text('Which step is yours?',2420,3180,94,time('thinking',.3))
  person(3550,3020,265,time('thinking',1),{pose:'write'})
  paper(3740,2850,500,225,[{text:'CHOOSE',size:66},{text:'THE METHOD',size:55}],time('thinking',1.8),{rot:-2,leading:77})

  // Practice strip: illustrations take over from numbers.
  const steps=[
    {x:420,label:'1  GET THE RIGHT HELP',region:'attempt',pose:'teacher'},
    {x:1570,label:'2  HIDE · EXPLAIN · CHECK',region:'recall',pose:'write'},
    {x:2800,label:'3  CHANGE IT · RETURN',region:'transfer',pose:'write'}
  ]
  for(const s of steps){
    const at=time(s.region,.4)
    paper(s.x,3250,1080,145,[{text:s.label,size:55}],at,{tag:true,pad:65,leading:94})
    person(s.x+180,3495,180,at+.4,{pose:s.pose})
    text(s.region==='attempt'?'example + hint':s.region==='recall'?'memory + feedback':'new problem + later',s.x+400,3490,62,at+1)
  }
  // A worked example is a physical piece of paper placed beside the learner.
  paper(1930,412,650,340,[{text:'WORKED EXAMPLE',size:51},{text:'3x + 6 = 21',size:62},{text:'3x = 15  →  x = 5',size:51}],
    time('example',.4),{rot:2,leading:80})

  // Hidden until the final pullback: secondary photographs, evidence, conclusion.
  add({type:'photo',asset:'notebookCutout',x:4590,y:240,w:720,h:480,at:0,rot:-4,alpha:true,depth:8})
  paper(5460,260,610,400,[
    {text:'EVIDENCE NOTES',size:56},
    {text:'Practice: 148 / 100',size:48,color:C.blue},
    {text:'Exam: 83 / 100',size:48,color:C.blue},
    {text:'Relative changes.',size:43},
    {text:'Different tests.',size:43}
  ],0,{rot:3,leading:69})
  text('LEARN',4550,1230,300,time('closing',3),{color:C.red,dur:.9})
  text('WITHOUT',4550,1580,255,time('closing',3.7),{dur:1})
  text('THE ANSWER.',4550,1920,220,time('closing',4.4),{dur:1})
  line([[4200,3170],[4350,3170],[4400,2000],[4500,1940]],time('closing',2),{width:8,dur:1.8})
  person(4900,2300,420,0,{pose:'write'})
  text('A fresh attempt.',5240,2240,102,0)
  text('Then come back later.',5240,2390,80,0)
  paper(4500,2720,1580,610,[
    {text:'Does AI Help You Learn—',size:94,weight:700},
    {text:'or Just Finish?',size:108,weight:700},
    {text:'ENGINEERING BRIEFING BOARD',size:52},
    {text:'LeoGuoLabs · A film made with Codex',size:44}
  ],0,{leading:125,pad:65,rule:310})

  const poses={
    hook:[1500,540,.77,-1.2],measures:[1900,1000,.55,.4],
    practice:[1700,1780,.59,-.3],exam:[1710,2240,.59,.3],
    tutor:[2150,2820,.53,0],scope:[3720,2250,1.35,1],
    physics:[3710,1520,1.17,-.8],thinking:[3310,3040,.94,.5],
    recognition:[1120,3130,1.08,-.6],example:[2220,550,1.4,1],
    attempt:[1050,3040,.78,-.3],recall:[2130,3040,.78,.4],
    transfer:[3350,3040,.78,-.3],closing:[3190,3040,.78,0]
  }
  const keys=[{frame:0,x:1330,y:440,z:2.2,roll:-3},
    {frame:26,x:1170,y:520,z:1.22,roll:-1.2},
    {frame:72,x:1500,y:540,z:.77,roll:-1.2},
    {frame:shots[0].end-34,x:1502,y:538,z:.775,roll:-1.15}]
  shots.forEach((s,i)=>{
    if(i===0)return
    let [x,y,z,roll]=poses[s.region]
    if(s.region==='practice'){
      keys.push({frame:s.start-12,x:3260,y:480,z:1.15,roll:-.8})
      keys.push({frame:s.start+96,x:3260,y:480,z:1.17,roll:-.5})
      keys.push({frame:s.start+154,x,y,z,roll})
    } else keys.push({frame:s.start+12,x,y,z,roll})
    keys.push({frame:s.end-34,x:x+5,y:y-2,z:z*1.01,roll:roll+.05})
  })
  // The full wall appears only once; the final title remains inside its frame.
  keys.push({frame:cursor-28,x:3190,y:3040,z:.78,roll:0})
  keys.push({frame:cursor+58,x:3200,y:1790,z:.279,roll:0})
  keys.push({frame:end,x:3200,y:1790,z:.282,roll:0})
  keys.sort((a,b)=>a.frame-b.frame)
  function camera(frame){
    let i=0;while(i<keys.length-2&&keys[i+1].frame<frame)i++
    const a=keys[i],b=keys[i+1],u=ease((frame-a.frame)/(b.frame-a.frame))
    const out={}
    for(const k of ['x','y','z','roll'])out[k]=mix(a[k],b[k],u)
    const breath=mix(1,.15,ease((frame-cursor)/24))
    out.x+=Math.sin(frame*.013)*1.6*breath;out.y+=Math.sin(frame*.017+.4)*1.2*breath
    return out
  }
  const subtitles=[]
  for(const s of shots){
    const observed=observations.find(o=>o.id===s.id)
    if(observed?.words?.length){
      const chunks=[];let words=[]
      for(const word of timedSourceWords(s.text,observed.words)){
        if(words.length&&[...words,word].map(w=>w.word.trim()).join(' ').length>58){
          chunks.push(words);words=[]
        }
        words.push(word)
        if(/[.!?]$/.test(word.word.trim())){
          chunks.push(words);words=[]
        }
      }
      if(words.length)chunks.push(words)
      for(let i=1;i<chunks.length;i++){
        const previous=chunks[i-1],group=chunks[i]
        if(group.length<3&&!/[.!?]$/.test(previous.at(-1).word.trim())){
          while(group.length<3&&previous.length>3)group.unshift(previous.pop())
        }
      }
      chunks.forEach((group,i)=>{
        const start=s.voiceStart+Math.round(group[0].start*FPS)
        const next=chunks[i+1]?.[0].start
        const end=s.voiceStart+Math.round((next??Math.min((s.voiceEnd-s.voiceStart)/FPS+.4,group.at(-1).end+.4))*FPS)
        subtitles.push({start,end,text:group.map(w=>w.word.trim()).join(' '),shotId:s.id,
          timing:'Authored text aligned to independently observed word timestamps'})
      })
      continue
    }
    const words=s.text.split(/\s+/),chunks=[]
    let current=[]
    for(const word of words){
      if([...current,word].join(' ').length>58){chunks.push(current.join(' '));current=[]}
      current.push(word)
    }
    if(current.length)chunks.push(current.join(' '))
    const total=chunks.reduce((n,c)=>n+c.length,0)
    let start=s.voiceStart
    chunks.forEach((text,i)=>{
      const n=Math.round((s.voiceEnd-s.voiceStart)*text.length/total)
      const finish=i===chunks.length-1?s.voiceEnd+14:start+n
      subtitles.push({start,end:finish,text});start=finish
    })
  }
  return {fps:FPS,duration_frames:end,shots,elements,events,keys,camera,subtitles,
    revealStart:cursor-28,reference:'LemoLab — The Ship Decides'}
}
