"""Anonymous, geometry-only adapter for Omni/Omni-derived candidates.

The adapter is intentionally independent of the detector implementation.  It
does not rank, deduplicate, or assign semantic meaning to candidates.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class AnonymousCandidate:
    candidate_id: str
    bbox: tuple[float, float, float, float]
    width: float
    height: float
    area: float
    source: str = "OMNI"

def _bbox(record: dict[str, Any]):
    b = record.get("bbox", record.get("bbox_xyxy_float"))
    if not isinstance(b, (list, tuple)) or len(b) != 4:
        raise ValueError("candidate bbox must be xyxy[4]")
    return tuple(float(v) for v in b)

def normalize_omni_candidates(omni_record: Any, image_width: int, image_height: int) -> list[AnonymousCandidate]:
    """Normalize one Omni frame record without exposing semantic fields."""
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")
    items = omni_record.get("candidates", omni_record.get("containers", omni_record)) if isinstance(omni_record, dict) else omni_record
    if not isinstance(items, list):
        raise ValueError("Omni record must contain a candidate list")
    out = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError("candidate record must be an object")
        x1, y1, x2, y2 = _bbox(item)
        # Historical container artifacts are source-image pixels. Normalized
        # coordinates are accepted for the versioned Omni interchange schema.
        if max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 1.000001:
            x1, x2 = x1 * image_width, x2 * image_width
            y1, y2 = y1 * image_height, y2 * image_height
        if not (0 <= x1 < x2 <= image_width and 0 <= y1 < y2 <= image_height):
            raise ValueError(f"invalid bbox at candidate {i}: {(x1,y1,x2,y2)}")
        w, h = x2 - x1, y2 - y1
        cid = str(item.get("candidate_id", item.get("container_id", f"candidate:{i}")))
        out.append(AnonymousCandidate(cid, (x1, y1, x2, y2), w, h, w*h))
    return out

def scorer_visible(candidate: AnonymousCandidate) -> dict[str, Any]:
    """Return the deliberately semantic-free scorer-facing representation."""
    return asdict(candidate)

__all__ = ["AnonymousCandidate", "normalize_omni_candidates", "scorer_visible"]
