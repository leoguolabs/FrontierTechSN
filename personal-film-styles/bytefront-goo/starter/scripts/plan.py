"""Bind pictures, printed captions, score cues and Foley to the native chapter recordings."""
import hashlib
import math
import re
import wave
from prepare import CONTENT, ROOT, read, write
from validate_evidence import validate as validate_evidence

def plan():
    ep = read(CONTENT/'episode.json')
    jobs = read(CONTENT/'chapters.json')['lines']
    timing = read(CONTENT/'alignment.json')[ep['language']]
    chapters, audio, caps, paragraphs, clocks = [], [], [], {}, {}
    frame = 12
    for ch in ep['chapters']:
        start = frame
        for j in (j for j in jobs if j['logical_chapter'] == ch['id']):
            src = ROOT/'audio/chapters'/(j['id']+'.wav')
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
            with wave.open(str(src)) as f:
                length = math.ceil(f.getnframes()*24/f.getframerate())
            assert sha == read(src.with_suffix('.json'))['audio_sha256']
            clocks[j['id']] = frame
            audio.append(dict(id=j['id'],start=frame, end=frame+length, file=str(src.relative_to(ROOT)), sha256=sha))
            frame += length
        chapters.append(dict(id=ch['id'], title=ch.get('title',ch['id']), start=start, end=frame,
                             activity=ch.get('activity',.65)))
        for p in ch['paragraphs']:
            a = timing[p['id']]
            assert a['audio_sha256']==next(e['sha256'] for e in audio if e['id']==a['chapter_id']), 'Stale word alignment'
            base = clocks[a['chapter_id']]+24*a['source_start']
            chars = a['chars']
            def cue(i):
                return round(base+24*next((c['start'] for c in chars if c['index']>=i),chars[-1]['end']))
            paragraphs[p['id']] = dict(text=p['text'], start=cue(0), end=round(base+24*chars[-1]['end']),
                                        markers={c['index']:cue(c['index']) for c in chars})
            text = p['text']
            tokens = list(re.finditer(r'\S+' if ep['language']=='en' else r'\S',text))
            begin = 0
            for n, token in enumerate(tokens):
                pos = tokens[begin].start()
                if (n == len(tokens)-1 or token.end()-pos >= (59 if ep['language']=='en' else 25)
                        or (token.end()-pos>10 and token.group()[-1] in '.!?。！？')):
                    end = cue(tokens[n+1].start()) if n+1 < len(tokens) else paragraphs[p['id']]['end']
                    caps.append(dict(start=cue(pos),end=end,text=text[pos:token.end()]))
                    begin = n+1
    def anchor(item):
        if 'seconds' in item: return round(24*item['seconds'])
        p = paragraphs[item['paragraph']]
        if 'phrase' not in item: return p['start']
        phrase = item['phrase']
        if not phrase or p['text'].count(phrase)!=1: raise ValueError(f'Missing or ambiguous phrase {phrase}')
        index = p['text'].index(phrase)
        return next(t for i,t in p['markers'].items() if i>=index)
    shots = []
    for s in ep['shots']:
        shots.append(dict(s, start=anchor(s),events={k:anchor(v) for k,v in s.get('events',{}).items()}))
    if shots[0]['paragraph'] != ep['chapters'][0]['paragraphs'][0]['id']:
        raise ValueError('Opening shot must be tied to first paragraph.')
    shots[0]['start'] = 0
    end = frame + 36
    for n,s in enumerate(shots):
        s['end'] = shots[n+1]['start'] if n+1<len(shots) else end
        assert s['start'] < s['end'] and all(s['start']<=f<s['end'] for f in s['events'].values()), s
    for n,c in enumerate(caps):
        if n: caps[n-1]['end']=min(caps[n-1]['end'],c['start'])
    assert all(0<=c['start']<c['end']<=end for c in caps), 'Check ASR cue lengths'
    foley = [dict(f,frame=anchor(f)) for f in ep.get('foley',[])]
    motifs = [anchor(m)/24 for m in ep.get('music',{}).get('motifs',[{'seconds':.4}])]
    assert all(0<=f['frame']<end for f in foley) and all(0<=t<end/24 for t in motifs)
    timeline = dict(language=ep['language'],fps=24,duration_frames=end,chapters=chapters,
          shots=shots,audio=audio,captions=caps,foley=foley,motifs=motifs)
    evidence_review = validate_evidence(timeline, ROOT)
    write(CONTENT/'evidence-review.json', evidence_review)
    write(CONTENT/'timeline.json', timeline)
    media = ROOT/'media'
    media.mkdir(exist_ok=True)
    def stamp(f):
        ms=round(f*1000/24)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
    for ext in ['vtt','srt']:
        cues=[]
        for i,c in enumerate(caps,1):
            ts=f"{stamp(c['start'])} --> {stamp(c['end'])}"
            cues.append((f'{i}\n'+ts.replace('.',',') if ext=='srt' else ts)+'\n'+c['text'])
        (media/('captions.'+ext)).write_text(('WEBVTT\n\n' if ext=='vtt' else '')+'\n\n'.join(cues)+'\n')
    (media/'chapters.txt').write_text('\n'.join(f"{stamp(c['start'] if i else 0)} {c['title']}" for i,c in enumerate(chapters))+'\n')
    print(f'{end} frames, {len(shots)} shots, {len(caps)} captions.')

if __name__ == '__main__': plan()
