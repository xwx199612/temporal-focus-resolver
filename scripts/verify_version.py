#!/usr/bin/env python3
from pathlib import Path
r=Path(__file__).parents[1]; v=(r/"CURRENT_VERSION").read_text().strip(); assert (r/"versions"/v).is_dir(); print(v)
