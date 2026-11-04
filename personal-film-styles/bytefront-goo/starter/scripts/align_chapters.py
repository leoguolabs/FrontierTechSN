"""Align continuous chapter recordings, retaining the provider's native PCM and prosody."""
from pathlib import Path
import hashlib,json,time,wave
import numpy as np
from scipy.signal import resample_poly
from word_alignment import aligned

root=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
chapters=read(root/'content/chapters.json')['lines']
lines={l['id']:l for l in read(root/'content/narration.json')['lines']}
lang=read(root/'content/episode.json')['language']
data={}
for ch in chapters:
    key=ch['id'];src=root/'audio/chapters'/(key+'.wav');receipt=src.with_suffix('.json')
    if not receipt.is_file(): raise FileNotFoundError(f'Missing chapter receipt {receipt}')
    job=read(receipt);digest=hashlib.sha256(src.read_bytes()).hexdigest()
    assert job['audio_sha256']==digest and job['request']['text']==ch['text']
    if lang=='en': assert job['request']==dict(text=ch['text'],voice='am_eric',speed=1.,language='en-us')
    else: assert job['provider']=='Volcengine' and job['request']['language']=='zh'
    with wave.open(str(src)) as f:
        rate=f.getframerate()
        assert (f.getnchannels(),f.getsampwidth())==(1,2) and (lang!='en' or rate==24000)
        pcm=np.frombuffer(f.readframes(f.getnframes()),'<i2')
    asr_path=root/'review/asr/chapters'/(key+'.json')
    asr_path.parent.mkdir(parents=True,exist_ok=True)
    if asr_path.exists() and read(asr_path)['sha256']==digest:
        asr=read(asr_path)
    else:
        import mlx_whisper
        signal=resample_poly(pcm.astype(np.float32)/32768.,16000,rate).astype(np.float32)
        result=mlx_whisper.transcribe(signal,path_or_hf_repo='mlx-community/whisper-large-v3-turbo-q4',language=lang,temperature=0,condition_on_previous_text=False,word_timestamps=True,verbose=False)
        words=[w for seg in result['segments'] for w in seg['words']]
        asr={'sha256':digest,'text':result['text'],'words':words}
        asr_path.write_text(json.dumps(asr,indent=2,ensure_ascii=False))
    chars,score=aligned(ch['text'],asr['words'])
    offset=0
    for pid in ch['paragraph_ids']:
        txt=lines[pid]['text']
        assert ch['text'][offset:offset+len(txt)]==txt
        cc=[dict(c,index=c['index']-offset) for c in chars if offset<=c['index']<offset+len(txt)]
        ratio=sum(c['matched'] for c in cc)/len(cc)
        assert ratio>.82,(pid,ratio,asr['text'])
        start=max(0,cc[0]['start']);end=min(len(pcm)/rate,cc[-1]['end'])
        assert 0<=start<end
        for c in cc:
            c['start']=max(0,c['start']-start)
            c['end']=max(0,c['end']-start)
        data[pid]={'id':pid,'chapter_id':key,'source_start':start,'source_end':end,'chars':cc,'match_ratio':ratio}
        offset+=len(txt)+1
    print(key,round(len(pcm)/rate,2),round(score,3),flush=True)
(root/'content/alignment.json').write_text(json.dumps({lang:data},indent=2,ensure_ascii=False))
