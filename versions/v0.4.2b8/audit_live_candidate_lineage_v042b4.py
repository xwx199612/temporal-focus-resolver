#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from b4_audit_lib import lineage,sha256,PROVENANCE
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--left',required=True); ap.add_argument('--right',required=True); ap.add_argument('--left-provenance',required=True); ap.add_argument('--right-provenance',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    x=lineage(a.left,a.right,a.left_provenance,a.right_provenance,{'left':str(Path(a.left).resolve()),'right':str(Path(a.right).resolve()),'left_sha256':sha256(Path(a.left).parent/'omni_execution_manifest.json') if (Path(a.left).parent/'omni_execution_manifest.json').exists() else None,'right_sha256':sha256(Path(a.right).parent/'omni_execution_manifest.json') if (Path(a.right).parent/'omni_execution_manifest.json').exists() else None}); Path(a.output).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
