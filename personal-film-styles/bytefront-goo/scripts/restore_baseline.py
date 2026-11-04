"""Verify and restore the sealed Math in AI source package without executing it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

KIT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('archive',type=Path)
p.add_argument('destination',type=Path)
a=p.parse_args()
dst=a.destination.resolve()
if dst.exists() or dst.is_relative_to(KIT): raise SystemExit('Destination must be a new external directory.')
record=json.loads((KIT/'baseline/archive-check.json').read_text())
with a.archive.open('rb') as f:
    h=hashlib.sha256()
    for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
if h.hexdigest()!=record['sha256']: raise ValueError('Incorrect sealed ZIP digest')
dst.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.archive) as z, tempfile.TemporaryDirectory(dir=dst.parent) as tmp:
    names=z.namelist()
    prefix='math-in-ai-goo-v29/'
    for item in z.infolist():
        parts=PurePosixPath(item.filename).parts
        if (not item.filename.startswith(prefix) or '..' in parts or '\\' in item.filename
                or stat.S_ISLNK(item.external_attr>>16)):
            raise ValueError(item.filename)
    manifest=json.loads(z.read(prefix+'PACKAGE-MANIFEST.json'))
    expected=manifest['files']
    assert manifest['revision']=='v29' and len(expected)==record['payload_files']
    assert len(set(names))==len(names) and set(names)=={prefix+n for n in [*expected,'PACKAGE-MANIFEST.json']}
    root=Path(tmp)/'restore';root.mkdir()
    for name,entry in expected.items():
        out=root/name
        out.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256()
        with z.open(prefix+name) as inp,out.open('xb') as f:
            for block in iter(lambda:inp.read(1048576),b''):
                f.write(block);h.update(block)
        assert out.stat().st_size==entry['bytes'] and h.hexdigest()==entry['sha256'],name
    (root/'PACKAGE-MANIFEST.json').write_bytes(z.read(prefix+'PACKAGE-MANIFEST.json'))
    dst.mkdir()
    try:
        for child in root.iterdir():child.rename(dst/child.name)
    except BaseException:
        shutil.rmtree(dst)
        raise
print(f'Restored {len(expected)} verified files into {dst}')
