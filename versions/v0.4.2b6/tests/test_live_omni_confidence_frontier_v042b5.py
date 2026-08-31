import json,unittest
from pathlib import Path
class TestFrontierContract(unittest.TestCase):
 def test_matrix_locked(self):
  x=json.loads((Path(__file__).parents[1]/'config/live_omni_confidence_frontier_v042b5.json').read_text()); self.assertEqual([p['confidence'] for p in x['profiles']],[.25,.20,.15,.10]); self.assertEqual(x['production_config_locked'],{'confidence':.25,'imgsz':640,'nms_iou':.7})
 def test_diagnostic_labels(self):
  x=(Path(__file__).parents[1]/'scripts/run_live_omni_confidence_frontier_v042b5.py').read_text(); self.assertIn('POST_HOC_DIAGNOSTIC_ONLY',x); self.assertIn('run_v042b4.py',x)
 def test_formal_and_diagnostic_separate(self): self.assertIn('NOT_A_RETROACTIVE_CHANGE_TO_FORMAL_B4_SCORE',(Path(__file__).parents[1]/'scripts/evaluate_live_omni_confidence_frontier_v042b5.py').read_text())
if __name__=='__main__': unittest.main()
