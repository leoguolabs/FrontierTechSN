"""List the explicit project inputs, editable outputs and review evidence to seal."""
import json
from prepare import ROOT

folders = ('content','assets','fonts','src','scripts','tools','guides','reference','baseline',
           'audio','score','review','media','source','profiles')
paths = []
for folder in folders:
    for file in sorted((ROOT/folder).rglob('*')):
        if file.is_symlink():
            raise ValueError(f'Remove linked asset or freeze a local copy: {file}')
        if file.is_file() and not (set(file.parts) & {'__pycache__','.DS_Store'}) and file.suffix!='.pyc':
            paths.append(file.relative_to(ROOT).as_posix())
for file in ('package.json','package-lock.json','requirements-rebuild.txt','requirements-review.txt','style-lock.json','AGENTS.md','PRODUCTION.md'):
    if not (ROOT/file).is_file(): raise FileNotFoundError(file)
    paths.append(file)
if (ROOT/'voice-config.json').exists():paths.append('voice-config.json')
lock=json.loads((ROOT/'style-lock.json').read_text())
print(json.dumps(dict(style=lock['id'],version=lock['version'],working_directories=['media','review'],files=paths),indent=2))
