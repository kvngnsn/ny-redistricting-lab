"""Shared paths and reproducible, checksummed public-source downloads."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
PUBLIC = ROOT / 'public' / 'data'
CACHE.mkdir(exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)

def fetch(name, url):
    path = CACHE / name
    if not path.exists():
        tmp = path.with_suffix(path.suffix + '.part')
        print('Downloading', name, flush=True)
        with urllib.request.urlopen(url, timeout=120) as response, tmp.open('wb') as out:
            while True:
                chunk = response.read(2**20)
                if not chunk:
                    break
                out.write(chunk)
        tmp.replace(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(2**20), b''):
            digest.update(chunk)
    record = {'file': name, 'url': url, 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
    lock = ROOT / 'research' / 'sources.lock.json'
    if lock.exists():
        expected = json.loads(lock.read_text()).get(name)
        if expected is None or expected['sha256'] != record['sha256'] or expected['url'] != url:
            raise ValueError(f'Source fingerprint mismatch for {name}; review the source update explicitly.')
    manifest = CACHE / 'downloads.json'
    entries = json.loads(manifest.read_text()) if manifest.exists() else {}
    entries[name] = record
    manifest.write_text(json.dumps(entries, indent=2) + '\n')
    return path

def write_json(path, obj):
    path.write_text(json.dumps(obj, separators=(',', ':'), allow_nan=False) + '\n')
