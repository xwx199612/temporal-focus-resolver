"""Side-effect-free extraction of the frozen v0.4.1 temporal features.

The arithmetic is mechanically copied from the v040 scorer, the v041b H
module, the v031e2s1 physical enlargement producer, and the v041f RGB
characterization producer.  No artifact or identity is read here.
"""
from __future__ import annotations
import math, statistics
import cv2, numpy as np
from .spatial_focus_scorer_v040 import score_frame
from .spatial_focus_scorer_v041b import score_h041b

FLOW=(.5,3,21,3,5,1.2)
def _flow_pair(prev, cur):
    a=cv2.cvtColor(prev,cv2.COLOR_RGB2GRAY); b=cv2.cvtColor(cur,cv2.COLOR_RGB2GRAY)
    f=cv2.calcOpticalFlowFarneback(a,b,None,*FLOW,0); back=cv2.calcOpticalFlowFarneback(b,a,None,*FLOW,0)
    h,w=f.shape[:2]; yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    bx=cv2.remap(back[...,0],xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR); by=cv2.remap(back[...,1],xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR)
    err=np.sqrt((f[...,0]+bx)**2+(f[...,1]+by)**2)
    return f,back,np.isfinite(err)&(err<3),err
def _geom(box,back,valid,err):
    h,w=valid.shape; x1=max(0,int(box[0])); y1=max(0,int(box[1])); x2=min(w-1,int(box[2])); y2=min(h-1,int(box[3]))
    xs=np.linspace(x1,x2,min(24,max(2,x2-x1+1))).astype(int); ys=np.linspace(y1,y2,min(24,max(2,y2-y1+1))).astype(int)
    pts=np.array([(x,y) for y in ys for x in xs],np.float32); ix=np.clip(pts[:,0].astype(int),0,w-1); iy=np.clip(pts[:,1].astype(int),0,h-1); ok=valid[iy,ix]; p=pts[ok]; ev=float(ok.mean()) if len(ok) else 0.
    base={'sample_count':int(len(pts)),'valid_sample_count':int(len(p)),'flow_valid_fraction':ev,'median_forward_backward_error':float(np.median(err[iy,ix])) if len(pts) else None}
    if len(p)<6:return {**base,'status':'LOCAL_AFFINE_UNAVAILABLE'}
    prev=p+back[iy[ok],ix[ok]]; A,ins=cv2.estimateAffine2D(p,prev,method=cv2.LMEDS,ransacReprojThreshold=3.,maxIters=2000,confidence=.99,refineIters=10)
    ins=ins.ravel().astype(bool) if ins is not None else np.zeros(len(p),bool)
    if A is None:return {**base,'status':'LOCAL_AFFINE_UNAVAILABLE'}
    lin=A[:,:2]; det=float(np.linalg.det(lin)); cond=float(np.linalg.cond(lin))
    if not np.isfinite(cond) or cond>1e4 or abs(det)<1e-5:return {**base,'status':'LOCAL_AFFINE_UNAVAILABLE','raw_backward_matrix':A.tolist(),'condition_number':cond}
    F=np.linalg.inv(lin); _,s,_=np.linalg.svd(F); sx,sy=float(s[0]),float(s[1]); area=abs(float(np.linalg.det(F))); anis=max(sx,sy)/max(min(sx,sy),1e-9)
    pred=p@A[:,:2].T+A[:,2]; resid=p-prev; translation=np.median(resid,axis=0); deform=resid-translation; cx=(box[0]+box[2])/2; cy=(box[1]+box[3])/2; sides={k:[] for k in ('left','right','top','bottom')}; rad=[]
    for q,d in zip(p,deform):
        dx=q[0]-cx; dy=q[1]-cy; rad.append(float(np.dot(d,np.array([dx,dy])/max(math.hypot(dx,dy),1e-9))))
        if abs(q[0]-box[0])<=max(2,(box[2]-box[0])*.12): sides['left'].append(float(-d[0]))
        if abs(q[0]-box[2])<=max(2,(box[2]-box[0])*.12): sides['right'].append(float(d[0]))
        if abs(q[1]-box[1])<=max(2,(box[3]-box[1])*.12): sides['top'].append(float(-d[1]))
        if abs(q[1]-box[3])<=max(2,(box[3]-box[1])*.12): sides['bottom'].append(float(d[1]))
    med=lambda z:float(np.median(z)) if z else None
    left,right,top,bottom=[med(sides[k]) for k in ('left','right','top','bottom')]; bil=sum(x is not None and x>0 for x in (left,right,top,bottom))/4; coh=sum(x>0 for x in rad)/max(1,len(rad)); rmed=med(rad)
    return {**base,'status':'LOCAL_AFFINE_VALID','p90_forward_backward_error':float(np.quantile(err[iy,ix],.9)),'raw_backward_matrix':A.tolist(),'forward_linear_matrix':F.tolist(),'scale_x':sx,'scale_y':sy,'area_scale':area,'rotation_radians':float(math.atan2(F[1,0],F[0,0])),'shear':float(F[0,1]+F[1,0]),'condition_number':cond,'local_affine_inlier_fraction':float(ins.mean()),'local_affine_residual_median':float(np.median(np.linalg.norm(pred-prev,axis=1))),'translation_removed':translation.tolist(),'left_outward_median':left,'right_outward_median':right,'top_outward_median':top,'bottom_outward_median':bottom,'horizontal_expansion':left+right if left is not None and right is not None else None,'vertical_expansion':top+bottom if top is not None and bottom is not None else None,'horizontal_support_valid':left is not None and right is not None,'vertical_support_valid':top is not None and bottom is not None,'positive_radial_fraction':coh,'median_radial_projection':rmed,'radial_projection_MAD':float(np.median([abs(x-rmed) for x in rad])) if rad else None,'radial_consistency':coh,'anisotropy_ratio':anis,'diagnostic_class':'BILATERAL_SCALE' if bil>=.75 and area>1 else 'RADIAL_SCALE' if coh>=.7 and area>1 else 'ONE_AXIS_ONLY_DEFORMATION' if area>1 and max(left or 0,right or 0,top or 0,bottom or 0)>0 else 'TRANSLATION_DOMINATED','bilateral_outward_support':bil}
def materialize_h_features(current_rgb, candidates, previous_rgb=None):
    """Return v041b H rows; previous_rgb is required by v040 H raw."""
    if previous_rgb is None: raise ValueError('H raw producer requires previous_rgb')
    boxes=[c['bbox'] for c in candidates]; _,rows,_=score_frame(previous_rgb,current_rgb,boxes)
    # The frozen helper serializes a frame_id, but ranking is frame-local and
    # must not consume identity.  An anonymous sentinel keeps the API pure.
    rows=[{'frame_id':'__anonymous__',**r} for r in rows]
    scored=score_h041b(rows)
    return [{**c,**r,'width':c['bbox'][2]-c['bbox'][0],'height':c['bbox'][3]-c['bbox'][1],'area':(c['bbox'][2]-c['bbox'][0])*(c['bbox'][3]-c['bbox'][1])} for c,r in zip(candidates,scored)]
def materialize_e_features(previous_rgb,current_rgb,candidates,h_rows=None):
    _,back,valid,err=_flow_pair(previous_rgb,current_rgb); _,base_rows,stats=score_frame(previous_rgb,current_rgb,[c['bbox'] for c in candidates]); out=[]
    for c,b in zip(candidates,base_rows):
        g=_geom(c['bbox'],back,valid,err); raw=float(b['enlargement_raw']); out.append({**c,**g,'portable_e_raw_v040a':raw,'enlargement_raw':raw})
    vals=[x['portable_e_raw_v040a'] for x in out]; order=sorted(range(len(out)),key=lambda i:(-vals[i],int(out[i].get('container_index',i)))); ranks=[0]*len(out)
    for n,i in enumerate(order,1):ranks[i]=n
    med=statistics.median(vals); mad=statistics.median(abs(x-med) for x in vals); scale=1.4826*mad
    if scale==0 and len(vals)>=4:
        q=statistics.quantiles(vals,n=4); scale=(q[2]-q[0])/1.349
    if scale==0: scale=statistics.pstdev(vals)
    gap=(vals[order[0]]-vals[order[1]])/scale if scale and len(order)>1 else None
    for i,x in enumerate(out): x.update({'e_rank':ranks[i],'e_gap_z':gap,'physical_strong':x.get('status')=='LOCAL_AFFINE_VALID' and x.get('flow_valid_fraction',0)>=.5 and x.get('local_affine_inlier_fraction',0)>=.5 and x.get('area_scale',0)>1.03 and x.get('bilateral_outward_support',0)>=.5 and x.get('radial_consistency',0)>=.5 and x.get('condition_number',999)<100 and x.get('diagnostic_class') in ('BILATERAL_SCALE','RADIAL_SCALE')})
    return out
def _patch_stats(im,prev,b):
    h,w=im.shape[:2]; x1,y1,x2,y2=[int(round(float(x))) for x in b]; x1=max(0,min(w-1,x1));x2=max(x1+1,min(w,x2));y1=max(0,min(h-1,y1));y2=max(y1+1,min(h,y2)); ring=max(1,int(round(.10*max(x2-x1,y2-y1))) ); a=im[y1:y2,x1:x2].astype(np.float32);q=prev[y1:y2,x1:x2].astype(np.float32);rx1=max(0,x1-ring);ry1=max(0,y1-ring);rx2=min(w,x2+ring);ry2=min(h,y2+ring); rp=im[ry1:ry2,rx1:rx2].astype(np.float32);rprev=prev[ry1:ry2,rx1:rx2].astype(np.float32);Y=np.array([.2126,.7152,.0722],np.float32); ay=a@Y;qy=q@Y;dy=ay-qy;rY=rp@Y;rq=rprev@Y; dcol=np.linalg.norm(a-q,axis=2); gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY).astype(np.float32); pgray=cv2.cvtColor(prev,cv2.COLOR_RGB2GRAY).astype(np.float32); gx,gy=cv2.Sobel(gray,cv2.CV_32F,1,0),cv2.Sobel(gray,cv2.CV_32F,0,1);pgx,pgy=cv2.Sobel(pgray,cv2.CV_32F,1,0),cv2.Sobel(pgray,cv2.CV_32F,0,1);de=np.hypot(gx,gy)[y1:y2,x1:x2]-np.hypot(pgx,pgy)[y1:y2,x1:x2]; pos=float(np.maximum(dy,0).mean()); neg=float(np.maximum(-dy,0).mean()); ep=float(np.maximum(de,0).mean()); en=float(np.maximum(-de,0).mean());
    return {'mean_delta_y':float(dy.mean()),'positive_luma_mass':pos,'negative_luma_mass':neg,'luma_polarity_balance':float((pos-neg)/(float(np.abs(dy).mean())+1e-9)),'positive_edge_onset_mass':ep,'negative_edge_offset_mass':en,'delta_border_gradient_energy':float(de.mean()),'interior_ring_luma_contrast_delta':float(abs(ay.mean()-rY.mean())-abs(qy.mean()-rq.mean())),'valid':bool(a.size and rp.size)}
def materialize_directional_features(previous_rgb,current_rgb,candidates,h_result=None,e_result=None):
    # v041f used cv2 BGR source arrays; preserve that frozen numeric convention.
    cur=cv2.cvtColor(current_rgb,cv2.COLOR_RGB2BGR); prev=cv2.cvtColor(previous_rgb,cv2.COLOR_RGB2BGR)
    return [{**c,'transition':_patch_stats(cur,prev,c['bbox'])} for c in candidates]
