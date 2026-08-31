#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vlm_distill.temporal_focus_image_input_v1 import decode_temporal_focus_image
from vlm_distill.temporal_focus_resolver_v041g6 import resolve_temporal_focus_encoded
print('encoded temporal-focus standalone loaded')
