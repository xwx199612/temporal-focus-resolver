import unittest
from pathlib import Path
class TestStandalone(unittest.TestCase):
 def test_required_files(self):
  r=Path(__file__).parents[1]
  for f in ['README.md','VERSION.json','self_test.py','release_manifest.py','scripts/run_live_omni_candidate_recall_v042b7.py'] : self.assertTrue((r/f).exists(),f)
if __name__=='__main__':unittest.main()
