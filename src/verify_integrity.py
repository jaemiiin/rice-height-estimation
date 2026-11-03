"""Verify Git-tracked files, optionally including the downloaded original RGBs."""
from pathlib import Path
import argparse, hashlib, json

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scope',choices=['public','all'],default='public')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];count=0
    entries=json.loads((root/'provenance/file_inventory.json').read_text(encoding='utf-8'))
    if args.scope=='all':
        data=json.loads((root/'provenance/data_files.json').read_text(encoding='utf-8'))
        entries.extend(entry for entry in data if entry['distribution']=='release_archive')
    for entry in entries:
        relative=entry['path'];path=(root/relative).resolve()
        assert path.is_relative_to(root),relative
        if not path.exists():parser.error('Missing '+relative+'; run python tools/download_data.py to obtain the release data.')
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        assert digest.hexdigest()==entry['sha256'],relative
        count+=1
    print(json.dumps(dict(status='PASS',scope=args.scope,files=count)))

if __name__=='__main__':main()
