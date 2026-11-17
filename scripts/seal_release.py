"""Refresh release fingerprints after intentionally regenerating and reviewing data."""
import hashlib
from common import ROOT,write_json
paths=[]
for folder in [ROOT/'public/data',ROOT/'research']:
    paths.extend(p for p in folder.rglob('*') if p.is_file() and p.name!='release-hashes.json')
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
write_json(ROOT/'research/release-hashes.json',manifest)
print('Sealed',len(manifest),'research and public data artifacts')
