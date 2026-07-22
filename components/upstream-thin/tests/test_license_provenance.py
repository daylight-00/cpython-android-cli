#!/usr/bin/env python3
from __future__ import annotations
import hashlib,io,json,sys,tarfile,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
from license_provenance import inspect_cpython_source,parse_dependency_pins  # noqa:E402
PINS=b'''def unpack_deps(host, prefix_dir, cache_dir):\n    for name_ver in [\n        "bzip2-1.0.8-3",\n        "libffi-3.4.4-3",\n        "openssl-3.5.7-0",\n        "sqlite-3.50.4-0",\n        "xz-5.4.6-1",\n        "zstd-1.5.7-2"\n    ]:\n        pass\n'''
def make_source(path:Path,unsafe=False):
 files={'Python-3.14.6/LICENSE':b'PSF license\n','Python-3.14.6/Misc/externals.spdx.json':json.dumps({'packages':[{'name':'libffi','versionInfo':'3.4.4','downloadLocation':'https://example.invalid/libffi.tar.gz','checksums':[{'algorithm':'SHA256','checksumValue':'abc'}]}]},sort_keys=True).encode(),'Python-3.14.6/Modules/expat/COPYING':b'expat license\n'}
 with tarfile.open(path,'w:gz') as tf:
  for name,data in files.items():
   ti=tarfile.TarInfo(name);ti.size=len(data);ti.mode=0o644;tf.addfile(ti,io.BytesIO(data))
  if unsafe:
   ti=tarfile.TarInfo('Python-3.14.6/bad');ti.type=tarfile.SYMTYPE;ti.linkname='../../escape';tf.addfile(ti)
class LicenseProvenanceTests(unittest.TestCase):
 def test_pins_exact(self):
  pins=parse_dependency_pins(PINS);self.assertEqual(pins['libffi']['release_tag'],'libffi-3.4.4-3');self.assertEqual(len(pins),6)
 def test_missing_pin_negative(self):
  with self.assertRaises(ValueError):parse_dependency_pins(PINS.replace(b'"libffi-3.4.4-3",\n',b''))
 def test_duplicate_pin_negative(self):
  with self.assertRaises(ValueError):parse_dependency_pins(PINS.replace(b'"libffi-3.4.4-3",',b'"libffi-3.4.4-3","libffi-3.4.4-3",'))
 def test_source_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'source.tgz';make_source(p);expected={'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size,'url':'https://example.invalid/source.tgz'};out=Path(td)/'out';r=inspect_cpython_source(p,out,expected=expected);self.assertEqual(r['spdx_packages'][0]['name'],'libffi');self.assertTrue((out/'LICENSE').is_file())
 def test_identity_negative(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'source.tgz';make_source(p);expected={'filename':p.name,'sha256':'0'*64,'size_bytes':p.stat().st_size,'url':'x'}
   with self.assertRaises(ValueError):inspect_cpython_source(p,Path(td)/'out',expected=expected)
 def test_unsafe_link_negative(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'source.tgz';make_source(p,unsafe=True);expected={'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size,'url':'x'}
   with self.assertRaises(ValueError):inspect_cpython_source(p,Path(td)/'out',expected=expected)
if __name__=='__main__':unittest.main()
