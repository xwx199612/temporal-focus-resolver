import hashlib, json, shutil, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_manifest as rm

def test_no_self_reference_and_verify():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); shutil.copy2(rm.ROOT/'VERSION.json',root/'VERSION.json'); shutil.copy2(rm.ROOT/'FUNCTIONAL_CAPABILITIES.json',root/'FUNCTIONAL_CAPABILITIES.json')
        shutil.copy2(rm.ROOT/'README.md',root/'README.md'); old=rm.ROOT
        assert rm.write_release(root,'2026-08-31T00:00:00Z')['passed']
        assert rm.verify(root)['checks']['no_self_reference']

def test_payload_tamper_detection():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); (root/'payload.txt').write_text('good'); (root/'FUNCTIONAL_CAPABILITIES.json').write_text('{}'); rm.write_release(root)
        (root/'payload.txt').write_text('tampered'); assert not rm.verify(root)['passed']

def test_manifest_and_seal_tamper_detection():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); (root/'payload.txt').write_text('good'); (root/'FUNCTIONAL_CAPABILITIES.json').write_text('{}'); rm.write_release(root)
        cm=root/'CONTENT_MANIFEST.json'; cm.write_text(cm.read_text().replace('CONTENT_MANIFEST_V1','BROKEN')); assert not rm.verify(root)['passed']
        rm.write_release(root); seal=root/'RELEASE_SEAL.json'; seal.write_text(seal.read_text().replace('v0.4.2b3','v0.4.2bX')); assert not rm.verify(root)['passed']
