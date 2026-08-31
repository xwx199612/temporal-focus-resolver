"""Canonical encoded-image dual decode for Temporal Focus."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import cv2, numpy as np
@dataclass(frozen=True)
class TemporalFocusImagePlanes:
    rgb: np.ndarray
    gray_e: np.ndarray
    encoded_sha256: str
    encoding: str
    decode_profile: str
    width: int
    height: int
def decode_temporal_focus_image(encoded_image):
    if not isinstance(encoded_image,(bytes,bytearray,memoryview)) or len(encoded_image)==0: raise ValueError('encoded image bytes must be non-empty')
    raw=bytes(encoded_image); buf=np.frombuffer(raw,dtype=np.uint8)
    bgr=cv2.imdecode(buf,cv2.IMREAD_COLOR); gray=cv2.imdecode(buf,cv2.IMREAD_GRAYSCALE)
    if bgr is None or gray is None: raise ValueError('OpenCV could not decode encoded image')
    rgb=np.ascontiguousarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)); gray=np.ascontiguousarray(gray)
    if rgb.shape[:2]!=gray.shape[:2]: raise ValueError('color/gray plane dimensions disagree')
    return TemporalFocusImagePlanes(rgb,gray,hashlib.sha256(raw).hexdigest(),'JPEG/OPENCV','OPENCV_ENCODED_DUAL_DECODE_V1',int(rgb.shape[1]),int(rgb.shape[0]))
