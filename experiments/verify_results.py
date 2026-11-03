"""Verify supplied features and independently re-score stored predictions."""
from pathlib import Path
import argparse, os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results'); p.add_argument('--reference-root'); p.add_argument('--data-root')
    p.add_argument('--report'); p.add_argument('--spatial', action='store_true')
    a = p.parse_args()
    if a.data_root: os.environ['RICE_HEIGHT_DATA_ROOT'] = str(Path(a.data_root).resolve())
    if a.reference_root: os.environ['RICE_HEIGHT_REFERENCE_ROOT'] = str(Path(a.reference_root).resolve())
    from runtime_check import activate
    activate()
    if a.spatial:
        from verify_spatial_records import verify
        result = verify()
    else:
        from verify_results import verify
        result = verify(a.results, a.reference_root)
    if a.report:
        from common import js
        js(result, a.report)
    print(json.dumps({k:v for k,v in result.items() if k not in ['metrics','inputs','checked']}, indent=2))

if __name__ == '__main__': main()
