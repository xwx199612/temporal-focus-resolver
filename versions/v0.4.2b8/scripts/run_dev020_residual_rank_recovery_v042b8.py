#!/usr/bin/env python3
"""Fresh .20 live Omni baseline plus GT-free residual feature inventory."""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image-root', required=True); ap.add_argument('--output', required=True)
    ap.add_argument('--omni-root', required=True); ap.add_argument('--checkpoint', required=True)
    a = ap.parse_args(); out = Path(a.output).resolve()
    subprocess.run([sys.executable, str(HERE/'scripts/run_live_omni_candidate_recall_v042b7.py'),
                    '--profile','dev_candidate_recall_020','--image-root',a.image_root,
                    '--output',str(out),'--omni-root',a.omni_root,'--checkpoint',a.checkpoint],
                   check=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    sys.path.insert(0, str(HERE/'standalone_temporal_focus/src'))
    from vlm_distill.temporal_focus_resolver_v041g6 import resolve_temporal_focus_encoded
    sm = json.loads((out/'session_manifest.json').read_text()); trace=[]; features=[]
    for i, frame in enumerate(sm['frames']):
        if i == 0: continue
        n = json.loads((out/'omni/normalized'/(frame['frame_id']+'.json')).read_text()); cs=n['candidates']
        prev=Path(sm['frames'][i-1]['encoded_image_path']).read_bytes(); cur=Path(frame['encoded_image_path']).read_bytes()
        r=resolve_temporal_focus_encoded(prev,cur,cs); r=r.to_dict() if hasattr(r,'to_dict') else r
        for c in r.get('h_features', []):
            features.append({'frame_id':frame['frame_id'],'candidate_id':c.get('candidate_id'),'bbox':c.get('bbox'),
              'area':c.get('width',0)*c.get('height',0),'h041b_raw':c.get('h041b_raw'),
              'density':c.get('density'),'valid_fraction':c.get('valid_fraction'),
              'positive_onset_support':c.get('positive_onset_support',c.get('onset_positive_support',0.0)),
              'offset_support':c.get('offset_support',c.get('offset_asymmetry',0.0)),
              'interior_ring_contrast':c.get('interior_ring_contrast',0.0),
              'edge_ring_continuity':c.get('edge_ring_continuity',0.0),
              'containment_depth':c.get('containment_depth'),'compactness':c.get('compactness'),
              'h_rank':c.get('h041b_rank'),'GT_FREE':True,'NO_PRODUCTION_CHANGE_APPLIED':True})
        trace.append({'frame_id':frame['frame_id'],'candidate_count':len(cs),'baseline':r,
                      'NO_PRODUCTION_CHANGE_APPLIED':True})
    (out/'inference/gt_free_feature_table.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in features))
    (out/'inference/baseline_full_trace.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in trace))
    seal={'gt_loaded_before_seal':False,'feature_table_sha256':sha(out/'inference/gt_free_feature_table.jsonl'),
      'baseline_trace_sha256':sha(out/'inference/baseline_full_trace.jsonl'),'prediction_sha256':sha(out/'predictions.jsonl'),
      'omni_manifest_sha256':sha(out/'omni/omni_execution_manifest.json'),'profile':'DEV_CANDIDATE_RECALL_PROFILE_020',
      'formula_candidates':['baseline_frozen_h','robust_positive_onset','contrast_coherence'],'formula_inputs_gt_free':True}
    (out/'inference/gt_free_seal.json').write_text(json.dumps(seal,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'output':str(out),'provider_invocations':29,'feature_rows':len(features),'seal':seal},sort_keys=True))
if __name__ == '__main__': main()
