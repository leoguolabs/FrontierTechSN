"""A single, through-running electronic score with no resets at chapter boundaries."""
from pathlib import Path
import json, math, random, struct
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'score'
spec=json.loads((S/'design.json').read_text())
film=json.loads((ROOT/'content/timeline.json').read_text())
episode=json.loads((ROOT/'content/episode.json').read_text())
spec.update({k:v for k,v in episode.get('music',{}).items() if k in ('title','bpm','theme_midi','seed')})
assert 48<=spec['bpm']<=168 and 1<=len(spec['theme_midi'])<=5 and all(0<=p<=127 for p in spec['theme_midi'])
T=film['duration_frames']/24
bpm=spec['bpm'];beat=60/bpm;bar_time=4*beat
rng=random.Random(spec['seed'])
chapters=film['chapters'];centres=[(c['start']+c['end'])/48 for c in chapters]
chords={
 'Eb9':(39,[55,58,62,65]), 'Eb6':(39,[55,58,60,65]), 'Cm9':(36,[51,55,58,62]),
 'Ab9':(44,[55,58,60,63]), 'Fm9':(41,[56,60,63,67]), 'Bb6':(46,[55,60,62,65]),
 'Gm7':(43,[53,58,62,65]), 'EbG':(43,[55,58,63,65]), 'Ab6':(44,[53,58,60,63]),
 'BbSus':(46,[56,60,63,65]), 'Cm11':(36,[55,58,62,65])}
progressions=[
 ['Eb9','EbG','Ab9','Bb6','Cm9','Gm7','Ab6','BbSus'],
 ['Cm9','Ab6','EbG','Bb6','Fm9','Cm11','Ab9','BbSus'],
 ['Ab9','Bb6','Cm11','Gm7','Fm9','Ab6','BbSus','Eb6'],
 ['Fm9','Ab9','Cm9','EbG','Ab6','Fm9','BbSus','Bb6'],
 ['Ab6','EbG','Cm9','Gm7','Fm9','Cm11','Ab9','Bb6'],
 ['Eb9','Ab6','Cm11','Gm7','Fm9','EbG','BbSus','Eb6']]
events=[]
parts={'cloud':(0,89),'underflow':(1,39),'current':(2,88),'halo':(3,91),'theme':(4,85),'beat':(9,0)}
def add(part,when,length,pitch,velocity):
    if when>=T-.06 or when<0:return
    events.append(dict(part=part,at=round(when,5),length=round(min(length,T-when),5),
                       pitch=int(pitch),velocity=round(float(velocity),4)))
bars=math.ceil(T/bar_time)
for bar in range(bars):
    at=bar*bar_time
    motion=float(np.interp(at,centres,[c['activity'] for c in chapters]))
    # One harmony spans two bars. The previous pad's decay overlaps the next attack.
    page=(bar//16)%len(progressions)
    name=progressions[page][(bar//2)%8]
    if T-at<2.1*bar_time:name='Eb6'
    root,notes=chords[name]
    if bar%2==0:
        for j,p in enumerate(notes):
            add('cloud',at+.013*j,bar_time*2+.24,p,.52+.06*np.sin(bar*.37+j*.75))
        add('underflow',at,bar_time*(1.23+.14*(1-motion)),root,.64+.06*motion)
        add('underflow',at+bar_time*1.45,bar_time*.51,root+(7 if bar%8 in (2,6) else 12),.43+.08*motion)
    # Alternating octave-inversions share a quarter-eighth grid across the entire film.
    seq=([0,2,1,3],[1,2,0,2],[0,1,3,2],[2,1,0,1])[(bar//2)%4]
    for j,degree in enumerate(seq):
        offset=[.24,1.24,2.24,3.24][j] + (.25 if j==3 and bar%4==3 else 0)
        if motion<.55 and j in (1,3):continue
        pitch=notes[degree]+(12 if (bar%8==6 and j==2) else 0)
        add('current',at+offset*beat,beat*(.55 if j==0 else .34),pitch,
            (.42+.20*motion)*(.94 if j%2==0 else .65))
    if bar%4 in (1,3):
        for j,p in enumerate([notes[1],notes[3]]):
            add('halo',at+beat*(1.4 if bar%4==1 else 2.4)+j*.031,beat*1.8,p+12,.29+.06*motion)
    # The percussion thins under dense arguments. The harmonic bed keeps moving.
    if T-at>6:
        add('beat',at,.30,36,motion*.59)
        if motion>.65:add('beat',at+beat*(2 if bar%4!=3 else 2.5),.24,36,motion*.41)
        if bar%2==1 and motion>.56:add('beat',at+3*beat,.18,38,motion*.46)
        for offset in ([.5,1.5,2.5,3.5] if motion>.79 else [.5,2.5]):
            add('beat',at+offset*beat+rng.uniform(-.006,.008),.10,42,motion*rng.uniform(.29,.39))
# Related but distinct melodic phrases are introduced at visual turns. The grid keeps running.
for start in film['motifs']:
    melody=spec['theme_midi']
    for i,p in enumerate(melody):
        add('theme',start+beat*[0,1,2.7,4.2,5.2][i],beat*(1.9 if i==len(melody)-1 else .85),p,.53 if i in (0,4) else .44)
events.sort(key=lambda e:e['at'])
(S/'arrangement.json').write_text(json.dumps({'title':spec['title'],'seconds':T,'bpm':bpm,'events':events},indent=1))
def vlq(n):
    b=[n&127]
    while n>=128:
        n>>=7;b.append(128|(n&127))
    return bytes(reversed(b))
def tick(t):return round(t/beat*480)
def meta(k,v):return bytes([255,k])+vlq(len(v))+v
def track(msg):
    block=bytearray();last=0
    for now,prior,data in sorted(msg,key=lambda z:(z[0],z[1])):
        block.extend(vlq(now-last)+data);last=now
    block.extend(vlq(max(0,tick(T)-last))+b'\xff\x2f\x00')
    return b'MTrk'+struct.pack('>I',len(block))+block
tracks=[track([(0,0,meta(81,round(60_000_000/bpm).to_bytes(3,'big')))]+
              [(tick(c['start']/24),1,meta(6,c['title'].encode())) for c in chapters])]
for name,(ch,pg) in parts.items():
    msg=[(0,-2,meta(3,name.encode())),(0,-1,bytes([192+ch,pg]))]
    for e in events:
        if e['part']!=name:continue
        on=tick(e['at']);off=max(on+1,tick(e['at']+e['length']))
        msg.extend([(on,1,bytes([144+ch,e['pitch'],round(127*e['velocity'])])),
                    (off,0,bytes([128+ch,e['pitch'],0]))])
    tracks.append(track(msg))
(S/'score.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,1,len(tracks),480)+b''.join(tracks))
print('Composed',len(events),'events across',bars,'unbroken bars.')
