#!/usr/bin/env python3
"""GT-after-seal paired evaluation; exact metric remains frozen, .75 is diagnostic."""
import argparse, json, math, hashlib, re, statistics
from pathlib import Path
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ar(b): return max(0.,b[2]-b[0])*max(0.,b[3]-b[1])
def iou(a,b):
 if not a or not b:return 0.
 x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3]); z=max(0,x2-x1)*max(0,y2-y1); return z/(ar(a)+ar(b)-z) if ar(a)+ar(b)>z else 0
def cen(a,b): return math.hypot((a[0]+a[2]-b[0]-b[2])/2,(a[1]+a[3]-b[1]-b[3])/2)
def exact(a,b): return a is not None and b is not None and all(round(float(x),6)==round(float(y),6) for x,y in zip(a,b))
def gtbox(e):
 if e.get('gt_bbox_xyxy') is not None:return e['gt_bbox_xyxy']
 m=re.search(r'mapped_object_bbox_display_local=(\[[^]]+\])',e.get('notes','')); return json.loads(m.group(1))
def read(root,entries):
 root=Path(root); ps=[json.loads(x) for x in (root/'predictions.jsonl').read_text().splitlines() if x.strip()]; rows=[]
 for p in ps:
  e=entries[p['frame_id']]; cs=json.loads((root/'omni/normalized'/f"{p['frame_id']}.json").read_text())['candidates']; g=gtbox(e); vals=[(iou(c['bbox'],g),c) for c in cs]; best=max(vals,key=lambda x:x[0],default=(0,None)); ex=[c for c in cs if exact(c['bbox'],g)]
  rows.append({'frame_id':p['frame_id'],'focus_type':e['focus_type'],'gt_bbox':g,'predicted_bbox':p.get('focused_bbox'),'predicted_candidate_id':p.get('focused_candidate_id'),'candidate_count':len(cs),'membership':p.get('candidate_membership',True),'origin':p.get('origin'),'exact_mapped':len(ex)==1,'gt_candidate_id':ex[0]['candidate_id'] if len(ex)==1 else None,'best_iou':best[0],'best_bbox':best[1]['bbox'] if best[1] else None,'best_confidence':best[1].get('confidence') if best[1] else None,'best_center_px':cen(best[1]['bbox'],g) if best[1] else None})
 return rows
def metrics(rows,t):
 c=rows[1:]; mapped=[r for r in c if (r['exact_mapped'] if t==1 else r['best_iou']>=t)]; correct=sum(iou(r['predicted_bbox'],r['gt_bbox'])>=t for r in c if r['predicted_bbox']); return {'causal_denominator':len(c),'mapped':len(mapped),'recall':len(mapped)/len(c),'correct':correct,'accuracy':correct/len(c),'conditional_correct':sum(iou(r['predicted_bbox'],r['gt_bbox'])>=t for r in mapped if r['predicted_bbox']),'conditional_accuracy':sum(iou(r['predicted_bbox'],r['gt_bbox'])>=t for r in mapped if r['predicted_bbox'])/len(mapped) if mapped else None,'contract':'FORMAL_LOCKED_EXACT_ROUNDED_6_METRIC' if t==1 else 'PARALLEL_DIAGNOSTIC_METRIC; NOT_A_RETROACTIVE_CHANGE_TO_FORMAL_SCORE'}
def pairs(a,b):
 out=[]
 for x,y in zip(a[1:],b[1:]):
  # Geometry comparison is frame-local greedy matching by IoU, never candidate index.
  ca=json.loads((Path(A)/'omni/normalized'/f"{x['frame_id']}.json").read_text())['candidates']; cb=json.loads((Path(B)/'omni/normalized'/f"{y['frame_id']}.json").read_text())['candidates']; used=set(); ms=[]
  for i,u in enumerate(ca):
   opts=sorted(((iou(u['bbox'],v['bbox']),j) for j,v in enumerate(cb) if j not in used),reverse=True)
   if opts and opts[0][0]>=.5: used.add(opts[0][1]); ms.append(opts[0][0])
  out.append({'frame_id':x['frame_id'],'production_count':len(ca),'dev_count':len(cb),'delta':len(cb)-len(ca),'matched_iou_050':sum(z>=.5 for z in ms),'matched_iou_090':sum(z>=.9 for z in ms),'matched_iou_099':sum(z>=.99 for z in ms),'mean_matched_iou':statistics.mean(ms) if ms else None,'added_count':max(0,len(cb)-len(ca)),'removed_or_shifted_count':max(0,len(ca)-len(cb))})
 return out
def main():
 global A,B
 p=argparse.ArgumentParser(); p.add_argument('--gt',required=True); p.add_argument('--production',required=True); p.add_argument('--development',required=True); p.add_argument('--output',required=True); a=p.parse_args(); A,B=a.production,a.development; entries={e['frame_id']:e for e in json.loads(Path(a.gt).read_text())['entries']}; pr=read(A,entries); dv=read(B,entries); comparison=pairs(pr,dv); out={'status':['HISTORICAL_REGRESSION_ONLY','DEVELOPMENT_IN_SAMPLE','POST_HOC_CANDIDATE_POLICY_REFINEMENT','NOT_HOLDOUT','NOT_GENERALIZATION_EVIDENCE','PRODUCTION_INTEGRATION_DISABLED'],'gt_sha256':sha(a.gt),'profiles':{'production_reference_025':{'rows':pr,'metrics':{str(t):metrics(pr,t) for t in (1,.5,.75,.9)}},'dev_candidate_recall_020':{'rows':dv,'metrics':{str(t):metrics(dv,t) for t in (1,.5,.75,.9)}}},'paired_geometry':comparison,'paired_aggregate':{'candidate_delta_total':sum(x['delta'] for x in comparison),'changed_final_winner_count':sum(x['production_count']!=x['dev_count'] for x in comparison)},'10_33_17':{'production':next(x for x in pr if '10_33_17' in x['frame_id']),'development':next(x for x in dv if '10_33_17' in x['frame_id'])},'formal_contract':'FORMAL_B4_LOCKED_METRIC unchanged'}; Path(a.output).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
if __name__=='__main__':main()
