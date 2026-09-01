#!/usr/bin/env python3
"""GT-after-seal evaluator for the locked confidence frontier."""
from __future__ import annotations
import argparse, hashlib, json, math, re, statistics
from pathlib import Path
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def area(b): return max(0.,b[2]-b[0])*max(0.,b[3]-b[1])
def iou(a,b):
    if not a or not b:return 0.
    x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3]); inter=max(0.,x2-x1)*max(0.,y2-y1); den=area(a)+area(b)-inter; return inter/den if den else 0.
def center(a,b): return math.hypot((a[0]+a[2]-b[0]-b[2])/2,(a[1]+a[3]-b[1]-b[3])/2)
def gtbox(e):
    if e.get('gt_bbox_xyxy'): return e['gt_bbox_xyxy']
    m=re.search(r'mapped_object_bbox_display_local=(\[[^]]+\])',e.get('notes','')); return json.loads(m.group(1)) if m else None
def exact(a,b): return a and b and all(round(float(x),6)==round(float(y),6) for x,y in zip(a,b))
def match(left,right,t=.5):
    used=set(); pairs=[]
    for i,a in enumerate(left):
        choices=sorted(((iou(a['bbox'],b['bbox']),j) for j,b in enumerate(right) if j not in used),reverse=True)
        if choices and choices[0][0]>=t: pairs.append((i,choices[0][1],choices[0][0])); used.add(choices[0][1])
    return pairs
def profile(root,gt):
    root=Path(root); entries={x['frame_id']:x for x in json.loads(Path(gt).read_text())['entries']}; preds=[json.loads(x) for x in (root/'predictions.jsonl').read_text().splitlines() if x.strip()]; rows=[]
    for p in preds:
        e=entries[p['frame_id']]; cs=json.loads((root/'omni/normalized'/(p['frame_id']+'.json')).read_text())['candidates']; gb=gtbox(e); scores=[iou(c['bbox'],gb) for c in cs] if gb else []
        exacts=[c for c in cs if exact(c['bbox'],gb)]; rows.append({'frame_id':p['frame_id'],'frame_index':p['frame_index'],'focus_type':e['focus_type'],'gt_bbox':gb,'predicted_bbox':p.get('focused_bbox'),'predicted_candidate_id':p.get('focused_candidate_id'),'candidate_count':len(cs),'origin':p.get('origin'),'membership':p.get('candidate_membership',True),'exact_mapped':len(exacts)==1,'ambiguous':len(exacts)>1,'gt_candidate_id':exacts[0]['candidate_id'] if len(exacts)==1 else None,'best_iou':max(scores,default=0.),'best_center_px':center(cs[scores.index(max(scores))]['bbox'],gb) if scores and max(scores)>0 else None})
    causal=rows[1:]; n=len(causal); out={'rows':rows,'metrics':{}}
    for threshold,name in [(1.0,'exact'),(.50,'iou_050'),(.75,'iou_075'),(.90,'iou_090')]:
        mapped=[x for x in causal if x['exact_mapped']] if threshold==1.0 else [x for x in causal if x['best_iou']>=threshold]
        correct=sum(1 for x in mapped if x['predicted_bbox'] and iou(x['predicted_bbox'],x['gt_bbox'])>=threshold)
        out['metrics'][name]={'mapping_criterion':'EXACT_ROUNDED_6' if threshold==1.0 else f'GT_BBOX_IOU_GE_{threshold:.2f}','mapped':len(mapped),'recall':len(mapped)/n,'end_to_end_correct':correct,'end_to_end_accuracy':correct/n,'conditional_correct':correct,'conditional_accuracy':correct/len(mapped) if mapped else None,'diagnostic_contract':'FORMAL_B4_LOCKED_METRIC' if threshold==1.0 else 'DIAGNOSTIC_ONLY_MAPPING_CONTRACT; NOT_A_RETROACTIVE_CHANGE_TO_FORMAL_B4_SCORE'}
    by={}
    for x in causal:
        d=by.setdefault(x['focus_type'],{'denominator':0,'correct':0}); d['denominator']+=1; d['correct']+=int(x['exact_mapped'] and x['predicted_bbox'] is not None and x['predicted_bbox']==x['gt_bbox'])
    for d in by.values(): d['accuracy']=d['correct']/d['denominator'] if d['denominator'] else None
    out['by_focus_type']=by; out['join_audit']={'prediction_rows':len(rows),'bootstrap_rows':1,'causal_prediction_rows':n,'gt_rows':len(entries),'causal_gt_rows':len(entries)-1,'duplicate_prediction_ids':len(rows)-len({x['frame_id'] for x in rows}),'duplicate_gt_ids':len(entries)-len(set(entries)),'frame_id_set_equality':set(entries)=={x['frame_id'] for x in rows},'first_causal_frame_included':rows[1]['frame_id']}; out['gt_sha256']=sha(gt); return out
def compare(base,diag):
    b=base['rows'][1:]; d=diag['rows'][1:]; bm={x['frame_id']:x for x in b}; dm={x['frame_id']:x for x in d}; out={'frames':[]}
    for f in sorted(bm):
        x,y=bm[f],dm[f]; out['frames'].append({'frame_id':f,'production_count':x['candidate_count'],'diagnostic_count':y['candidate_count'],'candidate_count_delta':y['candidate_count']-x['candidate_count'],'production_best_iou':x['best_iou'],'diagnostic_best_iou':y['best_iou'],'added_candidate_count':max(0,y['candidate_count']-x['candidate_count']),'removed_or_shifted_candidate_count':max(0,x['candidate_count']-y['candidate_count']),'predicted_bbox_changed':x['predicted_bbox']!=y['predicted_bbox'],'production_correct':x['exact_mapped'] and x['predicted_bbox']==x['gt_bbox'],'diagnostic_correct':y['exact_mapped'] and y['predicted_bbox']==y['gt_bbox']})
    def count(k): return sum(x[k] for x in out['frames'])
    out['aggregate']={'frame_count':len(out['frames']),'candidate_count_delta_total':sum(x['candidate_count_delta'] for x in out['frames']),'changed_final_winner_count':count('predicted_bbox_changed'),'formal_correct_preserved':sum(1 for x in out['frames'] if x['production_correct'] and x['diagnostic_correct']),'valid_rescue':sum(1 for x in out['frames'] if not x['production_correct'] and x['diagnostic_correct']),'regression':sum(1 for x in out['frames'] if x['production_correct'] and not x['diagnostic_correct']),'both_wrong':sum(1 for x in out['frames'] if not x['production_correct'] and not x['diagnostic_correct']),'H_winner_change_count':None,'H_correct_to_wrong':None,'H_wrong_to_correct':None,'E_eligible_intervention_counts':'see per-profile component trace','directional_counts':'see per-profile component trace'}; return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gt',required=True); ap.add_argument('--production',required=True); ap.add_argument('--diagnostic',action='append',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); roots=[Path(a.production)]+[Path(x) for x in a.diagnostic]; results={str(r):profile(r,a.gt) for r in roots}; base=results[str(Path(a.production))]; out={'formal_protocol':'FORMAL_B4_LOCKED_METRIC','diagnostic_contract':'DIAGNOSTIC_ONLY_MAPPING_CONTRACT; NOT_A_RETROACTIVE_CHANGE_TO_FORMAL_B4_SCORE','profiles':{r.name:results[str(r)] for r in roots},'comparisons':{r.name:compare(base,results[str(r)]) for r in roots[1:]},'gt_sha256':sha(a.gt),'sealed_hash_reverification':{str(r):{'predictions':sha(r/'predictions.jsonl'),'prediction_seal':json.loads((r/'inference/prediction_seal.json').read_text())['prediction_sha256'],'protocol':sha(r/'evaluation/evaluation_protocol.json'),'protocol_seal':json.loads((r/'evaluation/evaluation_protocol_seal.json').read_text())['protocol_sha256']} for r in roots}}
    Path(a.output).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:results[str(r)]['metrics']['exact'] for k,r in [(r.name,r) for r in roots]},indent=2))
if __name__=='__main__': main()
