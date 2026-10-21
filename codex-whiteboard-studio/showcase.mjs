import {comparisonBeats} from './src/comparison.mjs'
const $=id=>document.getElementById(id)
const main=$('film-player')
const read=async path=>{const r=await fetch(path);if(!r.ok)throw new Error(`${path}: ${r.status}`);return r.json()}
const time=t=>`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`
let edition='short',base=''
try{
  const long=await read('editions/long/media/timeline.json')
  if(long.complete_audio){
    $('edition-picker').hidden=false
    if(new URLSearchParams(location.search).get('edition')==='long'){
      edition='long';base='editions/long/'
      $('edition-select').value='long'
      const video=`${base}media/does-ai-help-you-learn-long.mp4`
      main.poster=`${base}media/poster.jpg`
      main.querySelector('source').src=video
      main.querySelector('track').src=`${base}media/captions.vtt`
      main.load()
      $('download-film').href=video
    }
  }
}catch{}
$('edition-select').onchange=()=>{
  const url=new URL(location.href);url.searchParams.set('edition',$('edition-select').value)
  location.assign(url)
}
let timeline,beats=[]
try{
  timeline=await read(`${base}media/timeline.json`)
  $('film-duration').textContent=`${time(timeline.duration)} MIN`
  beats=comparisonBeats(timeline,await read(`${base}content/comparison.json`))
  const chapterLabels=edition==='short'
    ?[['hook','The question'],['study','Two scoreboards'],['counter','Design matters'],['practice','A practical loop'],['closing','What remains']]
    :[['hook','The question'],['turkey','Two scoreboards'],['delay','One week later'],
      ['guidance','Choosing help'],['example','Try the method'],['closing','What remains']]
  for(const [id,label]of chapterLabels){
    const b=beats.find(b=>b.id===id),button=document.createElement('button'),stamp=document.createElement('small')
    stamp.textContent=time(b.start);button.append(stamp,document.createTextNode(label))
    button.onclick=()=>{main.currentTime=b.start;main.play();$('screen').scrollIntoView({behavior:'smooth'})}
    $('chapters').append(button)
  }
}catch{
  $('film-duration').textContent='SAMPLE FILM'
}
try{
  const {claims}=await read(`${base}content/sources.json`),seen=new Set()
  for(const claim of claims){
    if(seen.has(claim.source))continue;seen.add(claim.source)
    const item=document.createElement('article');item.className='source'
    const id=document.createElement('b');id.textContent=claim.id
    const body=document.createElement('div'),link=document.createElement('a'),kind=document.createElement('p')
    link.href=claim.source;link.textContent=claim.claim+' ↗';kind.textContent=claim.type
    body.append(link,kind);item.append(id,body);$('source-list').append(item)
  }
}catch{}
