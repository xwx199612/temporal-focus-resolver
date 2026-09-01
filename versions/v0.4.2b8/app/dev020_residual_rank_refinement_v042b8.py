"""Global deterministic development-only rank projections."""
def clamp(x):
    return max(0.0, min(1.0, float(x or 0.0)))
def score(feature, formula):
    h = float(feature.get('h041b_raw') or 0.0)
    if formula == 'baseline_frozen_h': return h
    if formula == 'robust_positive_onset': return h + .10*clamp(feature.get('positive_onset_support')) - .05*clamp(feature.get('offset_support'))
    if formula == 'contrast_coherence': return h + .05*clamp(feature.get('interior_ring_contrast')) + .05*clamp(feature.get('edge_ring_continuity'))
    raise ValueError(formula)
def rank(candidates, features, formula):
    scored = [(score(f, formula), c) for c, f in zip(candidates, features)]
    return [c for _, c in sorted(scored, key=lambda x: (-x[0], tuple(round(float(v), 6) for v in x[1]['bbox'])))]
