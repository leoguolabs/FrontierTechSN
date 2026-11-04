'use strict';
const data=JSON.parse(document.getElementById('catalog').textContent);
const voices=data.voices,audio=document.getElementById('audio');
const $=id=>document.getElementById(id);
const playIcon='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5 13 8l-9 5.5Z" fill="currentColor"/></svg>';
const pauseIcon='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 3h3v10H4zm5 0h3v10H9z" fill="currentColor"/></svg>';
let filter='all',current=null,visible=voices;
const format=s=>Number.isFinite(s)?`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`:'0:00';
$('sample-text').textContent=data.sample_text;
$('main-play').innerHTML=playIcon;
if(location.protocol==='file:') $('all-download').hidden=true;
function render(){
const q=$('search').value.trim().toLowerCase();visible=voices.filter(v=>(filter==='all'||(v.category||v.id.slice(0,2))===filter)&&(`${v.id} ${v.name} ${v.accent||''} ${v.gender||''}`).toLowerCase().includes(q));
$('results-count').textContent=`${visible.length} 个音色`;$('sequence').disabled=visible.length===0;
$('grid').replaceChildren();
if(!visible.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='没有找到匹配的音色。';$('grid').append(empty);}
visible.forEach(v=>{
const card=document.createElement('article');card.className='voice';card.dataset.voice=v.id;
const top=document.createElement('div');top.className='voice-top';
const idx=document.createElement('span');idx.className='index';idx.textContent=`${String(voices.indexOf(v)+1).padStart(2,'0')} / ${v.language.toUpperCase()}`;
const button=document.createElement('button');button.className='play-card';button.dataset.play=v.id;button.setAttribute('aria-label',`播放 ${v.name} ${v.id}`);button.innerHTML=playIcon;button.onclick=()=>select(v.id);
top.append(idx,button);
const heading=document.createElement('h2');heading.className='name';heading.textContent=v.name;
const id=document.createElement('div');id.className='voice-id';id.textContent=v.id;
const wave=document.createElement('div');wave.className='wave';wave.setAttribute('aria-hidden','true');v.waveform.forEach(level=>{const bar=document.createElement('i');bar.style.height=`${Math.max(2,level*34)}px`;wave.append(bar)});
const bottom=document.createElement('div');bottom.className='voice-bottom';const meta=document.createElement('span');meta.className='meta';meta.textContent=[v.accent,v.gender,`${v.duration_seconds.toFixed(1)}s`].filter(Boolean).join(' · ');
const download=document.createElement('a');download.className='wav-download';download.href=v.file;download.download=`${v.id}.wav`;download.textContent='WAV ↓';download.setAttribute('aria-label',`下载 ${v.name} WAV`);bottom.append(meta,download);
card.append(top,heading,id,wave,bottom);$('grid').append(card);
});sync();
}
function sync(){
document.querySelectorAll('.voice').forEach(card=>{const on=card.dataset.voice===current;card.classList.toggle('is-current',on);const button=card.querySelector('button');button.innerHTML=on&&!audio.paused?pauseIcon:playIcon;button.setAttribute('aria-label',`${on&&!audio.paused?'暂停':'播放'} ${card.dataset.voice}`);});
$('main-play').innerHTML=audio.paused?playIcon:pauseIcon;$('main-play').setAttribute('aria-label',audio.paused?'播放':'暂停');
const at=visible.findIndex(v=>v.id===current);$('previous').disabled=!current||at<=0;$('next').disabled=!current||at<0||at>=visible.length-1;
}
async function select(id){
if(current===id){if(audio.paused){if(audio.ended)audio.currentTime=0;await audio.play().catch(failed)}else audio.pause();sync();return;}
const voice=voices.find(v=>v.id===id);if(!voice)return;
document.body.classList.add('has-player');
audio.pause();current=id;$('now-name').textContent=voice.name;$('now-id').textContent=id;$('status').textContent='';$('elapsed').textContent='0:00';$('duration').textContent=format(voice.duration_seconds);$('main-play').disabled=false;$('seek').disabled=false;$('seek').value=0;audio.src=voice.file;audio.load();sync();await audio.play().catch(failed);
}
function failed(){ $('status').textContent='播放未开始，请点击播放按钮重试。';sync();}
document.querySelectorAll('.filter').forEach(button=>button.onclick=()=>{filter=button.dataset.filter;document.querySelectorAll('.filter').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));render();});
$('search').oninput=render;
$('sequence').onclick=()=>{if(!visible.length)return;$('continuous').checked=true;if(current===visible[0].id){audio.currentTime=0;audio.play().catch(failed);}else select(visible[0].id)};
$('main-play').onclick=()=>{if(current)select(current)};
$('previous').onclick=()=>{const i=visible.findIndex(v=>v.id===current);if(i>0)select(visible[i-1].id)};
$('next').onclick=()=>{const i=visible.findIndex(v=>v.id===current);if(i>=0&&i<visible.length-1)select(visible[i+1].id)};
$('seek').oninput=()=>{if(Number.isFinite(audio.duration)&&audio.duration>0)audio.currentTime=Number($('seek').value)/1000*audio.duration;};
audio.addEventListener('loadedmetadata',()=>{$('duration').textContent=format(audio.duration)});
audio.addEventListener('timeupdate',()=>{$('elapsed').textContent=format(audio.currentTime);$('seek').value=audio.duration?Math.round(audio.currentTime/audio.duration*1000):0});
audio.addEventListener('play',sync);audio.addEventListener('pause',sync);
audio.addEventListener('error',()=>{$('status').textContent='音频读取失败，请检查 audio 文件夹是否与页面放在一起。';sync()});
audio.addEventListener('ended',()=>{sync();if($('continuous').checked){const i=visible.findIndex(v=>v.id===current);if(i>=0&&i<visible.length-1)select(visible[i+1].id);else $('status').textContent='本组音色已全部播放。';}});
render();
