"""Encoded, dual-plane, and RGB compatibility Temporal Focus APIs."""
from __future__ import annotations
from .omni_candidate_adapter_v1 import scorer_visible
from .temporal_focus_image_input_v1 import decode_temporal_focus_image
from .temporal_focus_features_v041g6 import materialize_h_features,materialize_e_features,materialize_directional_features
from .temporal_focus_resolver_v041g4 import _gap,_with_scope
from .spatial_focus_scorer_v041g import arbitrate,POLARITY_THRESHOLD,COMPACTNESS_THRESHOLD,SIGNED_EVIDENCE_FLOOR
def bootstrap_temporal_focus(current_rgb,current_omni_candidates,frozen_config=None):
    return {'status':'OK','origin':'TEMPORAL_BOOTSTRAP_UNAVAILABLE','focused_bbox':None,'focused_candidate_id':None,'intervention':False,'input_profile':'OPENCV_ENCODED_DUAL_DECODE_V1','frozen_e_numeric_parity_capable':True,'candidate_count':len(current_omni_candidates)}
def resolve_temporal_focus_planes(previous_rgb,current_rgb,previous_gray_e,current_gray_e,current_omni_candidates,frozen_config=None,input_profile='OPENCV_ENCODED_DUAL_DECODE_V1',parity_capable=True):
    cs=[scorer_visible(c) if hasattr(c,'bbox') else dict(c) for c in current_omni_candidates]
    for i,c in enumerate(cs):c.setdefault('container_index',i);c['bbox']=[float(x) for x in c['bbox']]
    h=_with_scope(materialize_h_features(current_rgb,cs,previous_rgb)); e=_with_scope(materialize_e_features(previous_rgb,current_rgb,h,h,previous_gray_e,current_gray_e)); ho=sorted(h,key=lambda x:(x['h041b_rank'],x['container_index']));eo=sorted(e,key=lambda x:(-x['enlargement_raw'],x['container_index']));hw=ho[0];ew=eo[0];hg=_gap([x['h041b_raw'] for x in h]);eg=_gap([x['enlargement_raw'] for x in e]);ea=bool(ew.get('physical_strong') and eg is not None and hg is not None and eg>hg and ew['container_index']!=hw['container_index']); es=ea and ew['compactness']>=.70 and ew['containment_depth']<=1; baseline=ew if es else hw; d=materialize_directional_features(previous_rgb,current_rgb,h,h,e); dm={x['container_index']:x['transition'] for x in d}
    for x in h:x['transition']=dm[x['container_index']]
    g=arbitrate({'bootstrap':False,'baseline':baseline,'h_winner':hw,'e_intervention':es,'winner_candidate':hw,'candidates':h},polarity_threshold=POLARITY_THRESHOLD,compactness_threshold=COMPACTNESS_THRESHOLD,signed_evidence_floor=SIGNED_EVIDENCE_FLOOR); final=g['winner']
    return {'status':'OK','origin':g['origin'],'focused_bbox':final['bbox'],'focused_candidate_id':final.get('candidate_id',final.get('container_index')),'focused_container_index':final.get('container_index'),'intervention':bool(g.get('intervention')),'e_intervention':es,'h_winner_index':hw['container_index'],'e_winner_index':ew['container_index'],'directional_proposal_index':g.get('proposal',{}).get('container_index') if g.get('proposal') else None,'authority':'V041G_DIRECTIONAL_H_ONSET_RESCUE' if g.get('intervention') else 'V041E_OR_H_BASELINE','input_profile':input_profile,'frozen_e_numeric_parity_capable':parity_capable,'h_features':h,'e_features':e,'directional_features':d,'checks':g.get('checks',{})}
def resolve_temporal_focus_encoded(previous_image_bytes,current_image_bytes,current_omni_candidates,frozen_config=None):
    p=decode_temporal_focus_image(previous_image_bytes);c=decode_temporal_focus_image(current_image_bytes);r=resolve_temporal_focus_planes(p.rgb,c.rgb,p.gray_e,c.gray_e,current_omni_candidates,frozen_config);r.update({'previous_encoded_sha256':p.encoded_sha256,'current_encoded_sha256':c.encoded_sha256,'input_profile':'OPENCV_ENCODED_DUAL_DECODE_V1','frozen_e_numeric_parity_capable':True});return r
def resolve_temporal_focus(previous_rgb,current_rgb,current_omni_candidates,frozen_config=None):
    from .temporal_focus_resolver_v041g4 import resolve_temporal_focus as old
    r=old(previous_rgb,current_rgb,current_omni_candidates,frozen_config);r.update({'input_profile':'RGB_ARRAY_COMPATIBILITY_V1','frozen_e_numeric_parity_capable':False});return r
