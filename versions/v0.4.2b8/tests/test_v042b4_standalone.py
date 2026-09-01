import unittest
from pathlib import Path
class TestStandalone(unittest.TestCase):
 def test_no_canonical_import(self):
  root=Path(__file__).parents[1]
  text='\n'.join(p.read_text(errors='ignore') for p in root.rglob('*.py'))
  self.assertNotIn('import '+'temporal_focus_resolver',text)
 def test_version(self): self.assertEqual(__import__('json').loads((Path(__file__).parents[1]/'VERSION.json').read_text())['version'],'0.4.2b8')
if __name__=='__main__': unittest.main()
