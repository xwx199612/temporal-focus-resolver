#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1])); from app.canonical_semantic_projection_v042b6 import write,sha
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--source',action='append',required=True,help='label=sealed session root'); ap.add_argument('--output',required=True); a=ap.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True); allm={}
 for spec in a.source:
  label,path=spec.split('=',1); allm[label]=write(path,out/label)
 labels=list(allm); comps={}
 for i,l in enumerate(labels):
  for r in labels[i+1:]:
   comps[l+'__VS__'+r]={}
   for proj in ('candidate_geometry','authority_chain','final_focus','semantic_replay'):
    lp=out/l/(proj+'.json'); rp=out/r/(proj+'.json'); lx=json.loads(lp.read_text())['rows']; rx=json.loads(rp.read_text())['rows']; lm={x['frame_id']:x for x in lx} if isinstance(lx,list) else lx; rm={x['frame_id']:x for x in rx} if isinstance(rx,list) else rx; fs=sorted(set(lm)&set(rm)); dif=[f for f in fs if lm[f]!=rm[f]]; comps[l+'__VS__'+r][proj]={'hash_left':sha(lp),'hash_right':sha(rp),'equal':not dif,'divergence_count':len(dif),'first_divergence':dif[0] if dif else None}
 (out/'comparison.json').write_text(json.dumps({'comparisons':comps,'semantic_rule':'Only projection equality is replay parity; raw container hash is not sufficient.'},sort_keys=True,indent=2)+'\n'); print(json.dumps(comps,indent=2))
if __name__=='__main__': main()
