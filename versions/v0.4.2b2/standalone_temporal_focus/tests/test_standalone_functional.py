import unittest,sys
from pathlib import Path
import numpy as np,cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vlm_distill.temporal_focus_resolver_v041g6 import resolve_temporal_focus_encoded
class FunctionalTest(unittest.TestCase):
    def test_causal(self):
        a=np.zeros((64,64,3),np.uint8); b=a.copy(); b[20:40,20:40]=255
        ok,enc=cv2.imencode('.jpg',a); ok2,enc2=cv2.imencode('.jpg',b)
        r=resolve_temporal_focus_encoded(enc.tobytes(),enc2.tobytes(),[{'candidate_id':'x','bbox':[20,20,40,40]}])
        self.assertEqual(r['status'],'OK'); self.assertIsNotNone(r['focused_bbox']); self.assertTrue(r['frozen_e_numeric_parity_capable'])
if __name__=='__main__':unittest.main()
