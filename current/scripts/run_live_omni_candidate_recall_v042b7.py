#!/usr/bin/env python3
"""Explicit-profile live replay. 0.20 is never an implicit provider default."""
import argparse, json, os, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
PROFILES={"production_reference_025":(0.25,"FORMAL_PRODUCTION_REFERENCE"),"dev_candidate_recall_020":(0.20,"DEVELOPMENT_CANDIDATE_RECALL_PROFILE")}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--profile",choices=sorted(PROFILES),required=True); p.add_argument("--image-root",required=True); p.add_argument("--output",required=True); p.add_argument("--omni-root",required=True); p.add_argument("--checkpoint",required=True); a=p.parse_args()
    conf,status=PROFILES[a.profile]; out=Path(a.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    cmd=[sys.executable,str(HERE/"scripts/run_live_omni_confidence_frontier_v042b5.py"),"--image-root",a.image_root,"--output",str(out),"--omni-root",a.omni_root,"--checkpoint",a.checkpoint,"--confidence",str(conf)]
    subprocess.run(cmd,check=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    for fn in ("run_manifest.json","session_manifest.json"):
        q=out/fn; obj=json.loads(q.read_text()); obj.update({"version":"v0.4.2b7","profile":a.profile,"profile_status":status,"development_profile_explicit":True,"historical_status":["HISTORICAL_REGRESSION_ONLY","DEVELOPMENT_IN_SAMPLE","POST_HOC_CANDIDATE_POLICY_REFINEMENT","NOT_HOLDOUT","NOT_GENERALIZATION_EVIDENCE","PRODUCTION_INTEGRATION_DISABLED"]}); q.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (out/"audit/profile_lock.json").write_text(json.dumps({"profile":a.profile,"confidence":conf,"imgsz":640,"nms_iou":0.70,"status":status,"production_default_confidence":0.25,"explicit_profile_required":True,"sweep_candidates_used_for_prediction":False if conf!=0.25 else True},sort_keys=True,indent=2)+"\n")
if __name__=="__main__": main()
