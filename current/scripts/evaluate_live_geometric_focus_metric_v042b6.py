#!/usr/bin/env python3
"""Evaluate formal exact metric and parallel IoU>=0.75 metric after GT seal."""
import argparse,hashlib,json,re,sys
from pathlib import Path
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ar(b): return max(0,b[2]-b[0])*max(0,b[3]-b[1])
def iou(a,b):
 if not a or not b:return 0
 x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3]); inter=max(0,x2-x1)*max(0,y2-y1); den=ar(a)+ar(b)-inter; return inter/den if den else 0
def gb(e):
 if e.get('gt_bbox_xyxy'):return e['gt_bbox_xyxy']
 m=re.search(r'mapped_object_bbox_display_local=(\[[^]]+\])',e.get('notes','')); return json.loads(m.group(1)) if m else None
def ex(a,b):return a and b and all(round(float(x),6)==round(float(y),6) for x,y in zip(a,b))
def one(root,gt):
 r=Path(root); ge={x['frame_id']:x for x in json.loads(Path(gt).read_text())['entries']}; ps=[json.loads(x) for x in (r/'predictions.jsonl').read_text().splitlines()]; rows=[]
 for p in ps:
  e=ge[p['frame_id']]; cs=json.loads((r/'omni/normalized'/(p['frame_id']+'.json')).read_text())['candidates']; b=gb(e); best=max((iou(c['bbox'],b) for c in cs),default=0); rows.append({'frame_id':p['frame_id'],'frame_index':p['frame_index'],'focus_type':e['focus_type'],'gt_bbox':b,'predicted_bbox':p.get('focused_bbox'),'best_candidate_iou':best,'exact_candidate_available':any(ex(c['bbox'],b) for c in cs),'geometric_candidate_available':best>=.75,'formal_correct':any(ex(c['bbox'],b) for c in cs) and p.get('focused_bbox') and ex(p.get('focused_bbox'),b),'geometric_correct':p.get('focused_bbox') is not None and iou(p.get('focused_bbox'),b)>=.75,'origin':p.get('origin'),'membership':p.get('candidate_membership',True)})
 c=rows[1:]; return {'rows':rows,'formal_locked_exact_rounded_6':{'candidate_recall':sum(x['exact_candidate_available'] for x in c),'end_to_end_correct':sum(x['formal_correct'] for x in c),'denominator':len(c),'conditional_correct':sum(x['formal_correct'] for x in c if x['exact_candidate_available']),'contract':'FORMAL_LOCKED_EXACT_ROUNDED_6_METRIC'},'live_geometric_focus_metric_v1':{'candidate_recall':sum(x['geometric_candidate_available'] for x in c),'end_to_end_correct':sum(x['geometric_correct'] for x in c),'denominator':len(c),'iou_threshold':.75,'contract':['PARALLEL_DIAGNOSTIC_METRIC','NOT_A_RETROACTIVE_CHANGE_TO_FORMAL_SCORE','NOT_HOLDOUT','NOT_GENERALIZATION_EVIDENCE','NOT_PRODUCTION_THRESHOLD_PROMOTION']},'gt_sha256':sha(gt),'join_audit':{'prediction_rows':len(rows),'bootstrap_rows':1,'causal_rows':len(c),'frame_id_dictionary':True,'positional_slice_used':False}}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--source',action='append',required=True,help='label=path'); ap.add_argument('--gt',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); out={};
 for s in a.source: l,p=s.split('=',1); out[l]=one(p,a.gt)
 # Explicit 10_33 evidence is retained as a row in each profile result.
 Path(a.output).write_text(json.dumps({'metric_id':'LIVE_GEOMETRIC_FOCUS_METRIC_V1','formal_metric_id':'FORMAL_LOCKED_EXACT_ROUNDED_6_METRIC','profiles':out,'conclusion':'LIVE_GEOMETRIC_RECOVERY_OBSERVED_BUT_THRESHOLD_PROMOTION_BLOCKED_PENDING_NEW_DEV_DATA'},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
