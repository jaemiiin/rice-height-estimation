"""Check the recorded numerical environment without hard-coded machine paths."""
import argparse, importlib, json, os, platform, sys
from pathlib import Path
EXPECTED={'python':'3.12.14','numpy':'2.3.5','pandas':'3.0.1','scipy':'1.18.1','sklearn':'1.9.1'}
def activate():
    for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
    current={'python':platform.python_version()}
    for name in ['numpy','pandas','scipy','sklearn']:current[name]=importlib.import_module(name).__version__
    if current!=EXPECTED:raise RuntimeError(f'Recorded runtime required. Loaded {current}; expected {EXPECTED}. See README.md.')
    return current
if __name__=='__main__':
    print(json.dumps(activate(),indent=2))
