import unittest
from pathlib import Path
class TestHReadOnly(unittest.TestCase):
 def test_no_production_change_marker(self): self.assertIn('NO_PRODUCTION_CHANGE_APPLIED',(Path(__file__).parents[1]/'characterize_h_ranking_failures_readonly_v042b4.py').read_text())
if __name__=='__main__': unittest.main()
