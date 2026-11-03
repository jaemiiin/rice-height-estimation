"""Re-extract the five recorded feature matrices from the original 92 RGB files."""
from pathlib import Path
import argparse, os, sys, platform
sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-root', type=Path)
    parser.add_argument('--data-root', type=Path, default=PROJECT / 'data')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.limit is not None and (args.limit < 1 or not args.verify_only):
        parser.error('--limit must be positive and is only for --verify-only sampling')
    os.environ['RICE_HEIGHT_DATA_ROOT'] = str(args.data_root.resolve())
    import numpy, pandas, scipy, cv2
    actual = dict(python=platform.python_version(), numpy=numpy.__version__, pandas=pandas.__version__, scipy=scipy.__version__, opencv=cv2.__version__)
    expected = dict(python='3.9.18', numpy='1.26.4', pandas='2.1.4', scipy='1.13.1', opencv='4.11.0')
    if actual != expected:
        raise RuntimeError('Use the separate recorded pixel environment: ' + str(expected) + '; loaded ' + str(actual))
    from feature_extraction import extract
    extract(args.raw_root or args.data_root / 'raw', args.out, args.verify_only, args.limit)

if __name__ == '__main__': main()
