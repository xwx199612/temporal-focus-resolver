"""Frozen g4 feature routing with an independent direct grayscale E plane."""
from __future__ import annotations
import statistics, cv2, numpy as np
from .temporal_focus_features_v041g4 import _geom, materialize_h_features, materialize_directional_features
from .spatial_focus_scorer_v040 import score_frame
def _flow_gray(prev_gray,cur_gray):
    f=cv2.calcOpticalFlowFarneback(prev_gray,cur_gray,None,.5,3,21,3,5,1.2,0); b=cv2.calcOpticalFlowFarneback(cur_gray,prev_gray,None,.5,3,21,3,5,1.2,0); h,w=f.shape[:2]; yy,xx=np.mgrid[0:h,0:w].astype(np.float32); bx=cv2.remap(b[...,0],xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR); by=cv2.remap(b[...,1],xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR); err=np.sqrt((f[...,0]+bx)**2+(f[...,1]+by)**2); return b,np.isfinite(err)&(err<3),err
def materialize_e_features(previous_rgb,current_rgb,candidates,h_result=None,previous_gray_e=None,current_gray_e=None):
    if previous_gray_e is None or current_gray_e is None: raise ValueError('g6 E producer requires direct grayscale planes')
    back,valid,err=_flow_gray(previous_gray_e,current_gray_e); _,base,_=score_frame(previous_rgb,current_rgb,[c['bbox'] for c in candidates]); out=[]
    for c,b in zip(candidates,base):
        g=_geom(c['bbox'],back,valid,err); raw=float(b['enlargement_raw']); out.append({**c,**g,'portable_e_raw_v040a':raw,'enlargement_raw':raw,'gray_input_profile':'DIRECT_GRAYSCALE_FROM_ENCODED_BYTES'})
    vals=[x['enlargement_raw'] for x in out]; order=sorted(range(len(out)),key=lambda i:(-vals[i],int(out[i].get('container_index',i)))); ranks=[0]*len(out)
    for n,i in enumerate(order,1):ranks[i]=n
    med=statistics.median(vals) if vals else 0.; mad=statistics.median(abs(x-med) for x in vals) if vals else 0.; scale=1.4826*mad
    if scale==0 and len(vals)>=4:
        q=statistics.quantiles(vals,n=4);scale=(q[2]-q[0])/1.349
    if scale==0:scale=statistics.pstdev(vals) if vals else 0.
    gap=(vals[order[0]]-vals[order[1]])/scale if scale and len(order)>1 else None
    for i,x in enumerate(out): x.update({'e_rank':ranks[i],'e_gap_z':gap,'physical_strong':x.get('status')=='LOCAL_AFFINE_VALID' and x.get('flow_valid_fraction',0)>=.5 and x.get('local_affine_inlier_fraction',0)>=.5 and x.get('area_scale',0)>1.03 and x.get('bilateral_outward_support',0)>=.5 and x.get('radial_consistency',0)>=.5 and x.get('condition_number',999)<100 and x.get('diagnostic_class') in ('BILATERAL_SCALE','RADIAL_SCALE')})
    return out
