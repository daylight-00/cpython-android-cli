from __future__ import annotations
import hashlib,json,subprocess,tarfile,tempfile,unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
import license_payloads as lp
def make_tgz(p,files):
 with tarfile.open(p,'w:gz') as t:
  import io
  for n,b in files.items():
   x=tarfile.TarInfo(n);x.size=len(b);x.mode=0o644;t.addfile(x,io.BytesIO(b))
def make_full(p,with_hacl=True):
 with tempfile.TemporaryDirectory() as d:
  tar=Path(d)/'f.tar'
  with tarfile.open(tar,'w') as t:
   import io
   files={'python/install/lib/python3.14/lib-dynload/_decimal.so':b'libmpdec 2.5.1'}
   if with_hacl:files.update({'python/install/lib/python3.14/lib-dynload/_hmac.so':b'HACL* Modules/_hacl/Hacl_Streaming_HMAC.c','python/install/lib/python3.14/lib-dynload/_sha3.so':b'Modules/_hacl/Hacl_Hash_SHA3.c'})
   for n,b in files.items():x=tarfile.TarInfo(n);x.size=len(b);t.addfile(x,io.BytesIO(b))
  subprocess.run(['zstd','-q','-f',str(tar),'-o',str(p)],check=True)
class T(unittest.TestCase):
 def fixture(self,d,with_hacl=True):
  d=Path(d);fam=d/'family';fam.mkdir();full=fam/'x-full.tar.zst';make_full(full,with_hacl)
  cp=d/'Python-3.14.6.tgz';make_tgz(cp,{'Python-3.14.6/LICENSE':b'PSF license','Python-3.14.6/Misc/externals.spdx.json':b'{}','Python-3.14.6/Modules/expat/COPYING':b'expat license','Python-3.14.6/Modules/_decimal/libmpdec/mpdecimal.h':b'MPD_VERSION 2.5.1','Python-3.14.6/Modules/_decimal/libmpdec/COPYRIGHT.txt':b'mpdec license','Python-3.14.6/Modules/_hacl/LICENSE':b'hacl license','Python-3.14.6/Modules/_hacl/Hacl_Hash_SHA3.c':b'code'})
  src={}
  for c in ['bzip2','libffi','openssl','sqlite','zstd']:
   p=d/f'{c}.tar.gz';make_tgz(p,{f'{c}-v/LICENSE':f'{c} license'.encode()});src[c]={'path':str(p),'sha256':lp.sha_file(p),'version':'v'}
  return fam,full,cp,src
 def test_success_synthetic(self):
  with tempfile.TemporaryDirectory() as d:
   fam,full,cp,src=self.fixture(d);oldsha,oldsz=lp.CPYTHON_SOURCE_SHA,lp.CPYTHON_SOURCE_SIZE;lp.CPYTHON_SOURCE_SHA=lp.sha_file(cp);lp.CPYTHON_SOURCE_SIZE=cp.stat().st_size
   try:r=lp.acquire_license_evidence(fam,cp,src,Path(d)/'out',ROOT,expected_full_sha=lp.sha_file(full));self.assertTrue(r['pass']);self.assertEqual(r['metrics']['expanded_component_count'],13)
   finally:lp.CPYTHON_SOURCE_SHA,lp.CPYTHON_SOURCE_SIZE=oldsha,oldsz
 def test_bad_source_hash(self):
  with tempfile.TemporaryDirectory() as d:
   fam,full,cp,src=self.fixture(d);src['bzip2']['sha256']='0'*64;oldsha,oldsz=lp.CPYTHON_SOURCE_SHA,lp.CPYTHON_SOURCE_SIZE;lp.CPYTHON_SOURCE_SHA=lp.sha_file(cp);lp.CPYTHON_SOURCE_SIZE=cp.stat().st_size
   try:
    with self.assertRaises(ValueError):lp.acquire_license_evidence(fam,cp,src,Path(d)/'out',ROOT,expected_full_sha=lp.sha_file(full))
   finally:lp.CPYTHON_SOURCE_SHA,lp.CPYTHON_SOURCE_SIZE=oldsha,oldsz
 def test_missing_hacl_fails(self):
  with tempfile.TemporaryDirectory() as d:
   fam,full,cp,src=self.fixture(d,False);oldsha,oldsz=lp.CPYTHON_SOURCE_SHA,lp.CPYTHON_SOURCE_SIZE;lp.CPYTHON_SOURCE_SHA=lp.sha_file(cp);lp.CPYTHON_SOURCE_SIZE=cp.stat().st_size
   try:
    with self.assertRaises(ValueError):lp.acquire_license_evidence(fam,cp,src,Path(d)/'out',ROOT,expected_full_sha=lp.sha_file(full))
   finally:lp.CPYTHON_SOURCE_SHA,lp.CPYTHON_SOURCE_SIZE=oldsha,oldsz
 def test_symlink_tar_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.tgz'
   with tarfile.open(p,'w:gz') as tf:
    i=tarfile.TarInfo('x/LICENSE');i.type=tarfile.SYMTYPE;i.linkname='../../etc/passwd';tf.addfile(i)
   with self.assertRaises(ValueError):lp.inventory_source_archive('x',p,lp.sha_file(p),'1',Path(d)/'out')
 def test_unsafe_tar_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.tgz';make_tgz(p,{'../LICENSE':b'x'})
   with self.assertRaises(ValueError):lp.inventory_source_archive('x',p,lp.sha_file(p),'1',Path(d)/'out')
if __name__=='__main__':unittest.main()
