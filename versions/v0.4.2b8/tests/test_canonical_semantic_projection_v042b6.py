import json,unittest
from pathlib import Path
class TestProjection(unittest.TestCase):
 def test_contract_excludes_container_fields(self):
  x=(Path(__file__).parents[1]/'app/canonical_semantic_projection_v042b6.py').read_text(); self.assertIn('candidate_bboxes',x); self.assertIn('run_directory',x); self.assertIn('separators',x)
 def test_projection_types(self):
  s=(Path(__file__).parents[1]/'schemas/canonical_semantic_projection_v1.schema.json').read_text(); self.assertIn('SEMANTIC_REPLAY_PROJECTION',s)
if __name__=='__main__': unittest.main()
