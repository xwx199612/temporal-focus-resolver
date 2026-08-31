#!/usr/bin/env python3
"""b6 fresh live production replay; only 0.25/640/0.70 is executed."""
import argparse,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--image-root',required=True); ap.add_argument('--output',required=True); ap.add_argument('--omni-root',required=True); ap.add_argument('--checkpoint',required=True); a=ap.parse_args()
 cmd=[sys.executable,str(HERE/'scripts/run_live_omni_confidence_frontier_v042b5.py'),'--image-root',a.image_root,'--output',a.output,'--omni-root',a.omni_root,'--checkpoint',a.checkpoint,'--confidence','0.25']; subprocess.run(cmd,check=True,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
 if Path(a.output,'run_manifest.json').exists():
  p=Path(a.output,'run_manifest.json'); x=__import__('json').loads(p.read_text()); x.update({'version':'v0.4.2b6','replay_type':'FRESH_LIVE_OMNI_PRODUCTION_REFERENCE','semantic_projection_required_before_gt':True}); p.write_text(__import__('json').dumps(x,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
