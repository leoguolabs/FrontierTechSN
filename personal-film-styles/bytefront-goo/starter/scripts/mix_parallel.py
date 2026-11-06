"""Mix the new score against the frozen chapter performance and picture-synchronous Foley."""
from pathlib import Path
import hashlib
import json
import math
import wave
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.ndimage import maximum_filter1d
import pyloudnorm as pyln

ROOT=Path(__file__).resolve().parents[1]
timeline=json.loads((ROOT/'content/timeline.json').read_text())
N=timeline['duration_frames']*2000
SR=48000

def read(path):
    with wave.open(str(path)) as w:
        return w.getframerate(),np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,w.getnchannels()).astype(np.float32)/32768
def write(path,x):
    assert np.max(np.abs(x))<1
    with wave.open(str(path),'wb') as out:
        out.setparams((1 if x.ndim==1 else x.shape[1],2,SR,0,'NONE','not compressed'))
        out.writeframes(np.rint(x*32767).astype('<i2').tobytes())
def loud(x):
    return float(pyln.Meter(12000).integrated_loudness(resample_poly(x,1,4,axis=0).astype(np.float64)))
def amp(db):return 10**(db/20)

profile_path=ROOT/'voice-config.json'
profile=json.loads(profile_path.read_text()) if profile_path.exists() else {}
target=profile.get('chapter_balance_lufs')
levels=[]
voice=np.zeros(N,np.float32)
for event in timeline['audio']:
    path=ROOT/event['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==event['sha256']
    rate,wav=read(path)
    assert wav.shape[1]==1
    speech=resample_poly(wav[:,0],SR,rate).astype(np.float32)
    at=event['start']*2000
    native_lufs=loud(speech)
    if not math.isfinite(native_lufs):raise ValueError('Silent/invalid narration: '+event['file'])
    gain_db=0.0 if target is None else float(target)-native_lufs
    gain=amp(gain_db)
    voice[at:at+len(speech)]+=speech*.55*gain
    levels.append({'id':event['id'],'file':event['file'],'audio_sha256':event['sha256'],'input_lufs':native_lufs,'fixed_gain_db':gain_db,'balanced_lufs_before_bus':native_lufs+gain_db})
(ROOT/'review').mkdir(exist_ok=True)
(ROOT/'review/dialogue-levels.json').write_text(json.dumps({'target_lufs':target,'method':'One constant gain per full chapter; no time changes','chapters':levels},indent=2))
write(ROOT/'audio/voice.wav',voice)
from foley import render_foley
effects=render_foley(timeline,N,SR)
write(ROOT/'audio/effects.wav',effects)
track=np.zeros((N//2,2),np.float32)
for part in ['cloud','underflow','current','halo','theme','beat']:
    rate,stem=read(ROOT/'score/stems'/(part+'.wav'))
    assert rate==24000 and len(stem)==len(track)
    track+=stem
# Gentle low cut for sub-energy and a broad dip around consonants.
track=sosfilt(butter(2,39,'highpass',fs=24000,output='sos'),track,axis=0).astype(np.float32)
presence=sosfilt(butter(2,[1250,3400],'bandpass',fs=24000,output='sos'),track,axis=0).astype(np.float32)
track-=.26*presence
music=resample_poly(track,2,1,axis=0).astype(np.float32)
del track,presence,stem
# The understated score uses one stable gain, avoiding level surges at speech boundaries.
dialog_lufs=loud(voice)
music*=amp((dialog_lufs-18.0)-loud(music))
write(ROOT/'audio/music.wav',music)
mix=music+effects+voice[:,None]/np.sqrt(np.float32(2))
master_gain=amp(-16-loud(mix))
mix*=master_gain
block=48
peaks=np.max(np.pad(np.max(np.abs(mix),axis=1),(0,(-N)%block)).reshape(-1,block),axis=1)
future=maximum_filter1d(peaks,size=7,mode='nearest')
ceiling=amp(-1.65)
reduction=np.minimum(1,ceiling/np.maximum(1e-8,future))
g=1.;curve=np.empty_like(reduction)
for i,target in enumerate(reduction):
    g=min(target,g+(1-g)*.012)
    curve[i]=g
for i in range(0,N,SR*20):
    end=min(i+SR*20,N)
    mix[i:end]*=np.interp(np.arange(i,end),np.arange(len(curve))*block,curve)[:,None]
write(ROOT/'audio/mix.wav',mix)
evidence={'new_score':json.loads((ROOT/'content/episode.json').read_text()).get('music',{}).get('title','Continuous electronic study'),'seconds':N/SR,'native_chapter_hashes_verified':True,
    'dialogue_bus_before_master_lufs':dialog_lufs,'music_bus_before_master_lufs':loud(music),
    'music_relative_dialogue_lu':loud(music)-dialog_lufs,'integrated_mix_lufs':loud(mix),
    'sample_peak_dbfs':20*math.log10(np.abs(mix).max()),'master_gain_db':20*math.log10(master_gain),
    'max_limiter_reduction_db':float(-20*np.log10(curve.min()))}
(ROOT/'review/music-mix.json').write_text(json.dumps(evidence,indent=2))
print(evidence)
