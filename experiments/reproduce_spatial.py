"""Refit one or all of the archived 71 spatial sensitivity conditions."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from run_spatial import main
if __name__ == '__main__': main()
