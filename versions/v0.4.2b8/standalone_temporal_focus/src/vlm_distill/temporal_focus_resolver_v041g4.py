"""Functional, file-free v0.4.1g temporal focus composition."""
from __future__ import annotations
from .omni_candidate_adapter_v1 import normalize_omni_candidates, scorer_visible
from .temporal_focus_features_v041g4 import materialize_h_features, materialize_e_features, materialize_directional_features
from .spatial_focus_scorer_v041g import arbitrate, POLARITY_THRESHOLD, COMPACTNESS_THRESHOLD, SIGNED_EVIDENCE_FLOOR
import statistics

def _gap(values):
    if len(values)<2:return None
    v=sorted(map(float,values),reverse=True); med=statistics.median(v); mad=statistics.median(abs(x-med) for x in v); scale=1.4826*mad
    if scale==0 and len(v)>=4:
        q=statistics.quantiles(v,n=4); scale=(q[2]-q[0])/1.349
    if scale==0: scale=statistics.pstdev(v)
    return (v[0]-v[1])/scale if scale else None
def _with_scope(rows):
    for r in rows:
        b=r['bbox']; r['compactness']=min(r['width'],r['height'])/max(r['width'],r['height']) if r['width']>0 and r['height']>0 else None
    for r in rows:
        b=r['bbox']; r['containment_parents']=[q['container_index'] for q in rows if q is not r and q['bbox'][0]<=b[0] and q['bbox'][1]<=b[1] and q['bbox'][2]>=b[2] and q['bbox'][3]>=b[3]]; r['containment_depth']=len(r['containment_parents'])
    return rows
def bootstrap_temporal_focus(current_rgb,current_omni_candidates,frozen_config=None):
    return {'status':'OK','origin':'TEMPORAL_BOOTSTRAP_UNAVAILABLE','focused_bbox':None,'focused_candidate_id':None,'intervention':False,'candidate_count':len(current_omni_candidates)}
def resolve_temporal_focus(previous_rgb,current_rgb,current_omni_candidates,frozen_config=None):
    if previous_rgb is None or current_rgb is None: raise ValueError('causal pair requires both RGB arrays')
    cs=[scorer_visible(c) if hasattr(c,'bbox') else dict(c) for c in current_omni_candidates]
    for i,c in enumerate(cs): c.setdefault('container_index',i); c['bbox']=[float(x) for x in c['bbox']]
    h=materialize_h_features(current_rgb,cs,previous_rgb); h=_with_scope(h)
    e=materialize_e_features(previous_rgb,current_rgb,h,h); e=_with_scope(e)
    h_order=sorted(h,key=lambda x:(x['h041b_rank'],x['container_index'])); e_order=sorted(e,key=lambda x:(-x['enlargement_raw'],x['container_index']))
    hw=h_order[0]; ew=e_order[0]; hg=_gap([x['h041b_raw'] for x in h]); eg=_gap([x['enlargement_raw'] for x in e]); ephys=ew.get('physical_strong',False); e_arbitration=bool(ephys and eg is not None and hg is not None and eg>hg and ew['container_index']!=hw['container_index'])
    e_scope=e_arbitration and ew['compactness'] is not None and ew['compactness']>=.70 and ew['containment_depth']<=1
    baseline=ew if e_scope else hw
    d=materialize_directional_features(previous_rgb,current_rgb,h, h, e)
    by={x['container_index']:x for x in d};
    for x in h: x['transition']=by[x['container_index']]['transition']
    ctx={'bootstrap':False,'baseline':baseline,'h_winner':hw,'e_intervention':e_scope,'winner_candidate':hw,'candidates':h}
    g=arbitrate(ctx,polarity_threshold=POLARITY_THRESHOLD,compactness_threshold=COMPACTNESS_THRESHOLD,signed_evidence_floor=SIGNED_EVIDENCE_FLOOR)
    final=g['winner']; origin=g['origin'];
    return {'status':'OK','origin':origin,'focused_bbox':final['bbox'],'focused_candidate_id':final.get('candidate_id',final.get('container_index')),'focused_container_index':final.get('container_index'),'intervention':bool(g.get('intervention')),'e_intervention':bool(e_scope),'h_winner_index':hw['container_index'],'e_winner_index':ew['container_index'],'directional_proposal_index':g.get('proposal',{}).get('container_index') if g.get('proposal') else None,'h_features':h,'e_features':e,'directional_features':d,'e_eligible':e_arbitration,'e_scope_pass':e_scope,'directional_eligible':bool(g.get('checks')),'checks':g.get('checks',{}),'authority':'V041G_DIRECTIONAL_H_ONSET_RESCUE' if g.get('intervention') else 'V041E_OR_H_BASELINE'}
