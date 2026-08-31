import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vlm_distill.temporal_focus_image_input_v1 import decode_temporal_focus_image
class DecodeTest(unittest.TestCase):
    def test_invalid(self):
        with self.assertRaises(ValueError): decode_temporal_focus_image(b'not-an-image')
if __name__=='__main__':unittest.main()
