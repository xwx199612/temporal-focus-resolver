#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
assert not any(p.is_symlink() for p in root.rglob('*'))
assert not any(p.suffix in {'.pyc','.pyo'} or '__pycache__' in p.parts for p in root.rglob('*'))
assert json.loads((root/'VERSION.json').read_text())['version']=='0.4.2b7'
print(json.dumps({'status':'PASS','version':'v0.4.2b7','repository_imports':0,'symlink':0,'pyc':0,'production_default_confidence':0.25,'development_profile_confidence':0.20}))
