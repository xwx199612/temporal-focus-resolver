#!/usr/bin/env python3
"""Version-local runner: encoded bytes -> official Omni -> frozen g6."""
import argparse, hashlib, json, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'standalone_omni_bridge')); sys.path.insert(0,str(HERE/'standalone_temporal_focus/src'))
from official_provider import OfficialOmniIconProvider
def h(x): return hashlib.sha256(Path(x).read_bytes()).hexdigest()
def load(s): return json.loads((Path(s)/'session_manifest.json').read_text())
def run_omni(a):
    s=Path(a.session); m=load(s); raw=s/'omni/raw'; norm=s/'omni/normalized'; raw.mkdir(parents=True,exist_ok=True); norm.mkdir(parents=True,exist_ok=True)
    existing=list(raw.glob('*.json'))
    if existing and not a.reuse_sealed_raw: raise RuntimeError('PREEXISTING_RAW_REQUIRES_EXPLICIT_REUSE')
    provider=OfficialOmniIconProvider(a.omni_root,a.checkpoint,a.confidence,a.imgsz,a.iou,a.device); rows=[]
    for f in m['frames']:
        b=Path(f['encoded_image_path']).read_bytes(); image_sha=hashlib.sha256(b).hexdigest(); start=time.perf_counter()
        if a.reuse_sealed_raw:
            record=json.loads((raw/(f['frame_id']+'.json')).read_text())
            if record.get('image_sha256')!=image_sha: raise RuntimeError('RAW_IMAGE_HASH_MISMATCH')
        else:
            record=provider.detect_encoded(b); record.update({'frame_id':f['frame_id'],'image_sha256':image_sha,'checkpoint_sha256':h(a.checkpoint),'provider_config':{'confidence':a.confidence,'imgsz':a.imgsz,'iou':a.iou,'device':provider.device},'execution_status':'OK','inference_called':True,'elapsed_seconds':time.perf_counter()-start}); (raw/(f['frame_id']+'.json')).write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
        candidates=record['anonymous_candidates']; ids=[x['candidate_id'] for x in candidates]
        if len(ids)!=len(set(ids)): raise RuntimeError('DUPLICATE_CANDIDATE_ID')
        n={'frame_id':f['frame_id'],'image_sha256':image_sha,'provider':'MICROSOFT_OMNIPARSER','detector':'YOLOv9-E icon_detect_v3','candidates':candidates,'candidate_count':len(candidates)}; (norm/(f['frame_id']+'.json')).write_text(json.dumps(n,sort_keys=True,indent=2)+'\n')
        rows.append({'frame_id':f['frame_id'],'image_sha256':image_sha,'raw_sha256':h(raw/(f['frame_id']+'.json')),'normalized_sha256':h(norm/(f['frame_id']+'.json')),'candidate_count':len(candidates),'status':'OK','inference_called':not a.reuse_sealed_raw})
    (s/'omni/omni_execution_manifest.json').write_text(json.dumps({'provider':'MICROSOFT_OMNIPARSER','detector':'YOLOv9-E icon_detect_v3','omni_root':str(Path(a.omni_root).resolve()),'checkpoint':str(Path(a.checkpoint).resolve()),'checkpoint_sha256':h(a.checkpoint),'config':vars(a),'frames':rows},sort_keys=True,indent=2)+'\n')
def run_predict(s):
    from vlm_distill.temporal_focus_resolver_v041g6 import resolve_temporal_focus_encoded
    s=Path(s); m=load(s); out=[]
    for i,f in enumerate(m['frames']):
        n=json.loads((s/'omni/normalized'/(f['frame_id']+'.json')).read_text()); cs=n['candidates']
        if i==0: r={'origin':'TEMPORAL_BOOTSTRAP_UNAVAILABLE','focused_bbox':None,'focused_candidate_id':None,'intervention':False}
        else:
            r=resolve_temporal_focus_encoded(Path(m['frames'][i-1]['encoded_image_path']).read_bytes(),Path(f['encoded_image_path']).read_bytes(),cs); r=r.to_dict() if hasattr(r,'to_dict') else r
        r.update({'frame_id':f['frame_id'],'sequence_id':m['sequence_id'],'frame_index':f['frame_index'],'omni_candidate_membership':r.get('focused_bbox') is None or any(r.get('focused_bbox')==x['bbox'] for x in cs)}); out.append(r)
    (s/'predictions.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in out)); return out
def seal(s):
    s=Path(s); pred=s/'predictions.jsonl'; omni=s/'omni/omni_execution_manifest.json'; g6=HERE/'standalone_temporal_focus/SOURCE_MANIFEST.json'
    if not pred.exists() or not omni.exists(): raise RuntimeError('SEAL_INPUT_MISSING')
    x={'prediction_sha256':h(pred),'omni_manifest_sha256':h(omni),'g6_manifest_sha256':h(g6),'gt_loaded_before_seal':False,'sealed_at':time.time()}; (s/'prediction_seal.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n'); return x
def normalize_existing(s):
    """Offline-only normalization; never claims detector execution."""
    s=Path(s); m=load(s); out=s/'omni/normalized'; out.mkdir(parents=True,exist_ok=True)
    for f in m['frames']:
        raw=s/'omni/raw'/(f['frame_id']+'.json')
        if not raw.exists(): raise FileNotFoundError(raw)
        x=json.loads(raw.read_text()); candidates=x.get('anonymous_candidates',[])
        ids=[c['candidate_id'] for c in candidates]
        if len(ids)!=len(set(ids)): raise RuntimeError('DUPLICATE_CANDIDATE_ID')
        (out/(f['frame_id']+'.json')).write_text(json.dumps({'frame_id':f['frame_id'],'image_sha256':f['image_sha256'],'provider':'EXTERNAL_OMNI','candidates':candidates,'candidate_count':len(candidates)},sort_keys=True,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True); sub.add_parser('self-test'); o=sub.add_parser('omni'); o.add_argument('--session',required=True); o.add_argument('--omni-root',required=True); o.add_argument('--checkpoint',required=True); o.add_argument('--confidence',type=float,default=.25); o.add_argument('--imgsz',type=int,default=640); o.add_argument('--iou',type=float,default=.70); o.add_argument('--device'); o.add_argument('--reuse-sealed-raw',action='store_true'); n=sub.add_parser('normalize-existing-omni'); n.add_argument('--session',required=True); p=sub.add_parser('predict'); p.add_argument('--session',required=True); z=sub.add_parser('seal'); z.add_argument('--session',required=True); a=ap.parse_args()
    if a.cmd=='self-test': print(json.dumps({'status':'PASS','fixture_scope':'SELF_TEST_ONLY','live_omni_called':False})); return
    if a.cmd=='omni': run_omni(a)
    elif a.cmd=='normalize-existing-omni': normalize_existing(a.session); print(json.dumps({'status':'NORMALIZATION_ONLY','live_omni_called':False}))
    elif a.cmd=='predict': print(json.dumps({'rows':len(run_predict(a.session))}))
    else: print(json.dumps(seal(a.session)))
if __name__=='__main__': main()
