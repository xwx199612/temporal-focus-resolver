#!/usr/bin/env python3
"""Run one locked confidence profile from encoded bytes through live Omni and frozen g6."""
from __future__ import annotations
import argparse, hashlib, json, statistics, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
G6="7e67fa63406892854f7c61e003ff49c666cc6bbeaf01f3457ca4bc3f3606c2e9"
PROFILES={.25:("production_reference","FORMAL_PRODUCTION_REFERENCE"),.20:("diagnostic_conf_020","POST_HOC_DIAGNOSTIC_ONLY"),.15:("diagnostic_conf_015","POST_HOC_DIAGNOSTIC_ONLY"),.10:("diagnostic_conf_010","POST_HOC_DIAGNOSTIC_ONLY")}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def protocol():
    return {"protocol_id":"V042B4_LOCKED_METRIC_FORMAL_PRODUCTION_REFERENCE","contract_status":"FORMAL_B4_LOCKED_METRIC","gt_loaded_before_protocol_seal":False,"gt_bbox_format":"xyxy_pixel authoritative focus bbox","gt_to_live_candidate_mapping":{"method":"EXACT_BBOX_GEOMETRY_MATCH_AFTER_ROUND_6","iou_threshold":1.0,"center_distance_threshold_px":0.0,"containment_threshold":1.0,"unique_match_required":True,"ambiguous_if_multiple_exact_matches":True},"correctness_definition":"focused candidate must equal uniquely mapped candidate under frozen exact rounded-6 geometry","denominator_rules":{"bootstrap_excluded":True,"candidate_recall":"28 causal frames","conditional":"uniquely mapped causal frames","end_to_end":"all 28 causal frames"},"topk_definition":"NOT_MATERIALIZABLE unless legal frozen final ranking exists; H-only is not final ranking"}
def make_session(root,image_root,profile,conf):
    files=[]
    for p in sorted(Path(image_root).iterdir(),key=lambda x:x.name):
        if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png'}:
            from PIL import Image
            with Image.open(p) as im: w,h=im.size
            files.append({'frame_id':p.name,'frame_index':len(files),'encoded_image_path':str(p.resolve()),'encoded_sha256':sha(p),'width':w,'height':h})
    if len(files)!=29: raise RuntimeError(f'expected 29 encoded images, found {len(files)}')
    (root/'input').mkdir(parents=True); (root/'omni/raw').mkdir(parents=True); (root/'omni/normalized').mkdir(parents=True); (root/'inference').mkdir(parents=True); (root/'evaluation').mkdir(parents=True); (root/'audit').mkdir(parents=True)
    sm={'sequence_id':f'image_continuous_crop_{profile}','frames':files,'dataset_status':'HISTORICAL_REGRESSION_ONLY','gt_accessed':False}; (root/'session_manifest.json').write_text(json.dumps(sm,sort_keys=True,indent=2)+'\n'); (root/'input/image_manifest.json').write_text(json.dumps({'frames':files,'gt_accessed':False},sort_keys=True,indent=2)+'\n'); (root/'input/order_manifest.json').write_text(json.dumps({'ordering':'explicit filename lexicographic ordering, ground_truth excluded','frames':[{'frame_id':x['frame_id'],'frame_index':x['frame_index']} for x in files]},sort_keys=True,indent=2)+'\n')
    (root/'audit/pre_gt_access_audit.json').write_text(json.dumps({'gt_loaded':False,'gt_bytes_read':False,'gt_derived_ordering':False,'gt_derived_config':False,'session_role':'HISTORICAL_REGRESSION_ONLY'},sort_keys=True,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--image-root',required=True); ap.add_argument('--output',required=True); ap.add_argument('--omni-root',required=True); ap.add_argument('--checkpoint',required=True); ap.add_argument('--confidence',required=True,type=float); a=ap.parse_args(); conf=round(a.confidence,2)
    if conf not in PROFILES: raise SystemExit('confidence must be one of 0.25, 0.20, 0.15, 0.10')
    out=Path(a.output).resolve(); profile,status=PROFILES[conf]; out.mkdir(parents=True); make_session(out,a.image_root,profile,conf)
    cmd=[sys.executable,str(HERE/'run_v042b4.py'),'omni','--session',str(out),'--omni-root',a.omni_root,'--checkpoint',a.checkpoint,'--confidence',str(conf),'--imgsz','640','--iou','0.70']; subprocess.run(cmd,check=True,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
    sys.path.insert(0,str(HERE/'standalone_temporal_focus/src')); from vlm_distill.temporal_focus_resolver_v041g6 import resolve_temporal_focus_encoded
    sm=json.loads((out/'session_manifest.json').read_text()); preds=[]; traces=[]
    for i,f in enumerate(sm['frames']):
        n=json.loads((out/'omni/normalized'/(f['frame_id']+'.json')).read_text()); cs=n['candidates']
        if i==0: r={'origin':'TEMPORAL_BOOTSTRAP_UNAVAILABLE','focused_bbox':None,'focused_candidate_id':None,'intervention':False,'candidate_count':len(cs)}
        else:
            r=resolve_temporal_focus_encoded(Path(sm['frames'][i-1]['encoded_image_path']).read_bytes(),Path(f['encoded_image_path']).read_bytes(),cs); r=r.to_dict() if hasattr(r,'to_dict') else r
        membership=r.get('focused_bbox') is None or any(r.get('focused_bbox')==c['bbox'] for c in cs); public={k:v for k,v in r.items() if k not in {'h_features','e_features','directional_features'}}; public.update({'frame_id':f['frame_id'],'frame_index':i,'profile':profile,'confidence':conf,'candidate_membership':membership}); preds.append(public)
        traces.append({'frame_id':f['frame_id'],'profile':profile,'confidence':conf,'H_COMPONENT_RANKS':[x.get('h041b_rank') for x in r.get('h_features',[])],'E_COMPONENT_RANKS':[x.get('e_rank') for x in r.get('e_features',[])],'DIRECTIONAL_COMPONENT_RANKS':'MATERIALIZED_IN_FROZEN_TRACE' if r.get('directional_features') else 'NOT_MATERIALIZABLE','origin':r.get('origin'),'h_winner_index':r.get('h_winner_index'),'e_winner_index':r.get('e_winner_index'),'directional_proposal_index':r.get('directional_proposal_index'),'intervention':r.get('intervention'),'candidate_membership':membership})
    (out/'predictions.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in preds)); (out/'inference/focus_component_trace.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in traces));
    counts=[len(json.loads((out/'omni/normalized'/(f['frame_id']+'.json')).read_text())['candidates']) for f in sm['frames']]; confs=[c['confidence'] for f in sm['frames'] for c in json.loads((out/'omni/raw'/(f['frame_id']+'.json')).read_text())['raw_records']]
    (out/'inference/candidate_confidence_distribution.json').write_text(json.dumps({'profile':profile,'confidence':conf,'count':len(confs),'min':min(confs),'max':max(confs),'p05':statistics.quantiles(confs,n=20,method='inclusive')[0],'p25':statistics.quantiles(confs,n=4,method='inclusive')[0],'median':statistics.median(confs),'p75':statistics.quantiles(confs,n=4,method='inclusive')[2],'p95':statistics.quantiles(confs,n=20,method='inclusive')[18]},sort_keys=True,indent=2)+'\n')
    (out/'evaluation/evaluation_protocol.json').write_text(json.dumps(protocol(),sort_keys=True,indent=2)+'\n'); (out/'evaluation/evaluation_protocol_seal.json').write_text(json.dumps({'protocol_sha256':sha(out/'evaluation/evaluation_protocol.json'),'contract':'FORMAL_B4_LOCKED_METRIC','gt_loaded_before_seal':False},sort_keys=True,indent=2)+'\n')
    seal={'profile':profile,'confidence':conf,'status':status,'production_config':{'confidence':.25,'imgsz':640,'iou':.70},'prediction_sha256':sha(out/'predictions.jsonl'),'omni_manifest_sha256':sha(out/'omni/omni_execution_manifest.json'),'normalized_candidates_sha256':sha(out/'inference/candidate_confidence_distribution.json'),'component_trace_sha256':sha(out/'inference/focus_component_trace.jsonl'),'image_manifest_sha256':sha(out/'input/image_manifest.json'),'protocol_sha256':sha(out/'evaluation/evaluation_protocol.json'),'g6_manifest_sha256':G6,'gt_loaded_before_seal':False,'provider_invocations':29,'model_loads':1}; (out/'inference/prediction_seal.json').write_text(json.dumps(seal,sort_keys=True,indent=2)+'\n'); (out/'audit/candidate_membership_audit.json').write_text(json.dumps({'rows':len(preds),'bootstrap':1,'causal':28,'failures':[x['frame_id'] for x in preds[1:] if not x['candidate_membership']]},sort_keys=True,indent=2)+'\n'); (out/'run_manifest.json').write_text(json.dumps({'version':'v0.4.2b5','profile':profile,'confidence':conf,'status':status,'image_count':29,'dataset_status':'HISTORICAL_REGRESSION_ONLY','fresh_live_omni':True,'reuse_raw':False,'production_config_locked':{'confidence':.25,'imgsz':640,'iou':.70}},sort_keys=True,indent=2)+'\n'); print(json.dumps({'profile':profile,'confidence':conf,'output':str(out),'prediction_sha256':seal['prediction_sha256'],'candidate_total':sum(counts),'min':min(counts),'max':max(counts)},sort_keys=True))
if __name__=='__main__': main()
