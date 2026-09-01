#!/usr/bin/env python3
"""Post-seal evaluation; formal exact metric remains locked."""
import argparse, hashlib, json, re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.dev020_residual_rank_refinement_v042b8 import rank
def iou(a,b):
    if not a or not b:return 0.0
    x=max(0,min(a[2],b[2])-max(a[0],b[0])); y=max(0,min(a[3],b[3])-max(a[1],b[1])); z=x*y
    den=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-z
    return z/den if den else 0.0
def gtbox(e):
    if e.get('gt_bbox_xyxy') is not None:return e['gt_bbox_xyxy']
    return json.loads(re.search(r'mapped_object_bbox_display_local=(\[[^]]+\])',e.get('notes','')).group(1))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gt',required=True); ap.add_argument('--session',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    s=Path(a.session); entries=json.loads(Path(a.gt).read_text())['entries']; gt={e['frame_id']:gtbox(e) for e in entries}
    preds={json.loads(x)['frame_id']:json.loads(x) for x in (s/'predictions.jsonl').read_text().splitlines() if x.strip()}; feats={}
    for line in (s/'inference/gt_free_feature_table.jsonl').read_text().splitlines():
        z=json.loads(line); feats.setdefault(z['frame_id'],[]).append(z)
    results={}
    for formula in ['baseline_frozen_h','robust_positive_onset','contrast_coherence']:
        rows=[]
        for idx,e in enumerate(entries):
            if idx==0: continue
            fid=e['frame_id']; p=preds[fid]; cs=json.loads((s/'omni/normalized'/(fid+'.json')).read_text())['candidates']; fs=feats.get(fid,[])
            chosen=p.get('focused_bbox') if formula=='baseline_frozen_h' else (rank(cs,fs,formula)[0]['bbox'] if len(cs)==len(fs) and cs else p.get('focused_bbox'))
            rows.append({'frame_id':fid,'predicted_bbox':chosen,'baseline_bbox':p.get('focused_bbox'),'gt_bbox':gt[fid],'iou':iou(chosen,gt[fid]),'origin':p.get('origin'),'candidate_count':len(cs)})
        results[formula]={'rows':rows,'geometric_correct':sum(x['iou']>=.75 for x in rows),'geometric_top1':f"{sum(x['iou']>=.75 for x in rows)}/28"}
    base=results['baseline_frozen_h']
    for r in results.values():
        r['geometric_regression_vs_baseline']=sum(x['iou']>=.75 and y['iou']<.75 for x,y in zip(base['rows'],r['rows']))
        r['geometric_rescue_vs_baseline']=sum(x['iou']<.75 and y['iou']>=.75 for x,y in zip(base['rows'],r['rows']))
    out={'gt_sha256':hashlib.sha256(Path(a.gt).read_bytes()).hexdigest(),'formal_metric':'FORMAL_LOCKED_EXACT_ROUNDED_6_METRIC unchanged','diagnostic_metric':'LIVE_GEOMETRIC_FOCUS_METRIC_V1 IoU>=0.75','results':results,'acceptance':{'strictly_above_b7_25':any(r['geometric_correct']>25 for r in results.values()),'all_regressions_zero':all(r['geometric_regression_vs_baseline']==0 for r in results.values()),'ten_33_recovery_preserved':results['baseline_frozen_h']['rows'][0]['iou']>=.75},'status':['HISTORICAL_REGRESSION_ONLY','DEVELOPMENT_IN_SAMPLE','POST_HOC_REFINEMENT','NOT_HOLDOUT','NOT_GENERALIZATION_EVIDENCE','PRODUCTION_INTEGRATION_DISABLED']}
    Path(a.output).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
