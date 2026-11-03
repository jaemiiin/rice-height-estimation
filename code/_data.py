"""Ground-truth validation and the pinned 92-image GitHub Release download.

The archive contains only original JPEGs; labels remain in data/ground_truth.csv.
"""
from pathlib import Path, PurePosixPath
import csv
import hashlib
import math
import urllib.request
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = 'rice-height-images.zip'
ARCHIVE_URL = 'https://github.com/jaemiiin/rice-height-estimation/releases/download/rice-height-dataset/' + ARCHIVE_NAME
ARCHIVE_SIZE = 649918569
ARCHIVE_SHA256 = 'f0e12041425cfa267a71234c450f15cd91b233019ea3ee4cc42e3893b19387d1'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_ground_truth(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    required = {'image_id', 'filename', 'region', 'acquisition_date', 'acquisition_time',
                'site_date_id', 'shoot_length_cm', 'width', 'height', 'sha256'}
    if len(rows) != 92 or set(rows[0]) != required:
        raise ValueError('Expected the 92-row study ground_truth.csv with its documented columns')
    groups = {}
    filenames = set()
    for row in rows:
        name = PurePosixPath(row['filename'])
        if name.is_absolute() or len(name.parts) != 2 or name.parts[0] != row['region'] or name.suffix != '.jpg' or '\\' in row['filename'] or ':' in row['filename']:
            raise ValueError('Invalid image path in ground truth')
        if name.stem != row['image_id'] or row['filename'] in filenames:
            raise ValueError('Image identifier mismatch or duplicate filename')
        filenames.add(row['filename'])
        date = row['acquisition_date'].replace('-', '')
        stamp = row['image_id'].rsplit('.', 1)[1]
        hour = int(stamp[8:])
        if stamp[:8] != date or row['acquisition_time'] != f'{hour:02d}:00':
            raise ValueError('Filename and acquisition date/time disagree')
        if date not in ['20240615','20240701','20240715','20240801'] or hour not in ([8,9,10] if date == '20240615' else [7,8,9]):
            raise ValueError('Unexpected study acquisition date/time')
        if row['site_date_id'] != row['region'] + '_' + date:
            raise ValueError('Invalid site-date identity')
        height = float(row['shoot_length_cm'])
        if not math.isfinite(height) or height <= 0:
            raise ValueError('Invalid reference height')
        prior = groups.setdefault(row['site_date_id'], height)
        if prior != height:
            raise ValueError('Images from one site-date must share one reference height')
        if (int(row['width']), int(row['height'])) != (3840,2160):
            raise ValueError('Unexpected original image dimensions')
        if len(row['sha256']) != 64 or any(c not in '0123456789abcdef' for c in row['sha256']):
            raise ValueError('Invalid original image checksum')
    if len(groups) != 33 or len({r['region'] for r in rows}) != 9:
        raise ValueError('Expected 33 site-date references in nine regions')
    return rows


def image_path(root, row):
    root = Path(root).resolve()
    target = (root / row['filename']).resolve()
    if root not in target.parents:
        raise ValueError('Image path escapes the selected directory')
    return target


def check_images(root, rows, allow_missing=False):
    present = 0
    for row in rows:
        path = image_path(root, row)
        if path.exists():
            if not path.is_file() or sha256(path) != row['sha256']:
                raise ValueError('Original image checksum mismatch: ' + row['filename'])
            present += 1
        elif not allow_missing:
            raise FileNotFoundError('Missing original image: ' + row['filename'] + '; use run_all.py --download-only')
    return present


def download_images(root, ground_truth, archive=None):
    """Install byte-exact originals without replacing differing local files."""
    rows = load_ground_truth(ground_truth)
    present = check_images(root, rows, allow_missing=True)
    if present == len(rows):
        print('All 92 original images are present and SHA-256 verified.', flush=True)
        return
    if archive is None:
        cache = PROJECT / '.cache'
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / ARCHIVE_NAME
        if not archive.exists():
            partial = archive.with_suffix('.zip.part')
            request = urllib.request.Request(ARCHIVE_URL, headers={'User-Agent':'rice-height-reproduction'})
            total = last = 0
            with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > ARCHIVE_SIZE:
                        raise ValueError('Download exceeds the pinned archive size')
                    output.write(chunk)
                    if total - last >= 64 * 1024 * 1024:
                        print(f'Downloaded {total}/{ARCHIVE_SIZE} bytes', flush=True)
                        last = total
            if total != ARCHIVE_SIZE or sha256(partial) != ARCHIVE_SHA256:
                raise ValueError('Downloaded archive checksum mismatch')
            partial.replace(archive)
    archive = Path(archive)
    if archive.stat().st_size != ARCHIVE_SIZE or sha256(archive) != ARCHIVE_SHA256:
        raise ValueError('Archive size or SHA-256 differs from rice-height-dataset')
    with zipfile.ZipFile(archive) as bundle:
        expected = {'data/images/' + row['filename'] for row in rows}
        if len(bundle.infolist()) != 92 or set(bundle.namelist()) != expected:
            raise ValueError('The archive must contain exactly the 92 original image files')
        # Verify every selected member before installing any new image.
        for row in rows:
            content = bundle.read('data/images/' + row['filename'])
            if hashlib.sha256(content).hexdigest() != row['sha256']:
                raise ValueError('Archived image checksum mismatch: ' + row['filename'])
        for row in rows:
            path = image_path(root, row)
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as output:
                output.write(bundle.read('data/images/' + row['filename']))
    check_images(root, rows)
    print(f'Installed {len(rows)-present} original images; all 92 checksums verified.', flush=True)
