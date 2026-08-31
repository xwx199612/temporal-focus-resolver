"""Self-contained official OmniParser icon_detect_v3 provider boundary."""
from __future__ import annotations
import hashlib, importlib.util, io, sys, time
from pathlib import Path

class OfficialOmniIconProvider:
    def __init__(self, omni_root, checkpoint_path, confidence=0.25, imgsz=640, iou=0.70, device=None):
        self.omni_root=Path(omni_root).resolve(); self.checkpoint_path=Path(checkpoint_path).resolve()
        self.confidence=float(confidence); self.imgsz=int(imgsz); self.iou=float(iou)
        if not self.checkpoint_path.is_file() or self.checkpoint_path.stat().st_size<=0: raise FileNotFoundError(self.checkpoint_path)
        source=self.omni_root/'util/yolov9.py'
        if not source.is_file(): raise FileNotFoundError(source)
        if str(self.omni_root) not in sys.path: sys.path.insert(0,str(self.omni_root))
        try: import torchvision.ops  # noqa: F401
        except Exception:
            import types, torch
            def batched_nms(boxes,scores,classes,threshold):
                keep=[]
                for cls in torch.unique(classes):
                    ids=torch.where(classes==cls)[0]; order=ids[torch.argsort(scores[ids],descending=True)]
                    while order.numel():
                        i=int(order[0]); keep.append(i)
                        if order.numel()==1: break
                        b=boxes[order[1:]]; q=boxes[i]
                        xx1=torch.maximum(q[0],b[:,0]); yy1=torch.maximum(q[1],b[:,1]); xx2=torch.minimum(q[2],b[:,2]); yy2=torch.minimum(q[3],b[:,3])
                        inter=torch.clamp(xx2-xx1,min=0)*torch.clamp(yy2-yy1,min=0); qa=(q[2]-q[0])*(q[3]-q[1]); ba=(b[:,2]-b[:,0])*(b[:,3]-b[:,1]); overlap=inter/(qa+ba-inter+1e-8); order=order[1:][overlap<=threshold]
                return torch.tensor(keep,device=boxes.device,dtype=torch.long)
            tv=types.ModuleType('torchvision'); ops=types.ModuleType('torchvision.ops'); ops.batched_nms=batched_nms; tv.ops=ops
            old_tv=sys.modules.get('torchvision'); old_ops=sys.modules.get('torchvision.ops'); sys.modules['torchvision']=tv; sys.modules['torchvision.ops']=ops
        spec=importlib.util.spec_from_file_location('v042b1_official_yolov9',source); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.detector=mod.YOLOv9Detector(model_path=str(self.checkpoint_path),device=device or ('cuda' if __import__('torch').cuda.is_available() else 'cpu'))
        self.device=device or ('cuda' if __import__('torch').cuda.is_available() else 'cpu'); self.model_loaded=True
    def detect_encoded(self, encoded_image_bytes):
        if not encoded_image_bytes: raise ValueError('empty encoded image')
        from PIL import Image
        image=Image.open(io.BytesIO(bytes(encoded_image_bytes))).convert('RGB'); start=time.perf_counter()
        result=self.detector.predict(source=image,conf=self.confidence,imgsz=self.imgsz,iou=self.iou)[0]
        boxes=result.boxes.xyxy.detach().cpu().tolist(); scores=result.boxes.conf.detach().cpu().tolist(); rows=[]
        for i,(box,score) in enumerate(zip(boxes,scores)):
            b=[float(x) for x in box]; x1,y1,x2,y2=b
            if not (0<=x1<x2<=image.width and 0<=y1<y2<=image.height): raise ValueError('out-of-range detector bbox')
            rows.append({'candidate_id':f'omni:{i}','bbox':b,'confidence':float(score),'bbox_format':'xyxy_pixel','image_width':image.width,'image_height':image.height})
        return {'provider':'MICROSOFT_OMNIPARSER','detector':'YOLOv9-E icon_detect_v3','width':image.width,'height':image.height,'raw_records':rows,'anonymous_candidates':[{'candidate_id':x['candidate_id'],'bbox':x['bbox']} for x in rows],'elapsed_seconds':time.perf_counter()-start}
