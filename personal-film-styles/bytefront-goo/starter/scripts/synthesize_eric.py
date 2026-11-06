"""Submit the film's exact paragraphs to Kokoro and save its unaltered WAVs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.error

def digest(data):
    return hashlib.sha256(data).hexdigest()

def synthesize(lines, endpoint, save):
    headers = {'Authorization': 'Bearer '+os.environ['KOKORO_API_KEY'], 'Content-Type':'application/json'}
    def call(path, payload=None, binary=False):
        body = None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
        request = urllib.request.Request(endpoint+path, data=body, headers=headers)
        with urllib.request.urlopen(request, timeout=40) as response:
            result = response.read()
        return result if binary else json.loads(result)
    capabilities=call('/v1/capabilities')
    assert 'am_eric' in call('/v1/voices')['voices']
    save('capabilities.json',json.dumps(capabilities,indent=2).encode())
    for line in lines:
        text=line['text']
        assert digest(text.encode())==line['text_sha256']
        payload={'text':text,'voice':'am_eric','language':'en-us','speed':1.0}
        for attempt in range(10):
            try:
                job=call('/v1/jobs',dict(payload,cache=True))
                break
            except urllib.error.HTTPError as error:
                if error.code!=429 or attempt==9:raise
                time.sleep(int(error.headers.get('Retry-After',10)))
        deadline=time.monotonic()+600
        while job['status'] in ('queued','running') and time.monotonic()<deadline:
            time.sleep(.45)
            job=call('/v1/jobs/'+job['id'])
        assert job['status']=='completed' and job['request']==payload, (line['id'],job['status'])
        audio=call('/v1/jobs/'+job['id']+'/audio',binary=True)
        assert digest(audio)==job['audio_sha256'] and len(audio)==job['bytes']
        save(line['id']+'.wav',audio)
        save(line['id']+'.json',json.dumps(job,indent=2,ensure_ascii=False).encode())
        print(line['id'],round(job['duration_seconds'],2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--endpoint',default='http://10.60.11.3:8094')
    parser.add_argument('--relay',help='Session-local restricted receipt collector')
    opts=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    profile=json.loads((root/'voice-config.json').read_text())
    if profile.get('profile_id')!='legacy-kokoro-eric':
        raise SystemExit('Eric is a historical replay option. Current English default is Tim; use guides/tim-workflow.md.')
    if opts.relay:
        with urllib.request.urlopen(opts.relay+'/lines',timeout=20) as response:
            lines=json.load(response)
        def save(name,data):
            req=urllib.request.Request(opts.relay+'/'+name,data=data,method='PUT')
            with urllib.request.urlopen(req,timeout=30) as response: response.read()
    else:
        root=Path(__file__).resolve().parents[1]
        assert json.loads((root/'content/episode.json').read_text())['language']=='en'
        lines=json.loads((root/'content/chapters.json').read_text())['lines']
        out=root/'audio/chapters'
        out.mkdir(parents=True,exist_ok=True)
        def save(name,data):
            p=out/name
            q=p.with_suffix(p.suffix+'.part')
            q.write_bytes(data)
            q.replace(p)
    synthesize(lines,opts.endpoint,save)
