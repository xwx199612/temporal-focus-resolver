"""Development-only v0.4.1b structural H ranking.

One frame-global formula; no frame identity, GT, historical rank, or proposal
deletion is used.  This is intentionally parallel to v0.4.0a/v0.4.1a.
"""
import math
import numpy as np
RULE_MANIFEST={'name':'V041B_OBJECT_SCALE_CONTAINMENT_H_V1','formula':'0.10*robust_z(H_raw)+0.60*robust_z(density*(0.90+0.10*valid_fraction))+0.30*robust_z(log1p(area))','normalization':'per-frame median/MAD robust z','features':['highlight_raw','density','log1p(area)','valid_fraction'],'candidate_deletion':False,'tie_break':'container_index ascending','authority':'H_PRIMARY_ONLY','development_in_sample':True}
def robust(v):
 x=np.asarray(v,dtype=float); med=np.median(x) if len(x) else 0.; mad=np.median(np.abs(x-med)) if len(x) else 0.; return np.clip((x-med)/max(1.4826*mad,1e-9),-8,8)
def score_h041b(rows):
 raw=np.array([float(r.get('highlight_raw',0) or 0) for r in rows]); den=np.array([float(r.get('highlight_pool',{}).get('density',0) or 0) for r in rows]); area=np.array([math.log1p(max(0,(r['bbox'][2]-r['bbox'][0])*(r['bbox'][3]-r['bbox'][1]))) for r in rows]); valid=np.array([float(r.get('highlight_pool',{}).get('valid_fraction',1) or 0) for r in rows]); den=den*(.90+.10*np.clip(valid,0,1)); s=.10*robust(raw)+.60*robust(den)+.30*robust(area); order=sorted(range(len(rows)),key=lambda i:(-float(s[i]),int(rows[i].get('container_index',i)))); rank=[0]*len(rows)
 for n,i in enumerate(order,1):rank[i]=n
 return [{'frame_id':r['frame_id'],'container_index':r.get('container_index',i),'bbox':r['bbox'],'h041b_raw':float(s[i]),'h041b_rank':rank[i],'source_features':{'highlight_raw':float(raw[i]),'density':float(den[i]),'log1p_area':float(area[i])}} for i,r in enumerate(rows)]
