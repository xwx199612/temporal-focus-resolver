import json,unittest
from pathlib import Path
class TestStandalone(unittest.TestCase):
 def test_version(self): self.assertEqual(json.loads((Path(__file__).parents[1]/'VERSION.json').read_text())['version'],'0.4.2b6')
 def test_no_canonical_import(self):
  text='\n'.join(p.read_text(errors='ignore') for p in Path(__file__).parents[1].rglob('*.py')); self.assertNotIn('temporal_focus_resolver.',text)
if __name__=='__main__': unittest.main()
