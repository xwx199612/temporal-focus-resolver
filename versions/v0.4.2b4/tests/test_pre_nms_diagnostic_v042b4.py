import unittest
from pathlib import Path
class TestPreNMS(unittest.TestCase):
 def test_contract(self):
  text=(Path(__file__).parents[1]/'live_omni_pre_nms_diagnostic_provider_v042b4.py').read_text()
  self.assertIn('PRE_NMS_NOT_MATERIALIZABLE_FROM_OFFICIAL_PATH',text); self.assertIn('reimplementation_used',text)
 def test_sweep_is_nonproduction(self):
  text=(Path(__file__).parents[1]/'diagnose_omni_pre_nms_boundary_v042b4.py').read_text()
  for s in ('POST_HOC_DIAGNOSTIC_ONLY','NOT_FORMAL_CANDIDATES','NOT_USED_FOR_PREDICTION'): self.assertIn(s,text)
if __name__=='__main__': unittest.main()
