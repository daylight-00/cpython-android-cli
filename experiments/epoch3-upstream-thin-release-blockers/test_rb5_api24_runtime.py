from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

def module(name: str, file: str):
    spec=importlib.util.spec_from_file_location(name,HERE/file); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m); return m
AUDIT=module('audit_rb5', 'audit_rb5_api24_runtime.py')

class RB5AuditTests(unittest.TestCase):
    def fixture(self, *, tamper: str | None = None) -> Path:
        td=Path(tempfile.mkdtemp()); checks={k:True for k in AUDIT.REQUIRED_CHECKS}
        if tamper: checks[tamper]=False
        data={
          'result_kind':'epoch3-rb5-api24-runtime-candidate','pass':tamper is None,'checks':checks,
          'failed_checks':[] if tamper is None else [tamper],'errors':[],
          'release':{'release_id':AUDIT.EXPECTED_RELEASE_ID,'release_sha256':AUDIT.EXPECTED_RELEASE_SHA,'family_fingerprint_sha256':AUDIT.EXPECTED_FINGERPRINT,'install_only_sha256':AUDIT.EXPECTED_INSTALL_SHA},
          'target':{'mode':'adb','serial':'emulator-5554','required_android_api':24,'architecture':'aarch64'},
          'claim_boundary':{'api24_runtime_started':True,'api24_runtime_candidate':tamper is None,'api24_runtime_accepted':False,'rb5_closed':False,'actual_16k_runtime_qualified':False,'non_termux_android_context_qualified':False,'selectable':False,'publication':False,'artifact_bytes_changed':False},
        }
        (td/'result.json').write_text(json.dumps(data),encoding='utf-8'); return td
    def test_positive(self): self.assertTrue(AUDIT.verify(self.fixture())['pass'])
    def test_runtime_failure(self): self.assertFalse(AUDIT.verify(self.fixture(tamper='startup_and_relocation'))['pass'])
    def test_missing_result(self):
        with tempfile.TemporaryDirectory() as td: self.assertFalse(AUDIT.verify(Path(td))['pass'])

if __name__=='__main__': unittest.main()
