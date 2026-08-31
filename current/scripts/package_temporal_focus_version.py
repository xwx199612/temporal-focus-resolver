#!/usr/bin/env python3
"""b5-local release package entrypoint."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).parents[1]/'release_manifest.py'),run_name='__main__')
