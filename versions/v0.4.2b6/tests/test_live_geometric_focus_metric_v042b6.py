import json,unittest
from pathlib import Path
class TestMetric(unittest.TestCase):
 def test_metric_is_parallel(self):
  x=json.loads((Path(__file__).parents[1]/'config/live_geometric_focus_metric_v042b6.json').read_text()); self.assertEqual(x['metric_id'],'LIVE_GEOMETRIC_FOCUS_METRIC_V1'); self.assertEqual(x['iou_threshold'],.75); self.assertIn('NOT_A_RETROACTIVE_CHANGE_TO_FORMAL_SCORE',x['status'])
 def test_frame_id_join(self): self.assertIn('frame_id_dictionary',(Path(__file__).parents[1]/'scripts/evaluate_live_geometric_focus_metric_v042b6.py').read_text())
if __name__=='__main__': unittest.main()
