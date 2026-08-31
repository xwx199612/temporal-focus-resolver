#!/usr/bin/env python3
"""Canonical, model-semantic projections for replay comparison.

Container metadata, paths, timestamps, profile labels, candidate IDs and
provider order are deliberately excluded from projection payloads.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

SERIALIZATION={"encoding":"UTF-8","json":"sort_keys=true,separators=(',',':'),allow_nan=false","numbers":"bbox coordinates rounded to 6 decimal places; integers remain integers","ordering":"frame_id ascending; candidate bbox tuple (x1,y1,x2,y2) ascending"}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rb(b): return [round(float(x),6) for x in b] if b else None
def loadc(p): return json.loads(Path(p).read_text()).get('candidates',json.loads(Path(p).read_text()).get('anonymous_candidates',[]))
def dump(x): return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def trace_for(root,sm,frame_index,candidates):
    existing=root/'inference/focus_component_trace.jsonl'; fid=sm['frames'][frame_index]['frame_id']
    if False and existing.exists():
        for line in existing.read_text().splitlines():
            x=json.loads(line)
            if x.get('frame_id')==fid:
                # Compact traces from b5 contain container indices. Resolve
                # those indices to geometry locally; IDs/order are excluded.
                if any(k in x for k in ('h_winner_index','e_winner_index','directional_proposal_index')):
                    return {**x,'h_winner_bbox':rb(candidates[x['h_winner_index']]['bbox']) if isinstance(x.get('h_winner_index'),int) and x['h_winner_index']<len(candidates) else None,'e_winner_bbox':rb(candidates[x['e_winner_index']]['bbox']) if isinstance(x.get('e_winner_index'),int) and x['e_winner_index']<len(candidates) else None,'directional_proposal_bbox':rb(candidates[x['directional_proposal_index']]['bbox']) if isinstance(x.get('directional_proposal_index'),int) and x['directional_proposal_index']<len(candidates) else None,'e_intervention':bool(x.get('e_intervention') if x.get('e_intervention') is not None else x.get('intervention',False)),'directional_intervention':bool(x.get('directional_intervention') if x.get('directional_intervention') is not None else x.get('intervention',False))}
    if frame_index==0:return {}
    sys.path.insert(0,str(Path(__file__).parents[1]/'standalone_temporal_focus/src'))
    from vlm_distill.temporal_focus_resolver_v041g6 import resolve_temporal_focus_encoded
    r=resolve_temporal_focus_encoded(Path(sm['frames'][frame_index-1]['encoded_image_path']).read_bytes(),Path(sm['frames'][frame_index]['encoded_image_path']).read_bytes(),candidates)
    def bx(i,items): return rb(items[i]['bbox']) if isinstance(i,int) and 0<=i<len(items) else None
    return {'h_winner_bbox':bx(r.get('h_winner_index'),r.get('h_features',[])),'e_winner_bbox':bx(r.get('e_winner_index'),r.get('e_features',[])),'directional_proposal_bbox':bx(r.get('directional_proposal_index'),r.get('directional_features',[])),'h_winner_index':r.get('h_winner_index'),'e_winner_index':r.get('e_winner_index'),'directional_proposal_index':r.get('directional_proposal_index'),'h_intervention':bool(r.get('intervention',False)),'e_intervention':bool(r.get('e_intervention',False)),'directional_intervention':bool(r.get('intervention',False)),'origin':r.get('origin')}
def make(source):
    root=Path(source); sm=json.loads((root/'session_manifest.json').read_text()); preds={json.loads(x)['frame_id']:json.loads(x) for x in (root/'predictions.jsonl').read_text().splitlines() if x.strip()}; geo=[]; auth=[]; final=[]
    for i,f in enumerate(sorted(sm['frames'],key=lambda x:x['frame_id'])):
        fid=f['frame_id']; p=preds[fid]; c=loadc(root/'omni/normalized'/(fid+'.json')); cbox=sorted((rb(x['bbox']) for x in c)); origin=p.get('origin'); membership=p.get('candidate_membership',p.get('omni_candidate_membership',True)); geo.append({'frame_id':fid,'origin':origin,'image_sha256':f.get('encoded_sha256',f.get('encoded_image_sha256')),'candidate_bboxes':cbox,'candidate_count':len(c)})
        final.append({'frame_id':fid,'origin':origin,'focused_bbox':rb(p.get('focused_bbox')),'candidate_membership':bool(membership),'blocked':origin in {'TEMPORAL_FOCUS_BLOCKED','BLOCKED'},'null_focused_bbox':p.get('focused_bbox') is None and not str(origin).startswith('TEMPORAL_BOOTSTRAP')})
        if i>0:
            t=trace_for(root,sm,i,c); auth.append({'frame_id':fid,'H_WINNER_BBOX':t.get('h_winner_bbox'),'H_DECISION':t.get('h_decision',t.get('origin')),'E_PHYSICAL_ELIGIBLE_COUNT':t.get('e_physical_eligible_count'),'E_SCOPE_PASS':t.get('e_scope_pass'),'E_INTERVENTION':t.get('e_intervention'),'E_SELECTED_BBOX':t.get('e_winner_bbox'),'DIRECTIONAL_PROPOSAL_BBOX':t.get('directional_proposal_bbox'),'DIRECTIONAL_INTERVENTION':t.get('directional_intervention',t.get('intervention')),'FINAL_AUTHORITY_ORIGIN':t.get('origin',origin)})
    sem={'candidate_geometry':geo,'authority_chain':auth,'final_focus':final}
    return {k:{'projection_type':k.upper()+'_PROJECTION' if k!='candidate_geometry' else 'CANDIDATE_GEOMETRY_PROJECTION','rows':v,'serialization':SERIALIZATION} for k,v in [('candidate_geometry',geo),('authority_chain',auth),('final_focus',final)]}|{'semantic_replay':{'projection_type':'SEMANTIC_REPLAY_PROJECTION','rows':sem,'serialization':SERIALIZATION}}
def write(source,out):
    src=Path(source); out=Path(out); out.mkdir(parents=True,exist_ok=True); projections=make(src); manifest={'source_prediction_path':str((src/'predictions.jsonl').resolve()),'source_prediction_sha256':sha(src/'predictions.jsonl'),'projections':{}}
    for name,obj in projections.items():
        p=out/(name+'.json'); p.write_bytes(dump(obj)); manifest['projections'][name]={'path':p.name,'sha256':sha(p),'schema_version':'CANONICAL_SEMANTIC_PROJECTION_V1','included_fields':list(obj['rows'][0].keys()) if isinstance(obj['rows'],list) and obj['rows'] else list(obj['rows'].keys()),'excluded_fields':['timestamp','run_directory','profile_label','host_path','manifest_path','artifact_hash','candidate_id','provider_order','confidence','environment_metadata']}
    (out/'projection_manifest.json').write_bytes(dump(manifest)); return manifest
