from __future__ import annotations
import io,json,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
import legal_overlay as L

def tar_bytes(rows):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w:gz') as tf:
  for name,data,kind,link in rows:
   i=tarfile.TarInfo(name)
   if kind=='file':i.size=len(data);tf.addfile(i,io.BytesIO(data))
   elif kind=='symlink':i.type=tarfile.SYMTYPE;i.linkname=link;tf.addfile(i)
 return b.getvalue()
class T(unittest.TestCase):
 def tmp(self):return Path(tempfile.mkdtemp())
 def test_xz_product_evidence(self):
  t=self.tmp();data=tar_bytes([('root/share/doc/xz/COPYING',b'A','file',''),('root/share/doc/xz/COPYING.GPLv2',b'B','file',''),('root/share/doc/xz/AUTHORS',b'C','file','')]);a=t/'xz.tar.gz';a.write_bytes(data)
  files={'COPYING':(L.sha_bytes(b'A'),1),'COPYING.GPLv2':(L.sha_bytes(b'B'),1),'AUTHORS':(L.sha_bytes(b'C'),1)}
  with patch.object(L,'XZ_SHA',L.sha_file(a)),patch.object(L,'XZ_SIZE',a.stat().st_size),patch.object(L,'XZ_FILES',files):
   r=L.extract_xz_product_evidence(a,t/'out');self.assertTrue(r['pass']);self.assertEqual(len(r['files']),3)
 def test_unsafe_symlink_fails(self):
  t=self.tmp();a=t/'x.tar.gz';a.write_bytes(tar_bytes([('root/bad',b'','symlink','../../escape')]))
  with self.assertRaises(ValueError):list(L._regular_members(a))
 def test_sqlite_public_domain(self):
  t=self.tmp();a=t/'sqlite.tar.gz';a.write_bytes(tar_bytes([('root/sqlite3.c',b'/* SQLite is in the public domain. */','file','')]))
  r=L.scan_sqlite_public_domain(a,L.sha_file(a),t/'out.json');self.assertTrue(r['pass'])
 def test_hacl_license_markers(self):
  t=self.tmp();a=t/'Python.tgz';a.write_bytes(tar_bytes([('Python/Modules/_hacl/refresh.sh',b'HACL_COMMIT=0123456789abcdef0123456789abcdef01234567','file',''),('Python/Modules/_hacl/Hacl.c',b'/* MIT License\nPermission is hereby granted */','file','')]))
  with patch.object(L,'CPYTHON_SOURCE_SHA',L.sha_file(a)),patch.object(L,'CPYTHON_SOURCE_SIZE',a.stat().st_size):
   r=L.scan_hacl(a,t/'hacl',t/'hacl.json');self.assertTrue(r['pass']);self.assertGreater(r['license_marker_file_count'],0)
 def test_hacl_without_license_fails(self):
  t=self.tmp();a=t/'Python.tgz';a.write_bytes(tar_bytes([('Python/Modules/_hacl/README.md',b'HACL source','file','')]))
  with patch.object(L,'CPYTHON_SOURCE_SHA',L.sha_file(a)),patch.object(L,'CPYTHON_SOURCE_SIZE',a.stat().st_size):
   with self.assertRaises(ValueError):L.scan_hacl(a,t/'hacl',t/'hacl.json')
 def test_libmpdec_header(self):
  t=self.tmp();d=t/'cpython/Modules/_decimal/libmpdec';d.mkdir(parents=True);(d/'mpdecimal.h').write_text('Copyright X\nRedistribution and use in source and binary forms\nTHIS SOFTWARE IS PROVIDED')
  r=L.scan_libmpdec(t,t/'out.json');self.assertTrue(r['pass'])
 def test_provider_policy(self):
  t=self.tmp();r=L.provider_policy(ROOT,t/'policy.json');self.assertTrue(r['pass']);self.assertEqual([x['soname'] for x in r['providers']],L.SYSTEM_LIBS)
if __name__=='__main__':unittest.main()
