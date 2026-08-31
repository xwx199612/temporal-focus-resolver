"""Portable v0.4.0a spatial Focus scorer.

This module is a new algorithm lineage.  It intentionally does not import or
read any historical Focus score tables.  All public functions are pure with
respect to their image/flow/container inputs.
"""
from __future__ import annotations
import math, statistics
import cv2, numpy as np

EPS=1e-9
FLOW_PARAMS=dict(pyr_scale=.5, levels=3, winsize=21, iterations=3, poly_n=5, poly_sigma=1.2)
RULES={'flow_consistency_px':3.0,'sample_grid':24,'context_pad_fraction':.15,'edge_band_fraction':.08,'h_strong_percentile':90.0,'e_min_area_scale':1.01}

def _flow(a,b): return cv2.calcOpticalFlowFarneback(a,b,None,**FLOW_PARAMS,flags=0)
def motion_pair(previous_rgb,current_rgb):
    pa=cv2.cvtColor(previous_rgb,cv2.COLOR_RGB2GRAY); ca=cv2.cvtColor(current_rgb,cv2.COLOR_RGB2GRAY)
    f=_flow(pa,ca); b=_flow(ca,pa); h,w=pa.shape; yy,xx=np.mgrid[:h,:w].astype(np.float32)
    bx=cv2.remap(b[...,0],xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR); by=cv2.remap(b[...,1],xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR)
    err=np.sqrt((f[...,0]+bx)**2+(f[...,1]+by)**2); valid=np.isfinite(err)&(err<=RULES['flow_consistency_px'])
    warped=cv2.remap(previous_rgb,xx+f[...,0],yy+f[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    return {'forward_flow':f,'backward_flow':b,'flow_error':err,'valid_mask':valid,'warped_previous_rgb':warped,'valid_warp_mask':valid.copy(),'global_motion':np.median(f[valid],axis=0).tolist() if valid.any() else [0.,0.]}
def _gray(x): return cv2.cvtColor(x,cv2.COLOR_RGB2GRAY).astype(np.float32)/255.
def highlight_field(previous_rgb,current_rgb,m):
    cur=current_rgb.astype(np.float32)/255.; old=m['warped_previous_rgb'].astype(np.float32)/255.
    color=np.linalg.norm(cur-old,axis=2)/math.sqrt(3); luma=np.abs(_gray(current_rgb)-_gray(m['warped_previous_rgb']))
    gc=cv2.Laplacian(_gray(current_rgb),cv2.CV_32F); go=cv2.Laplacian(_gray(m['warped_previous_rgb']),cv2.CV_32F); grad=np.abs(gc-go)
    def norm(z):
        q=float(np.percentile(z[m['valid_mask']],95)) if m['valid_mask'].any() else 1.; return np.clip(z/max(q,EPS),0,1)
    field=.45*norm(color)+.35*norm(luma)+.20*norm(grad); field[~m['valid_mask']]=0
    return field.astype(np.float32),{'color_residual':color,'luma_residual':luma,'gradient_residual':grad}
def _inside(b,h,w,pad=0):
    x1=max(0,int(math.floor(b[0]-pad)));y1=max(0,int(math.floor(b[1]-pad)));x2=min(w,int(math.ceil(b[2]+pad)));y2=min(h,int(math.ceil(b[3]+pad)));return x1,y1,x2,y2
def pool_field(field,valid,b):
    h,w=field.shape;x1,y1,x2,y2=_inside(b,h,w); crop=field[y1:y2,x1:x2]; vm=valid[y1:y2,x1:x2]
    if crop.size==0:return {'mass':0.,'density':0.,'support_fraction':0.,'extent':0.,'quadrants':[0.,0.,0.,0.],'perimeter_support':0.,'valid_fraction':0.}
    threshold=float(np.percentile(crop[vm],75)) if vm.any() else float('inf'); support=(crop>=threshold)&vm
    cy,cx=np.array(crop.shape)//2; q=[support[:cy,:cx],support[:cy,cx:],support[cy:,:cx],support[cy:,cx:]]
    return {'mass':float(crop[vm].sum()) if vm.any() else 0.,'density':float(crop[vm].mean()) if vm.any() else 0.,'support_fraction':float(support.mean()),'extent':float(np.count_nonzero(support)/max(1,support.size)),'quadrants':[float(x.mean()) if x.size else 0. for x in q],'perimeter_support':float(np.mean(np.r_[crop[0,:],crop[-1,:],crop[:,0],crop[:,-1]])) if crop.size else 0.,'valid_fraction':float(vm.mean())}
def highlight_scores(field,valid,bboxes):
 ps=[pool_field(field,valid,b) for b in bboxes]; raw=np.array([.45*x['density']+.25*x['support_fraction']+.20*min(1,x['mass']/max(1,field.size*.01))+.10*np.mean(x['quadrants']) for x in ps],dtype=float);return raw.tolist(),ps
def _affine_for_bbox(back,valid,err,b):
 h,w=valid.shape;x1,y1,x2,y2=_inside(b,h,w); xs=np.linspace(x1,max(x1,x2-1),min(RULES['sample_grid'],max(2,x2-x1))).astype(int);ys=np.linspace(y1,max(y1,y2-1),min(RULES['sample_grid'],max(2,y2-y1))).astype(int);p=np.array([(x,y) for y in ys for x in xs],np.float32)
 if p.size==0:return {'status':'UNAVAILABLE','valid_fraction':0.}
 ok=valid[p[:,1].astype(int),p[:,0].astype(int)];p=p[ok]
 if len(p)<6:return {'status':'UNAVAILABLE','valid_fraction':float(ok.mean()) if len(ok) else 0.}
 prev=p+back[p[:,1].astype(int),p[:,0].astype(int)];A,ins=cv2.estimateAffine2D(p,prev,method=cv2.LMEDS,ransacReprojThreshold=3.,maxIters=2000,confidence=.99,refineIters=10)
 if A is None:return {'status':'UNAVAILABLE','valid_fraction':float(ok.mean())}
 try:F=np.linalg.inv(A[:,:2]); cond=float(np.linalg.cond(A[:,:2])); sv=np.linalg.svd(F,compute_uv=False)
 except np.linalg.LinAlgError:return {'status':'UNAVAILABLE','valid_fraction':float(ok.mean())}
 if not np.isfinite(cond) or cond>1e4:return {'status':'UNAVAILABLE','valid_fraction':float(ok.mean())}
 residual=(p@A[:,:2].T+A[:,2])-prev; trans=np.median(residual,axis=0); deform=residual-trans; cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;rad=[]
 for q,d in zip(p,deform):
  v=q-np.array([cx,cy]);rad.append(float(np.dot(d,v)/max(np.linalg.norm(v),EPS)))
 return {'status':'VALID','scale_x':float(sv[0]),'scale_y':float(sv[1]),'area_scale':abs(float(np.linalg.det(F))),'rotation':float(math.atan2(F[1,0],F[0,0])),'shear':float(F[0,1]+F[1,0]),'condition_number':cond,'inlier_fraction':float(ins.mean()) if ins is not None else 0.,'residual_median':float(np.median(np.linalg.norm(residual,axis=1))),'translation_removed':trans.tolist(),'positive_radial_fraction':float(np.mean(np.array(rad)>0)),'median_radial_projection':float(np.median(rad)),'radial_mad':float(np.median(np.abs(rad-np.median(rad)))),'valid_fraction':float(ok.mean())}
def enlargement_scores(m,bboxes):
 vals=[];diag=[]
 for b in bboxes:
  z=_affine_for_bbox(m['backward_flow'],m['valid_mask'],m['flow_error'],b);diag.append(z)
  if z.get('status')!='VALID':vals.append(0.);continue
  scale=max(0.,z['area_scale']-1.)*max(0.,z['positive_radial_fraction']); vals.append(float(scale*min(1.,z['inlier_fraction'])*z['valid_fraction']))
 return vals,diag
def outline_field(previous_rgb,current_rgb,m):
 a=cv2.Canny(cv2.cvtColor(m['warped_previous_rgb'],cv2.COLOR_RGB2GRAY),50,150).astype(np.float32)/255.;b=cv2.Canny(cv2.cvtColor(current_rgb,cv2.COLOR_RGB2GRAY),50,150).astype(np.float32)/255.;z=np.clip(b-a,0,1)*m['valid_mask'];return z.astype(np.float32)
def outline_scores(field,valid,bboxes): return [float(pool_field(field,valid,b)['mass']) for b in bboxes]
def ranks(values):
 order=sorted(range(len(values)),key=lambda i:(-float(values[i]),i));out=[0]*len(values)
 for r,i in enumerate(order,1):out[i]=r
 return out,order
def channel_stats(values):
 v=[float(x) for x in values];order=sorted(v,reverse=True);med=float(np.median(v)) if v else 0.;mad=float(np.median(np.abs(np.array(v)-med))) if v else 0.;scale=max(1.4826*mad,EPS);return {'winner':order[0] if order else None,'runner_up':order[1] if len(order)>1 else None,'median':med,'MAD':mad,'winner_gap':order[0]-order[1] if len(order)>1 else None,'winner_gap_z':(order[0]-order[1])/scale if len(order)>1 else None,'count':len(v)}
def score_frame(previous_rgb,current_rgb,bboxes):
 m=motion_pair(previous_rgb,current_rgb);hf,hparts=highlight_field(previous_rgb,current_rgb,m);h,hd=highlight_scores(hf,m['valid_mask'],bboxes);e,ed=enlargement_scores(m,bboxes);of=outline_field(previous_rgb,current_rgb,m);o=outline_scores(of,m['valid_mask'],bboxes);hr,ho=ranks(h);er,eo=ranks(e);orr,oo=ranks(o)
 rows=[]
 for i,b in enumerate(bboxes):rows.append({'container_index':i,'bbox':[float(x) for x in b],'highlight_raw':h[i],'enlargement_raw':e[i],'outline_raw':o[i],'highlight_rank':hr[i],'enlargement_rank':er[i],'outline_rank':orr[i],'highlight_pool':hd[i],'enlargement_physical':ed[i]})
 return m,rows,{'H':channel_stats(h),'E':channel_stats(e),'O':channel_stats(o),'H_winner':ho[0] if ho else None,'E_winner':eo[0] if eo else None,'O_winner':oo[0] if oo else None}
