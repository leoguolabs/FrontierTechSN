"""Stereo custom synth render for Parallel Lines. Returns and envelopes span scene cuts."""
from pathlib import Path
import json,math,wave
import numpy as np
from scipy.signal import butter,sosfilt

root=Path(__file__).resolve().parents[1];score=root/'score'
spec=json.loads((score/'design.json').read_text());arr=json.loads((score/'arrangement.json').read_text())
spec['seed']=json.loads((root/'content/episode.json').read_text()).get('music',{}).get('seed',spec['seed'])
sr=spec['sample_rate'];count=round(sr*arr['seconds']);rng=np.random.default_rng(spec['seed']);tau=2*np.pi
stems=score/'stems';stems.mkdir(exist_ok=True)
def excite(e):
    part=e['part'];v=e['velocity'];length=e['length']
    release={'cloud':.63,'underflow':.26,'current':.28,'halo':.55,'theme':.42,'beat':.09}[part]
    t=np.arange(round((length+4.8*release)*sr))/sr
    pitch=e['pitch'];f=440*2**((pitch-69)/12)
    def envelope(attack):
        return (1-np.exp(-t/attack))*np.exp(-np.maximum(0,t-length)/release)
    slow=t+e['at']
    phase=tau*f*t
    if part=='cloud':
        channels=[]
        for sign in [-1,1]:
            det=tau*f*(1+sign*.0016)*t+.40*np.sin(tau*.12*slow+sign*.7)
            core=.46*np.sin(phase+.14*np.sin(tau*.082*slow))+.37*np.sin(det)
            cloud=core+.13*np.sin(2*det+.31)+.065*np.sin(3*det+.6)
            channels.append(cloud*envelope(.38)*(.92+.08*np.sin(tau*.075*slow+sign*.3))*.39*v)
        return np.stack(channels,axis=1)
    if part=='underflow':
        shape=np.sin(phase)+.39*np.sin(2*phase+.12)+.19*np.sin(3*phase+.4)+.085*np.sin(4*phase)
        x=np.tanh(1.18*shape)*envelope(.048)*(.76+.24*np.exp(-t/.40))*.55*v;pan=0
    elif part=='current':
        colour=.34+1.1*np.exp(-t/.16)
        x=(np.sin(phase+colour*np.sin(phase*1.001))+ .17*np.sin(2*phase+.08))*envelope(.026)*np.exp(-t/.62)*.33*v
        pan=.31*np.sin(.69*e['at'])
    elif part=='halo':
        x=(np.sin(phase+.64*np.exp(-t/.3)*np.sin(2*phase))+.14*np.sin(phase*1.003))*envelope(.18)*np.exp(-t/1.1)*.23*v;pan=.27
    elif part=='theme':
        # Rounded, unhurried portamento and a slightly wider release than the sequencer.
        p=phase-.75*(1-np.exp(-t/.032))+.12*np.sin(tau*3.7*t)*np.minimum(1,t/.5)
        x=(np.sin(p)+.24*np.sin(2*p+.28)+.095*np.sin(3*p))*envelope(.055)*(.57+.43*np.exp(-t/.75))*.44*v;pan=-.12
    else:
        noise=rng.normal(size=len(t))
        if pitch==36:
            p=tau*(48*t+48*.032*(1-np.exp(-t/.032)))
            x=(np.sin(p)+.15*np.sin(2*p))*np.exp(-t/.12)*.73;pan=0
        elif pitch==38:
            x=sosfilt(butter(2,[600,3200],btype='bandpass',fs=sr,output='sos'),noise)
            x=(.31*x+.21*np.sin(tau*167*t))*np.exp(-t/.063)*.56;pan=-.18
        else:
            x=sosfilt(butter(2,[3200,6200],btype='bandpass',fs=sr,output='sos'),noise)*np.exp(-t/.043)*.26;pan=.30
        x=x*v*np.minimum(1,t/.008)
    return np.stack([x*np.sqrt((1-pan)/2),x*np.sqrt((1+pan)/2)],axis=1)
def wav(path,x):
    assert np.max(np.abs(x))<.999
    with wave.open(str(path),'wb') as w:
        w.setparams((2,2,sr,0,'NONE','not compressed'));w.writeframes(np.rint(x*32767).astype('<i2').tobytes())
for part in ['cloud','underflow','current','halo','theme','beat']:
    bus=np.zeros((count,2),np.float32)
    events=[e for e in arr['events'] if e['part']==part]
    for e in events:
        at=round(e['at']*sr);x=excite(e);n=min(len(x),count-at)
        bus[at:at+n]+=x[:n].astype(np.float32)
    if part in ['cloud','current','halo','theme']:
        room=sosfilt(butter(2,2600,fs=sr,output='sos'),bus,axis=0).astype(np.float32)
        taps=[(.034,.09),(.087,.072),(.153,.052),(.245,.042),(.377,.027)]
        if part in ('current','theme','halo'):
            beat=60/spec['bpm']
            taps.extend([(beat*.75,.17),(beat*1.5,.095),(beat*2.25,.046)])
        for i,(dt,gain) in enumerate(taps):
            delay=round(dt*sr)
            bus[delay:]+=room[:-delay,::-1 if i%2==0 else 1]*gain
    # Only the ends of the entire piece fade. Chapter boundaries share the same tails.
    attack=round(.46*sr);release=round(1.65*sr)
    bus[:attack]*=np.linspace(0,1,attack)[:,None];bus[-release:]*=np.linspace(1,0,release)[:,None]
    wav(stems/(part+'.wav'),bus);print(part,len(events),flush=True)
