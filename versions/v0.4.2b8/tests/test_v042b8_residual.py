import json, unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class TestB8Residual(unittest.TestCase):
 def test_locked_profiles(self):
  c=json.loads((ROOT/'config/residual_rank_refinement_v042b8.json').read_text()); self.assertEqual(c['baseline_profile']['confidence'],.20); self.assertEqual(c['production_reference']['confidence'],.25); self.assertTrue(c['global_only']); self.assertFalse(c['gt_features_used'])
 def test_formula_is_global(self):
  from app.dev020_residual_rank_refinement_v042b8 import rank
  self.assertEqual(len(rank([{'bbox':[0,0,1,1]},{'bbox':[1,1,2,2]}],[{'h041b_raw':1},{'h041b_raw':0}], 'baseline_frozen_h')),2)
if __name__=='__main__':unittest.main()
