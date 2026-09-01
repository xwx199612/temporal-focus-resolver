#!/usr/bin/env python3
"""Small, dependency-free audit helpers for the v0.4.2b4 release."""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path

PROVENANCE = {
    "frozen": "FROZEN_V041G6_OMNI_DERIVED_REFERENCE",
    "b2": "LIVE_V042B2_PRODUCTION_REPLAY",
    "b3": "LIVE_V042B3_PRODUCTION_REPLAY",
    "b4": "LIVE_V042B4_PRODUCTION_REPLAY",
}

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_json(path): return json.loads(Path(path).read_text())
def bbox(c): return [float(x) for x in (c.get("bbox") or c.get("focused_bbox"))]
def area(b): return max(0., b[2]-b[0])*max(0., b[3]-b[1])
def iou(a,b):
    x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3])
    inter=max(0.,x2-x1)*max(0.,y2-y1); den=area(a)+area(b)-inter
    return inter/den if den else 0.
def center_distance(a,b):
    return math.hypot((a[0]+a[2]-b[0]-b[2])/2.,(a[1]+a[3]-b[1]-b[3])/2.)
def candidates(path):
    x=read_json(path); return x.get("candidates",x.get("anonymous_candidates",[]))
def frame_map(root):
    root=Path(root); return {p.name.removesuffix('.json'): candidates(p) for p in sorted(root.glob('*.json'))}
def match_one_to_one(left,right,threshold=0.5):
    pairs=[]; used=set()
    for li,l in enumerate(left):
        best=max(((iou(bbox(l),bbox(r)),ri) for ri,r in enumerate(right) if ri not in used), default=(0.,None))
        if best[1] is not None and best[0] >= threshold: pairs.append((li,best[1],best[0])); used.add(best[1])
    return pairs
def lineage(left_root,right_root,left_provenance,right_provenance,source_paths,threshold=.5):
    L,R=frame_map(left_root),frame_map(right_root); frames=sorted(set(L)|set(R))
    rows=[]; all_iou=[]; all_disp=[]
    for f in frames:
        l,r=L.get(f,[]),R.get(f,[]); row={"frame_id":f,"left_count":len(l),"right_count":len(r),"delta":len(r)-len(l)}
        row["exact_normalized_bbox_multiset_equal"]=sorted([bbox(x) for x in l])==sorted([bbox(x) for x in r])
        for t in (.50,.90,.99): row[f"iou_{t:.2f}"] = len(match_one_to_one(l,r,t))
        row["exact_bbox_matches"]=len(match_one_to_one(l,r,1.0))
        pairs=match_one_to_one(l,r,threshold); row["matched_pairs"]=len(pairs); row["unmatched_left"]=len(l)-len(pairs); row["unmatched_right"]=len(r)-len(pairs)
        row["matched_ious"]=[round(x[2],8) for x in pairs]; row["center_displacements"]=[round(center_distance(bbox(l[a]),bbox(r[b])),6) for a,b,_ in pairs]
        all_iou += [x[2] for x in pairs]; all_disp += [center_distance(bbox(l[a]),bbox(r[b])) for a,b,_ in pairs]; rows.append(row)
    def med(x):
        x=sorted(x); return x[len(x)//2] if x else None
    return {"comparison_id":left_provenance+"__VS__"+right_provenance,"left_provenance":left_provenance,"right_provenance":right_provenance,"source_artifacts":source_paths,"frame_count":len(frames),"frames":rows,"matching":{"method":"greedy frame-local one-to-one geometry matching; candidate index is never identity","threshold_iou":threshold,"aggregate_matched":len(all_iou),"mean_matched_iou":sum(all_iou)/len(all_iou) if all_iou else None,"median_matched_iou":med(all_iou),"mean_center_displacement_px":sum(all_disp)/len(all_disp) if all_disp else None,"median_center_displacement_px":med(all_disp)},"candidate_universe_verdict":"REPLAY_PARITY" if all(x["left_count"]==x["right_count"] and x["exact_normalized_bbox_multiset_equal"] for x in rows) else "CANDIDATE_UNIVERSE_CHANGED","replay_parity_legal":all(x["exact_normalized_bbox_multiset_equal"] for x in rows),"limitations":"Geometry comparison is frame-local; it proves neither semantic identity nor pre-NMS equivalence."}
def write_jsonl(path,rows):
    Path(path).write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows))
def feature_rows(session):
    s=Path(session); preds=[json.loads(x) for x in (s/'predictions.jsonl').read_text().splitlines() if x.strip()]; rows=[]
    for p in preds:
        cs=candidates(s/'omni/normalized'/(p['frame_id']+'.json'))
        for rank,c in enumerate(cs,1):
            h=c.get('h041b',{}) if isinstance(c,dict) else {}
            rows.append({'frame_id':p['frame_id'],'candidate_id':c.get('candidate_id'),'bbox':c.get('bbox'),'area':area(c['bbox']),'compactness':h.get('compactness'),'containment_depth':h.get('containment_depth'),'H_RAW':h.get('raw_score'),'H_DENSITY':h.get('density'),'H_VALID_FRACTION':h.get('valid_fraction'),'H_FINAL':h.get('score'),'H_COMPONENT_RANK':rank,'E_RAW':None,'E_PHYSICAL_ELIGIBLE':None,'E_COMPONENT_RANK':None,'DIRECTIONAL_COMPONENT_RANK':None,'final_authority_trace':p.get('authority_trace',p.get('origin')),'winner':c.get('candidate_id')==p.get('predicted_candidate_id'),'runner_up_margin':p.get('runner_up_margin'),'previous_patch_statistics':None,'current_patch_statistics':None,'GT_FREE':True})
    return rows
