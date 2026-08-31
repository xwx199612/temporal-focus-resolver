#!/usr/bin/env python3
"""Official-provider trace boundary; never reimplements YOLO decode/NMS."""
from __future__ import annotations
import inspect, json, time
from pathlib import Path
from standalone_omni_bridge.official_provider import OfficialOmniIconProvider

class PreNMSDiagnosticProvider:
    def __init__(self,*args,**kwargs):
        self.provider=OfficialOmniIconProvider(*args,**kwargs)
        source=Path(self.provider.omni_root)/'util/yolov9.py'
        self.source_trace={'provider_class':'OfficialOmniIconProvider','callable':'detect_encoded','official_source':str(source),'source_sha256':__import__('hashlib').sha256(source.read_bytes()).hexdigest(),'interception_stage':'postprocess output returned by official provider','pre_nms_materializable':False,'decision':'PRE_NMS_NOT_MATERIALIZABLE_FROM_OFFICIAL_PATH','blocking_point':'official provider exposes result.boxes after detector.predict; raw tensor/pre-NMS proposals are not part of its public return contract','reimplementation_used':False}
    def detect_encoded_with_trace(self,encoded):
        t=time.perf_counter(); result=self.provider.detect_encoded(encoded); trace={'stage':'POST_NMS_BOXES_EXPOSED_BY_OFFICIAL_PROVIDER','elapsed_seconds':time.perf_counter()-t,'proposal_count':len(result.get('raw_records',[])),'production_config':{'confidence':self.provider.confidence,'imgsz':self.provider.imgsz,'iou':self.provider.iou},'pre_nms':self.source_trace,'raw_records':result.get('raw_records',[])}
        return result,trace
def write_trace(path,trace): Path(path).write_text(json.dumps(trace,sort_keys=True,indent=2)+'\n')
