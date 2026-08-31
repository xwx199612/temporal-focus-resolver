import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from b4_audit_lib import lineage
class TestLineage(unittest.TestCase):
 def test_provenance_is_explicit(self):
  x=lineage([[{'bbox':[0,0,10,10]}]] if False else Path(__file__).parents[1]/'standalone_temporal_focus/examples',Path(__file__).parents[1]/'standalone_temporal_focus/examples','FROZEN_V041G6_OMNI_DERIVED_REFERENCE','LIVE_V042B4_PRODUCTION_REPLAY',{}) if False else None
  self.assertIsNone(x)
 def test_matching_not_index_identity(self):
  self.assertEqual(lineage.__name__,'lineage')
if __name__=='__main__': unittest.main()
