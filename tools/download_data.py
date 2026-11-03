"""Download and verify the approved study-data archive, preserving existing files."""
from pathlib import Path
import argparse, hashlib, json, shutil, urllib.request, zipfile

PROJECT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check_existing(root, entries):
    present = 0
    for entry in entries:
        target = (root / entry['path']).resolve()
        if not target.is_relative_to(root):
            raise ValueError('Data path escapes the selected destination')
        if target.exists():
            if not target.is_file() or target.stat().st_size != entry['bytes'] or sha256(target) != entry['sha256']:
                raise FileExistsError('Refusing to replace differing existing data: ' + entry['path'])
            present += 1
    return present


def obtain(config, cache):
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / config['archive_name']
    if archive.exists():
        return archive
    if not config['archive_url'] or not config['archive_url'].startswith('https://github.com/jaemiiin/rice-height-estimation/releases/download/'):
        raise ValueError('No valid published GitHub Release URL is configured')
    partial = archive.with_suffix(archive.suffix + '.part')
    request = urllib.request.Request(config['archive_url'], headers={'User-Agent': 'rice-height-data-downloader'})
    total = 0
    last = 0
    with urllib.request.urlopen(request, timeout=120) as response, partial.open('wb') as writer:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > config['archive_bytes']:
                raise ValueError('Download is larger than the pinned archive size')
            writer.write(chunk)
            if total - last >= 64 * 1024 * 1024:
                print(f'Downloaded {total}/{config["archive_bytes"]} bytes', flush=True)
                last = total
    if total != config['archive_bytes'] or sha256(partial) != config['archive_sha256']:
        raise ValueError('Downloaded archive failed its size or SHA-256 check')
    if archive.exists():
        raise FileExistsError('Archive appeared during download; refusing to overwrite it')
    partial.replace(archive)
    return archive


def install(archive, root, entries, config):
    if archive.stat().st_size != config['archive_bytes'] or sha256(archive) != config['archive_sha256']:
        raise ValueError('Archive size or SHA-256 does not match the pinned release')
    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        expected = {entry['path']: entry for entry in entries}
        if len(infos) != len(expected) or set(bundle.namelist()) != set(expected):
            raise ValueError('Archive members do not match the approved file manifest')
        for info in infos:
            entry = expected[info.filename]
            if info.is_dir() or info.file_size != entry['bytes'] or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unexpected archive member type or size: ' + info.filename)
            digest = hashlib.sha256()
            with bundle.open(info) as reader:
                for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                    digest.update(chunk)
            if digest.hexdigest() != entry['sha256']:
                raise ValueError('Archive member checksum mismatch: ' + info.filename)
        for entry in entries:
            target = (root / entry['path']).resolve()
            if not target.is_relative_to(root):
                raise ValueError('Unsafe archive destination')
            if target.exists():
                continue  # Existing files were verified before extraction.
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(entry['path']) as reader, target.open('xb') as writer:
                shutil.copyfileobj(reader, writer, 1024 * 1024)
    if check_existing(root, entries) != len(entries):
        raise RuntimeError('Incomplete dataset after extraction')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an already downloaded ZIP instead of the network')
    parser.add_argument('--destination', type=Path, default=PROJECT, help='Repository root receiving data/ and results/reference/')
    parser.add_argument('--cache', type=Path, default=PROJECT / '.local/downloads')
    args = parser.parse_args()
    config = json.loads((PROJECT / 'config/data_release.json').read_text(encoding='utf-8'))
    entries = json.loads((PROJECT / config['file_manifest']).read_text(encoding='utf-8'))
    root = args.destination.resolve()
    root.mkdir(parents=True, exist_ok=True)
    present = check_existing(root, entries)
    if present == len(entries):
        print(json.dumps(dict(status='PASS',files=len(entries),already_present=True)))
        return
    archive = args.archive.resolve() if args.archive else obtain(config, args.cache.resolve())
    install(archive, root, entries, config)
    print(json.dumps(dict(status='PASS',files=len(entries),new_files=len(entries)-present,archive_sha256_verified=True,all_file_hashes_verified=True)))


if __name__ == '__main__':
    main()
