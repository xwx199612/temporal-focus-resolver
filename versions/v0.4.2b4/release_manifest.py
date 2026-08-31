#!/usr/bin/env python3
"""Two-layer, self-reference-free release manifest generator and verifier."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXCLUDED = {"CONTENT_MANIFEST.json", "RELEASE_SEAL.json", "RELEASE_SEAL.sha256"}
G6 = "7e67fa63406892854f7c61e003ff49c666cc6bbeaf01f3457ca4bc3f3606c2e9"
def digest(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def payload(root=ROOT):
    out=[]
    for p in root.rglob("*"):
        if not p.is_file() or p.name in EXCLUDED: continue
        if p.is_symlink() or p.suffix in {".pyc", ".pyo"} or "__pycache__" in p.parts: raise RuntimeError(f"invalid release payload: {p}")
        rel=p.relative_to(root).as_posix(); out.append({"path":rel,"size":p.stat().st_size,"sha256":digest(p)})
    return sorted(out,key=lambda x:x["path"])
def content_manifest(root=ROOT): return {"schema":"CONTENT_MANIFEST_V1","payload":payload(root)}
def write_release(root=ROOT, creation_timestamp="2026-08-31T00:00:00Z"):
    cm=root/"CONTENT_MANIFEST.json"; seal=root/"RELEASE_SEAL.json"; sig=root/"RELEASE_SEAL.sha256"
    cm.write_text(json.dumps(content_manifest(root),indent=2,sort_keys=True)+"\n")
    caps=json.loads((root/"FUNCTIONAL_CAPABILITIES.json").read_text())
    obj={"version":"v0.4.2b4","content_manifest_sha256":digest(cm),"frozen_g6_manifest_sha256":G6,"creation_timestamp":creation_timestamp,"functional_capabilities":caps,"live_execution_decision":"V042B4_ENCODED_IMAGE_TO_OMNI_TO_FOCUS_VERIFIED"}
    seal.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n"); sig.write_text(digest(seal)+"\n")
    return verify(root)
def verify(root=ROOT):
    cm=root/"CONTENT_MANIFEST.json"; seal=root/"RELEASE_SEAL.json"; sig=root/"RELEASE_SEAL.sha256"
    if not (cm.exists() and seal.exists() and sig.exists()): return {"passed":False,"reason":"manifest files missing"}
    data=json.loads(cm.read_text()); rows=data.get("payload",[]); paths=[x.get("path") for x in rows]
    actual_paths=sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name not in EXCLUDED and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"})
    checks={"schema":data.get("schema")=="CONTENT_MANIFEST_V1","sorted_unique_paths":paths==sorted(set(paths)),"excluded_from_payload":not (set(paths)&EXCLUDED),"content_path_completeness":paths==actual_paths,"files_exist_and_hash":all((root/x["path"]).is_file() and (root/x["path"]).stat().st_size==x["size"] and digest(root/x["path"])==x["sha256"] for x in rows),"content_manifest_hash":digest(cm)==json.loads(seal.read_text()).get("content_manifest_sha256"),"seal_hash":digest(seal)==sig.read_text().strip(),"g6_hash":json.loads(seal.read_text()).get("frozen_g6_manifest_sha256")==G6,"no_self_reference":not any(x["path"] in EXCLUDED or x["sha256"] in {digest(cm),digest(seal),sig.read_text().strip()} for x in rows),"circular_reference_absent":not any(x["path"] in {"CONTENT_MANIFEST.json","RELEASE_SEAL.json","RELEASE_SEAL.sha256"} for x in rows)}
    return {"passed":all(checks.values()),"checks":checks,"payload_count":len(rows)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",choices=("create","verify")); ap.add_argument("--timestamp",default="2026-08-31T00:00:00Z"); a=ap.parse_args(); result=write_release(creation_timestamp=a.timestamp) if a.command=="create" else verify(); print(json.dumps(result,indent=2,sort_keys=True)); sys.exit(0 if result.get("passed") else 1)
if __name__=="__main__": main()
