"""Start a self-contained episode workspace, separate from the personal style library."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

KIT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('destination',type=Path)
    p.add_argument('--example',choices=['clap-sync'])
    p.add_argument('--language',choices=['en','zh'],default='en')
    args=p.parse_args()
    dest=args.destination.resolve()
    style=json.loads((KIT/'style.json').read_text())
    if dest.exists() or dest.is_relative_to(KIT) or 'codex-film-studio' in dest.parts:
        raise SystemExit('Choose a new episode directory outside the style library and Film Studio.')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        work=Path(tmp)/'episode'
        shutil.copytree(KIT/'starter',work,ignore=shutil.ignore_patterns('__pycache__','node_modules','.venv','*.pyc'))
        (work/'content').mkdir(exist_ok=True)
        if args.example:
            if args.language!='en':p.error('The recorded reference episode is English.')
            e=KIT/'examples'/args.example
            shutil.copyfile(e/'episode.json',work/'content/episode.json')
            shutil.copyfile(e/'topic.mjs',work/'src/topic.mjs')
            for d in ('audio','review'):shutil.copytree(e/d,work/d)
        else:
            (work/'content/episode.json').write_text(json.dumps(dict(id=dest.name,title='',language=args.language,chapters=[],shots=[],foley=[],music={}),indent=2)+'\n')
        if args.language == 'en':
            profile = Path('profiles/en-eric-replay.json') if args.example else Path(style['english_audio_profile']).relative_to('starter')
            shutil.copyfile(work/profile,work/'voice-config.json')
        for name in ('guides','reference','baseline'):
            shutil.copytree(KIT/name,work/name)
        shutil.copyfile(KIT/'scripts/restore_baseline.py',work/'scripts/restore_baseline.py')
        shutil.copyfile(KIT/'style.json',work/'style-lock.json')
        (work/'AGENTS.md').write_text('Use guides/production.md, character.md and audio.md. Read guides/evidence.md before adding news, paper, image or footage cutaways; zero inserts is valid. Read voice-config.json for English narration. New English episodes use OpenAI Realtime Cedar. See guides/cedar-workflow.md. Author this episode in this working directory. Use the shared FFmpeg gate. Review the encoded output before delivery.\n')
        dest.mkdir()  # reserve destination exclusively; concurrent initialization cannot overwrite it
        try:
            for child in work.iterdir(): child.rename(dest/child.name)
        except BaseException:
            shutil.rmtree(dest)
            raise
    print(dest)
if __name__=='__main__': main()
