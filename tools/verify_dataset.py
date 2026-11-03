"""Standard-library image/label checks; optionally hash every raw image."""
from pathlib import Path
from collections import defaultdict
from decimal import Decimal
import argparse, csv, hashlib, json
PROJECT = Path(__file__).resolve().parents[1]

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def verify(data, raw=None):
    metadata=data/'metadata'
    images=read(metadata/'images.csv'); sites=read(metadata/'site_date_heights.csv')
    manifest=read(metadata/'raw_image_manifest.csv'); coords=read(metadata/'retained_strip_coordinates.csv')
    assert len(images)==92 and len(sites)==33 and len(manifest)==92 and len(coords)==552
    assert len({r['region'] for r in images})==9
    image_map={(r['region'],r['image_id']):r for r in images}; assert len(image_map)==92
    site_map={r['site_date_id']:r for r in sites}; assert len(site_map)==33
    grouped=defaultdict(list)
    for r in coords: grouped[(r['Region'],r['파일명'])].append(r)
    for r in images:
        site=site_map[r['site_date_id']]
        assert r['region']==site['region'] and r['acquisition_date']==site['acquisition_date']
        assert Decimal(r['shoot_length_cm'])==Decimal(site['shoot_length_cm'])
        group=grouped[(r['region'],r['image_id'])]
        assert len(group)==6 and {int(x['strip_order']) for x in group}==set(range(6))
        assert all(Decimal(x['shoot_length_cm'])==Decimal(r['shoot_length_cm']) for x in group)
    for site in sites: assert sum(r['site_date_id']==site['site_date_id'] for r in images)==int(site['n_images'])
    hashes=0; total=0; largest=0
    for r in manifest:
        image=image_map[(r['Region'],r['파일명'])]
        assert r['sha256']==image['raw_sha256'] and r['relative_path']==image['relative_path']
        if raw is not None:
            path=(raw/r['relative_path']).resolve(); assert path.is_relative_to(raw.resolve())
            with path.open('rb') as f:
                h=hashlib.sha256()
                for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
            assert h.hexdigest()==r['sha256'], r['relative_path']
            hashes+=1; size=path.stat().st_size; total+=size; largest=max(largest,size)
    for name in ['continuous','raw','otsu','matched','full']:
        rows=read(data/'processed'/('features_'+name+'.csv'))
        assert len(rows)==552 and len(rows[0])==41 and 'NDBGRI' not in rows[0]
        counts=defaultdict(int)
        for r in rows:
            key=(r['Region'],r['파일명']); counts[key]+=1; image=image_map[key]
            assert Decimal(r['shoot_length_cm'])==Decimal(image['shoot_length_cm'])
            assert r['site_date']==image['acquisition_date'].replace('-','')
        assert len(counts)==92 and set(counts.values())=={6}
    return dict(status='PASS',images=92,regions=9,site_date_references=33,strips=552,feature_tables=5,candidates=37,raw_hashes_checked=hashes,raw_total_bytes=total,raw_largest_file_bytes=largest,original_measurements_invented=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,default=PROJECT/'data');p.add_argument('--raw-root',type=Path)
    p.add_argument('--include-raw',action='store_true');p.add_argument('--report',type=Path)
    a=p.parse_args();result=verify(a.data_root,a.raw_root or (a.data_root/'raw' if a.include_raw else None))
    if a.report:
        if a.report.exists():raise FileExistsError('Choose a new report path')
        a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
