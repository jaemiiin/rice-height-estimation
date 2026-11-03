"""Reproduce the paper from original images using separate pixel/model runtimes."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import time
from _data import PROJECT, download_images, load_ground_truth, check_images


def execute(python, script, *arguments):
    command = [str(python), str(Path(__file__).parent / script), *map(str, arguments)]
    print('Running ' + script, flush=True)
    environment = os.environ.copy()
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
        environment[name] = '1'
    subprocess.run(command, check=True, env=environment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pixels-python', type=Path, help='Python executable in the Python 3.9 pixel environment')
    parser.add_argument('--analysis-python', type=Path, default=Path(sys.executable), help='Python executable in the Python 3.12 analysis environment')
    parser.add_argument('--images', type=Path, default=PROJECT / 'data/images')
    parser.add_argument('--ground-truth', type=Path, default=PROJECT / 'data/ground_truth.csv')
    parser.add_argument('--out', type=Path, default=PROJECT / 'results/main', help='New output directory; existing runs are never replaced')
    parser.add_argument('--download', action='store_true', help='Obtain missing original images before running')
    parser.add_argument('--download-only', action='store_true', help='Obtain and verify original images, then exit; standard library only')
    parser.add_argument('--archive', type=Path, help='Existing Rice Height Dataset ZIP instead of an online download')
    args = parser.parse_args()
    if args.download or args.download_only or args.archive:
        download_images(args.images, args.ground_truth, args.archive)
    if args.download_only:
        return
    if args.pixels_python is None:
        parser.error('--pixels-python is required for full reproduction; see the two-environment installation in README.md')
    check_images(args.images, load_ground_truth(args.ground_truth))
    output = args.out.resolve()
    if output.exists():
        raise FileExistsError('Choose a new output directory: ' + str(output))
    started = time.time()
    # Steps 01 and 02 are applied within step03 for each image. Intermediate
    # full-resolution arrays stay in memory rather than occupying several GB.
    execute(args.pixels_python, 'step03_feature_extraction.py', '--images', args.images.resolve(),
            '--ground-truth', args.ground_truth.resolve(), '--out', output / 'inputs')
    for script in ['step04_feature_selection.py', 'step05_model_fitting.py',
                   'step06_evaluation.py', 'step07_comparisons.py']:
        execute(args.analysis_python, script, '--out', output)
    with (output / 'run_summary.json').open('x', encoding='utf-8') as f:
        json.dump({'status':'PASS','seconds':time.time()-started,'analysis_count':24,
                   'source':'92 original images and ground_truth.csv'}, f, indent=2)
    print('All stages completed; see ' + str(output / 'verification.json'), flush=True)


if __name__ == '__main__':
    main()
