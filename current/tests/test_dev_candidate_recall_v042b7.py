import json, unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class TestB7(unittest.TestCase):
 def test_profiles_are_explicit_and_locked(self):
  c=json.loads((ROOT/'config/dev_candidate_recall_v042b7.json').read_text()); self.assertTrue(c['explicit_profile_required']); self.assertEqual(c['profiles']['production_reference_025']['confidence'],.25); self.assertEqual(c['profiles']['dev_candidate_recall_020']['confidence'],.20)
 def test_no_old_version_mutation_in_artifact(self): self.assertTrue((ROOT/'scripts/run_live_omni_candidate_recall_v042b7.py').exists())
if __name__=='__main__':unittest.main()
