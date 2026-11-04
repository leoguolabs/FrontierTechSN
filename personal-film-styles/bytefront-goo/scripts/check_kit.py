"""Verify all shipped inputs and references against the relative-path SHA-256 inventory."""
import hashlib
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
index=root/'inventory.json'
def inventory():
    paths=sorted(p for p in root.rglob('*') if p.is_file() and p!=index and
                 not any(s in {'.git','.DS_Store','__pycache__'} for s in p.relative_to(root).parts))
    if any(p.is_symlink() for p in paths): raise ValueError('Unexpected symlink')
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
current=inventory()
if sys.argv[1:]==['--update']:
    index.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n')
else:
    expected=json.loads(index.read_text())
    changed=[p for p in sorted(current.keys()|expected.keys()) if current.get(p)!=expected.get(p)]
    if changed:raise SystemExit('Kit differs: '+', '.join(changed))
print(f'{len(current)} files verified' if sys.argv[1:]!=['--update'] else f'Indexed {len(current)} files')
