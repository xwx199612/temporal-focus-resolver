#!/usr/bin/env python3
"""GT-after-seal report helper. It only reads sealed predictions/candidates."""
import argparse,json
from pathlib import Path
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--session',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); s=Path(a.session); targets={'WIN_20260529_10_35_27_Pro.jpg','WIN_20260529_10_36_22_Pro.jpg','WIN_20260529_10_42_38_Pro.jpg'}; rows=[]
    preds={json.loads(x)['frame_id']:json.loads(x) for x in (s/'predictions.jsonl').read_text().splitlines() if x.strip()}
    for f in sorted(targets):
        p=preds[f]; rows.append({'frame_id':f,'candidate_count':len(json.loads((s/'omni/normalized'/(f+'.json')).read_text())['candidates']),'final_focused_bbox':p.get('focused_bbox'),'origin':p.get('origin'),'authority_trace':p.get('authority_trace'),'h_component_rank':None,'e_physical_eligibility':None,'e_arbitration':p.get('intervention'),'compact_object_scope':None,'directional_gate':None,'NO_PRODUCTION_CHANGE_APPLIED':True,'classification':'H_RANKING_FAILURE','note':'GT fields are populated only by the post-seal evaluator.'})
    Path(a.output).write_text(json.dumps({'scope':'READ_ONLY_POST_HOC_CHARACTERIZATION','rows':rows},sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
