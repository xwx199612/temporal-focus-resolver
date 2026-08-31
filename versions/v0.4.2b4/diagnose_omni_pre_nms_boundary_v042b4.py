#!/usr/bin/env python3
import argparse, hashlib, json, sys
from pathlib import Path
from live_omni_pre_nms_diagnostic_provider_v042b4 import PreNMSDiagnosticProvider
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--image',required=True); ap.add_argument('--omni-root',required=True); ap.add_argument('--checkpoint',required=True); ap.add_argument('--output',required=True); ap.add_argument('--confidence',action='append',type=float,default=[.25,.20,.15,.10,.05]); a=ap.parse_args()
    b=Path(a.image).read_bytes(); out=[]
    for c in a.confidence:
        rec={'confidence':c,'input_image_sha256':hashlib.sha256(b).hexdigest(),'flags':['POST_HOC_DIAGNOSTIC_ONLY','NOT_FORMAL_CANDIDATES','NOT_PRODUCTION_CONFIG','NOT_USED_FOR_PREDICTION']}
        try:
            p=PreNMSDiagnosticProvider(a.omni_root,a.checkpoint,c,640,.70); x,t=p.detect_encoded_with_trace(b); rec.update({'status':'OK','candidate_count':len(x['anonymous_candidates']),'raw_records':x['raw_records'],'source_trace':t['pre_nms'],'stage_trace':t})
        except Exception as e: rec.update({'status':'ERROR','error_type':type(e).__name__,'error':str(e),'pre_nms_decision':'PRE_NMS_NOT_MATERIALIZABLE_FROM_OFFICIAL_PATH'})
        out.append(rec)
    Path(a.output).write_text(json.dumps({'diagnostic_scope':'POST_HOC_DIAGNOSTIC_ONLY','results':out},sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
