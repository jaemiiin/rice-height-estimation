"""Locations relative to this project; optional roots are provided by the caller."""
from pathlib import Path
import os
PACKAGE = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('RICE_HEIGHT_DATA_ROOT', str(PACKAGE / 'data'))).resolve()
INPUTS = DATA / 'processed'
METADATA = DATA / 'metadata'
REFERENCE = Path(os.environ.get('RICE_HEIGHT_REFERENCE_ROOT', str(PACKAGE / 'results/reference'))).resolve()
SPATIAL_INPUTS = INPUTS / 'spatial'
SPATIAL_METADATA = METADATA / 'spatial'
SPATIAL_REFERENCE = REFERENCE / 'spatial'
