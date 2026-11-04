"""Rebuild a single-language episode from its current script, verified audio and scenes."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from prepare import ROOT, CONTENT, read
sys.path.insert(0,str(ROOT/'tools/frame_review'))
from ffmpeg_gate import run

def build():
    p = argparse.ArgumentParser()
    p.add_argument('--width',type=int,choices=[960,1920,3840],default=3840)
    p.add_argument('--output',default='media/master.mp4')
    p.add_argument('--encoder',choices=['libx264','h264_videotoolbox'],default='h264_videotoolbox' if sys.platform=='darwin' else 'libx264')
    args=p.parse_args()
    target=(ROOT/args.output).resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists(): raise FileExistsError(target)
    for step in ('prepare','align_chapters','plan','compose_parallel','render_parallel_music','mix_parallel'):
        subprocess.run([sys.executable,str(ROOT/'scripts'/(step+'.py'))],cwd=ROOT,check=True)
    total=read(CONTENT/'timeline.json')['duration_frames']
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        draft=Path(tmp)/'encode.mp4'
        producer=subprocess.Popen(['node',str(ROOT/'scripts/draw.mjs'),str(args.width)],stdout=subprocess.PIPE,cwd=ROOT)
        try:
            run(['-nostdin','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgba',
                 '-video_size',f'{args.width}x{args.width*9//16}','-framerate','24','-i','pipe:0',
                 '-i',str(ROOT/'audio/mix.wav'),'-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p',
                 '-c:v',args.encoder,'-b:v','26M' if args.width==3840 else '5M','-g','48',
                 '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
                 '-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-movflags','+faststart',str(draft)],
                 stdin=producer.stdout)
        finally:
            producer.stdout.close()
            if producer.wait()!=0: raise RuntimeError('Picture renderer failed')
        import json
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(draft)]))
        v=next(s for s in info['streams'] if s['codec_type']=='video')
        a=next(s for s in info['streams'] if s['codec_type']=='audio')
        assert int(v['nb_frames'])==total and v['width']==args.width and abs(float(a['duration'])-total/24)<1/24
        os.link(draft,target)
    print(target)

if __name__=='__main__': build()
