"""Verify project file hashes, optionally including permission-pending data."""
from pathlib import Path
import argparse, hashlib, json

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scope',choices=['public','all'],default='public')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];count=0
    entries=json.loads((root/'provenance/file_inventory.json').read_text(encoding='utf-8'))
    if args.scope=='all':
        local_inventory=root/'.local/provenance/data_inventory.json'
        if not local_inventory.exists():
            parser.error('The full-data scope requires the authors\' local data inventory and authorized data. A public clone contains code/documentation only; use --scope public.')
        entries+=json.loads(local_inventory.read_text(encoding='utf-8'))
    for entry in entries:
        if args.scope=='public' and entry['release_status']!='code_or_documentation_candidate':continue
        relative=entry['path'];path=(root/relative).resolve()
        assert path.is_relative_to(root),relative
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        assert digest.hexdigest()==entry['sha256'],relative
        count+=1
    print(json.dumps(dict(status='PASS',scope=args.scope,files=count)))

if __name__=='__main__':main()
