"""Parallel, GT-free directional H onset/offset specialist (v0.4.1g).

This module is deliberately data-free: callers provide the sealed H/E roles and
candidate rows.  It cannot access GT, focus type, frame names, or production
state.  It is not imported by the production endpoint.
"""
POLARITY_THRESHOLD = 0.80
COMPACTNESS_THRESHOLD = 0.70
SIGNED_EVIDENCE_FLOOR = 32.0

def compactness(candidate):
    w, h = float(candidate["width"]), float(candidate["height"])
    if not (w > 0 and h > 0):
        return None
    return min(w, h) / max(w, h)

def choose_positive_proposal(candidates):
    eligible = [c for c in candidates if c.get("h041b_rank", 10**9) <= 3 and c.get("transition", {}).get("valid") is True]
    if not eligible:
        return None
    return max(eligible, key=lambda c: (float(c["transition"].get("positive_luma_mass", float("-inf"))), -int(c["h041b_rank"]), -int(c["container_index"])))

def arbitrate(row, *, polarity_threshold=POLARITY_THRESHOLD, compactness_threshold=COMPACTNESS_THRESHOLD, signed_evidence_floor=SIGNED_EVIDENCE_FLOOR):
    """Return a prediction from one frame's GT-free candidates and sealed roles."""
    if row["bootstrap"]:
        return {"winner": row["baseline"], "origin": "TEMPORAL_BOOTSTRAP_UNAVAILABLE", "intervention": False, "reason": "BOOTSTRAP_UNCHANGED"}
    if row["e_intervention"]:
        return {"winner": row["baseline"], "origin": "V041E_BASELINE_PRESERVED", "intervention": False, "reason": "E_AUTHORITY_PROTECTED"}
    if row["baseline"] != row["h_winner"]:
        return {"winner": row["baseline"], "origin": "V041E_BASELINE_PRESERVED", "intervention": False, "reason": "NON_E_BASELINE_ROLE_MISMATCH"}
    winner = row["winner_candidate"]
    proposal = choose_positive_proposal(row["candidates"])
    if proposal is None:
        return {"winner": row["baseline"], "origin": "V041E_BASELINE_PRESERVED", "intervention": False, "reason": "PROPOSAL_UNAVAILABLE"}
    wc, pc = winner.get("transition", {}), proposal.get("transition", {})
    checks = {
        "winner_valid": wc.get("valid") is True,
        "winner_negative_polarity": wc.get("luma_polarity_balance", 0) <= -polarity_threshold,
        "winner_negative_floor": wc.get("negative_luma_mass", 0) >= signed_evidence_floor,
        "winner_negative_dominant": wc.get("negative_luma_mass", 0) > wc.get("positive_luma_mass", 0),
        "proposal_valid": pc.get("valid") is True,
        "proposal_positive_polarity": pc.get("luma_polarity_balance", 0) >= polarity_threshold,
        "proposal_positive_floor": pc.get("positive_luma_mass", 0) >= signed_evidence_floor,
        "proposal_positive_dominant": pc.get("positive_luma_mass", 0) > pc.get("negative_luma_mass", 0),
        "reciprocal_positive": pc.get("positive_luma_mass", 0) > wc.get("positive_luma_mass", 0),
        "reciprocal_negative": wc.get("negative_luma_mass", 0) > pc.get("negative_luma_mass", 0),
        "compactness_valid": compactness(proposal) is not None,
        "noncompact_scope": compactness(proposal) is not None and compactness(proposal) < compactness_threshold,
        "proposal_distinct": proposal["container_index"] != winner["container_index"],
    }
    if all(checks.values()):
        return {"winner": proposal, "origin": "V041G_DIRECTIONAL_H_ONSET_RESCUE", "intervention": True, "reason": "DIRECTIONAL_GATE_PASS", "proposal": proposal, "checks": checks}
    failed = next(k for k, v in checks.items() if not v)
    return {"winner": row["baseline"], "origin": "V041E_BASELINE_PRESERVED", "intervention": False, "reason": failed.upper(), "proposal": proposal, "checks": checks}
