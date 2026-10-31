"""
Let the tests in subfolders import the helpers here (`paths.py` and `timing.py`), and draw plots without a display
"""
import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
os.environ.setdefault('SCIRIS_BACKEND', 'agg')
os.environ.setdefault('STARSIM_UNCOMPILED_WARNING', '0')
os.environ.setdefault('JAX_PLATFORMS', 'cpu') # Many test workers can't share one GPU
