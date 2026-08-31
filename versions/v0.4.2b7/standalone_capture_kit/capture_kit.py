"""Portable capture/session/annotation/sealing helpers (standard library)."""
from __future__ import annotations
import hashlib,json,shutil,subprocess,time
from pathlib import Path
def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def write_json(p,x): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def import_images(input_dir,order_manifest,session_id,family,role,out):
 if role not in {'dev','holdout','unassigned'}: raise ValueError('invalid role')
 order=[]
 for line in Path(order_manifest).read_text().splitlines():
  if line.strip():
   x=json.loads(line); order.append(x.get('path',x.get('filename',x.get('frame_id'))))
 if not order: raise ValueError('explicit order manifest is empty')
 frames=[]
 for i,item in enumerate(order):
  src=Path(item); src=src if src.is_absolute() else Path(input_dir)/src
  if not src.exists(): raise FileNotFoundError(src)
  dst=Path(out)/'frames'/f'{i:06d}_{src.name}'; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
  frames.append({'session_id':session_id,'sequence_id':session_id,'frame_id':dst.name,'frame_index':i,'capture_session_family':family,'capture_method':'import-images','source_description':'original encoded bytes copied without resize/crop/re-encode','captured_at':time.time(),'encoded_image_path':str(dst.resolve()),'image_sha256':sha(dst),'dataset_role':role,'bootstrap':i==0,'transition_context':None,'camera_motion':None})
 write_json(Path(out)/'session_manifest.json',{'session_id':session_id,'sequence_id':session_id,'capture_session_family':family,'dataset_role':role,'frames':frames,'sealed':False}); return frames
def extract_video(video,out,indices):
 import cv2
 cap=cv2.VideoCapture(str(video)); frames=[]; wanted=set(indices)
 i=0
 while True:
  ok,im=cap.read()
  if not ok: break
  if i in wanted:
   p=Path(out)/'frames'/f'{i:06d}.png'; p.parent.mkdir(parents=True,exist_ok=True); cv2.imwrite(str(p),im); frames.append({'frame_index':i,'encoded_image_path':str(p),'source_video_sha256':sha(video),'capture_method':'extract-video'})
  i+=1
 cap.release(); return frames
def adb_screencap(out):
 try: b=subprocess.check_output(['adb','exec-out','screencap','-p'])
 except FileNotFoundError: return {'status':'ADB_UNAVAILABLE'}
 except subprocess.CalledProcessError as e: return {'status':'ADB_CAPTURE_FAILED','error':str(e)}
 p=Path(out)/'frames'/'000000_adb.png'; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b); return {'status':'OK','path':str(p),'sha256':sha(p),'capture_method':'adb-screencap'}
def prepare_annotation(session):
 s=json.loads((Path(session)/'session_manifest.json').read_text()); out=[]
 for f in s['frames']:
  cfile=Path(session)/'omni'/(f['frame_id']+'.json'); cs=[]
  if cfile.exists(): cs=json.loads(cfile.read_text()).get('anonymous_candidates',[])
  out.append({'frame_id':f['frame_id'],'sequence_id':s['sequence_id'],'frame_index':f['frame_index'],'candidates':cs,'prediction_visible':False})
 write_json(Path(session)/'annotation_material.json',out); return out
def annotate(session,frame_id,candidate_id,focus_type,note=''):
 if focus_type not in {'HIGHLIGHT','ENLARGEMENT','OUTLINE'}: raise ValueError('invalid focus type')
 p=Path(session)/'annotation_gt.jsonl'; s=json.loads((Path(session)/'session_manifest.json').read_text()); f=next(x for x in s['frames'] if x['frame_id']==frame_id); c=next((x for x in json.loads((Path(session)/'omni'/(frame_id+'.json')).read_text()).get('anonymous_candidates',[]) if x['candidate_id']==candidate_id),None)
 if c is None: raise ValueError('candidate not found')
 row={'frame_id':frame_id,'sequence_id':s['sequence_id'],'frame_index':f['frame_index'],'focus_type':focus_type,'authoritative_focus_bbox':c['bbox'],'authoritative_candidate_id':candidate_id,'gt_candidate_match':True,'transition_context':None,'camera_motion':None,'annotator_note':note,'annotation_timestamp':time.time()}
 with p.open('a') as q:q.write(json.dumps(row,sort_keys=True)+'\n')
 return row
def seal(session,g6_sha):
 p=Path(session); s=json.loads((p/'session_manifest.json').read_text()); fam=s['capture_session_family']; role=s['dataset_role']
 if role not in {'dev','holdout'}: raise ValueError('session role must be dev or holdout before sealing')
 pred=p/'predictions.jsonl'; omni=p/'omni_manifest.json';
 if not pred.exists() or not omni.exists(): raise ValueError('prediction and Omni outputs required')
 seal={'session_id':s['session_id'],'dataset_role':role,'capture_session_family':fam,'rgb_manifest_sha256':sha(p/'session_manifest.json'),'omni_manifest_sha256':sha(omni),'g6_manifest_sha256':g6_sha,'prediction_sha256':sha(pred),'sealed_at':time.time(),'gt_loaded_before_seal':False}
 write_json(p/'prediction_seal.json',seal); s['sealed']=True; write_json(p/'session_manifest.json',s); return seal
