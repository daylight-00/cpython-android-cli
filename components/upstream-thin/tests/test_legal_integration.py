from __future__ import annotations
import io,json,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
import legal_integration as L

def vendor_lines():return '\n'.join(f'{n}==1.0' for n in L.VENDOR_SPECS)+'\n'
def pip_archive(path:Path,missing:str|None=None,unsafe:bool=False):
 rows=[];prefix='python/lib/python3.14/site-packages/'
 rows += [(prefix+'pip/_vendor/vendor.txt',vendor_lines().encode()),(prefix+'pip/_vendor/README.rst',b'Modifications\n'),(prefix+'pip-26.1.2.dist-info/METADATA',b'Name: pip\nVersion: 26.1.2\n')]
 lic=prefix+'pip-26.1.2.dist-info/licenses/';rows += [(lic+'LICENSE.txt',b'pip license'),(lic+'AUTHORS.txt',b'pip authors')]
 for name,(folder,expr,files) in L.VENDOR_SPECS.items():
  for fn in files:
   if missing==name:continue
   rows.append((lic+f'src/pip/_vendor/{folder}/{fn}',f'{name}:{fn}'.encode()))
 with tarfile.open(path,'w:gz') as tf:
  for name,data in rows:
   i=tarfile.TarInfo(name);i.size=len(data);tf.addfile(i,io.BytesIO(data))
  if unsafe:
   i=tarfile.TarInfo('python/bad');i.type=tarfile.SYMTYPE;i.linkname='../../escape';tf.addfile(i)
 return path

def fake_family(t:Path,archive:Path):
 f=t/'family';f.mkdir();(f/'release-index.json').write_text(json.dumps({'release':{'release_id':'cpython-3.14.6+e3-r1-aarch64-linux-android','assets':[],'family_invariants':{}}}))
 (f/'SHA256SUMS').write_text('old\n');(f/archive.name).write_bytes(archive.read_bytes())
 for i in range(20):(f/f'dummy-{i:02d}.json').write_text('{}\n')
 assert len(list(f.iterdir()))==23;return f
class Tests(unittest.TestCase):
 def tmp(self):return Path(tempfile.mkdtemp())
 def test_vendor_parser_exact(self):
  rows=L.parse_vendor_txt(vendor_lines().encode());self.assertEqual(len(rows),18);self.assertEqual({x['name'] for x in rows},set(L.VENDOR_SPECS))
 def test_vendor_parser_missing_fails(self):
  with self.assertRaises(ValueError):L.parse_vendor_txt(b'CacheControl==1\n')
 def test_extract_pip_review(self):
  t=self.tmp();a=pip_archive(t/'install_only.tar.gz');legal=t/'legal'
  with patch.object(L,'INSTALL_ONLY_SHA',L.sha256_file(a)),patch.object(L,'INSTALL_ONLY_SIZE',a.stat().st_size):r=L.extract_pip_review(a,legal)
  self.assertEqual(r['vendor_component_count'],18);self.assertEqual(len([p for p in (legal/'pip/licenses/vendors').rglob('*') if p.is_file()]),20)
 def test_missing_vendor_license_fails(self):
  t=self.tmp();a=pip_archive(t/'install_only.tar.gz',missing='certifi')
  with patch.object(L,'INSTALL_ONLY_SHA',L.sha256_file(a)),patch.object(L,'INSTALL_ONLY_SIZE',a.stat().st_size):
   with self.assertRaises(ValueError):L.extract_pip_review(a,t/'legal')
 def test_unsafe_symlink_fails(self):
  t=self.tmp();a=pip_archive(t/'install_only.tar.gz',unsafe=True)
  with patch.object(L,'INSTALL_ONLY_SHA',L.sha256_file(a)),patch.object(L,'INSTALL_ONLY_SIZE',a.stat().st_size):
   with self.assertRaises(ValueError):L.extract_pip_review(a,t/'legal')
 def assembled(self):
  t=self.tmp();a=pip_archive(t/'x-install_only.tar.gz');f=fake_family(t,a);o=t/'out'
  with patch.object(L,'INSTALL_ONLY_SHA',L.sha256_file(a)),patch.object(L,'INSTALL_ONLY_SIZE',a.stat().st_size),patch.object(L,'verify_release_family',return_value={'pass':True}):r=L.assemble_legal_integrated_family(f,o,root=ROOT)
  return t,f,o,r
 def test_synthetic_assembly(self):
  t,f,o,r=self.assembled();self.assertTrue(r['pass']);self.assertEqual(r['metrics']['review_unit_count'],31);self.assertEqual(r['metrics']['remaining_gap_count'],1)
 def test_tampered_reused_file_fails(self):
  t,f,o,r=self.assembled();(o/'dummy-00.json').write_text('tamper')
  with patch.object(L,'verify_release_family',return_value={'pass':True}):v=L.verify_legal_integrated_family(o,predecessor_family=f,root=ROOT)
  self.assertFalse(v['pass']);self.assertIn('predecessor_files_reused',v['failed_checks'])
 def test_owner_approval_tamper_fails(self):
  t,f,o,r=self.assembled();p=o/'release-index.json';d=json.loads(p.read_text());d['release']['claim_boundary']['owner_approved']=True;d['release_sha256']=__import__('hashlib').sha256(L.canonical_json_bytes(d['release'])).hexdigest();p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
  with patch.object(L,'verify_release_family',return_value={'pass':True}):v=L.verify_legal_integrated_family(o,predecessor_family=f,root=ROOT)
  self.assertFalse(v['pass']);self.assertIn('claims_bounded',v['failed_checks'])
if __name__=='__main__':unittest.main()
