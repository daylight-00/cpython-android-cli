#!/usr/bin/env python3
"""Verify the Stage 3-D Gate 1 consumer authority design."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

checks: dict[str, bool] = {}
def ck(name: str, value: bool) -> None:
    if name in checks:
        raise RuntimeError(f"duplicate check {name}")
    checks[name] = bool(value)

authority = load(EXP / "gate1-consumer-authority.json")
matrix = load(EXP / "gate2-consumer-discovery-matrix.json")
scope = text("docs/stages/STAGE3D_SCOPE.md")
design = text("experiments/stage3d-consumer-integration/GATE1_CONSUMER_AUTHORITY_DESIGN.md")
readme = text("README.md")
current = text("docs/PROJECT_CONTEXT_STAGE3D.md")
historical = text("docs/PROJECT_CONTEXT_STAGE3C.md")
phase5 = text("docs/stages/STAGE3C_PHASE5_SCOPE.md")
ledger = text("docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md")
handoff = text("docs/handoff/README.md")
evidence = text("docs/evidence/STAGE3D_GATE1_CONSUMER_AUTHORITY_DESIGN_RESULT.md")

ck("authority_schema", authority.get("schema_version") == 1)
ck("authority_kind", authority.get("authority_kind") == "stage3d-gate1-consumer-authority-design")
ck("authority_status", authority.get("status") == "design-frozen")
ck("authority_primary_model", authority.get("primary_model") == "uv-system-python")
ck("authority_control", authority.get("canonical_control") == "explicit-absolute-interpreter-path")
ck("authority_download_policy", authority.get("download_policy") == "disabled-for-all-system-integration-scenarios")
ck("authority_gate4_commit", authority["input_authority"]["gate4e_commit"] == "68b67dcc3b65872e1034c487747d3fcd1ad5a319")
ck("authority_gate4_tree", authority["input_authority"]["gate4e_tree"] == "2115f6fa3b923c9fcf21a1b8343cb6149afb6cc7")
ck("authority_gate4_v1", authority["input_authority"]["gate4d_v1_sha256"] == "ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c")
ck("authority_gate4_v2", authority["input_authority"]["gate4d_v2_sha256"] == "98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2")
ck("authority_gate4_66", authority["input_authority"]["gate4_scenarios"] == {"count": 66, "pass": 66})
ck("authority_products", [p["python"] for p in authority["products"]] == ["3.14.5", "3.14.6"])
ck("authority_source_commits", {p["source_commit"] for p in authority["products"]} == {"5607950ef232dad16d75c0cf53101d9649d89115", "c63aec69bd59c55314c06c23f4c22c03de76fe45"})
ck("authority_topologies", authority["topologies"] == ["runtime-only", "runtime+development", "runtime+test", "full"])
ck("authority_surfaces", len(authority["discovery_surfaces"]) == 14 and len(set(authority["discovery_surfaces"])) == 14)
ck("authority_gate_sequence", authority["gate_sequence"] == {
    "gate1":"FROZEN", "gate2":"PENDING_READ_ONLY_TERMUX_CENSUS", "gate3":"PENDING_SYSTEM_INTEGRATION_CONTRACT",
    "gate4":"PENDING_TARGET_IMPLEMENTATION_VALIDATION", "gate5":"PENDING_INDEPENDENT_FREEZE",
    "gate6":"DEFERRED_OPTIONAL_MANAGED_PYTHON_RESEARCH"})
for forbidden in ("global-prefix-links", "shell-startup-edits", "managed-install-dir-registration", "uv-patching", "python-download-fallback", "root", "proot", "shizuku", "docker"):
    ck(f"forbidden_{forbidden}", forbidden in authority["mutation_policy"]["forbidden"])
obs = authority["upstream_observations"]
ck("upstream_review_date", obs["reviewed"] == "2026-07-15")
ck("upstream_python_url", obs["python_versions_url"] == "https://docs.astral.sh/uv/concepts/python-versions/")
ck("upstream_platform_url", obs["platform_support_url"] == "https://docs.astral.sh/uv/reference/policies/platforms/")
ck("upstream_system_term", obs["non_uv_installation_is_system_python"] is True)
ck("upstream_local_requests", obs["local_request_forms_include_path_name_and_install_dir"] is True)
ck("upstream_discovery", obs["discovery_includes_managed_dir_and_path"] is True)
ck("upstream_download_disable", obs["downloads_can_be_disabled"] is True)
ck("upstream_managed_source", obs["managed_cpython_source"] == "python-build-standalone")
ck("upstream_android_not_tier", obs["android_listed_in_uv_platform_tiers"] is False)
ck("authority_claim_boundary", "No Termux discovery" in authority["claim_boundary"] and "managed-Python provider" in authority["claim_boundary"])

rows = matrix["scenarios"]
ck("matrix_schema", matrix["schema_version"] == 1)
ck("matrix_kind", matrix["matrix_kind"] == "stage3d-gate2-consumer-discovery-census")
ck("matrix_status", matrix["status"] == "design-frozen-not-executed")
ck("matrix_count", matrix["scenario_count"] == 64 and len(rows) == 64)
ck("matrix_unique_ids", len({r["id"] for r in rows}) == 64)
groups = Counter(r["group"] for r in rows)
ck("matrix_group_counts", dict(groups) == matrix["group_counts"] == {"explicit":8,"natural":32,"project":8,"precedence-negative":12,"transition-continuity":4})
ck("matrix_explicit_ids", [r["id"] for r in rows if r["group"] == "explicit"] == [f"E{i:02d}" for i in range(1,9)])
ck("matrix_natural_ids", [r["id"] for r in rows if r["group"] == "natural"] == [f"N{i:02d}" for i in range(1,33)])
ck("matrix_project_ids", [r["id"] for r in rows if r["group"] == "project"] == [f"P{i:02d}" for i in range(1,9)])
ck("matrix_negative_ids", [r["id"] for r in rows if r["group"] == "precedence-negative"] == [f"X{i:02d}" for i in range(1,13)])
ck("matrix_transition_ids", [r["id"] for r in rows if r["group"] == "transition-continuity"] == [f"T{i:02d}" for i in range(1,5)])
for group in ("explicit", "natural", "project"):
    subset = [r for r in rows if r["group"] == group]
    ck(f"matrix_{group}_products", {r["product"] for r in subset} == {"3.14.5", "3.14.6"})
    ck(f"matrix_{group}_topologies", {r["topology"] for r in subset} == {"runtime-only", "runtime+development", "runtime+test", "full"})
ck("matrix_explicit_cross_product", len({(r["product"],r["topology"]) for r in rows if r["group"]=="explicit"}) == 8)
natural_requests = {r["request"] for r in rows if r["group"] == "natural"}
ck("matrix_natural_requests", natural_requests == {"executable-name", "install-directory", "path-python3.14", "version-3.14"})
ck("matrix_natural_cross_product", all(sum(1 for r in rows if r["group"]=="natural" and r["product"]==p and r["topology"]==t) == 4 for p in ("3.14.5","3.14.6") for t in ("runtime-only","runtime+development","runtime+test","full")))
project_requests = Counter(r["request"] for r in rows if r["group"] == "project")
ck("matrix_project_requests", project_requests == {"python-version-file":4,"project-requires-python":4})
neg_requests = {r["request"] for r in rows if r["group"] == "precedence-negative"}
for req in ("venv-precedence","system-flag-ignores-venv","managed-decoy-no-download","only-system","only-managed","incompatible-version","non-executable-candidate","moved-prefix-explicit-path"):
    ck(f"matrix_negative_{req}", req in neg_requests)
transitions = {(r["product"],r["topology"]) for r in rows if r["group"] == "transition-continuity"}
ck("matrix_transition_directions", transitions == {("3.14.6->3.14.5","runtime-only"),("3.14.5->3.14.6","runtime-only"),("3.14.6->3.14.5","full"),("3.14.5->3.14.6","full")})
for req in ("python-downloads-disabled","raw-stdout-stderr-exit-recorded","selected-realpath-recorded","repository-invariant","canonical-installation-invariant","pass-or-fail-archive-preserved"):
    ck(f"matrix_requirement_{req}", req in matrix["global_requirements"])
ck("matrix_claim_boundary", "no target result is accepted" in matrix["claim_boundary"])

# Documentation consistency.
ck("scope_active", "ACTIVE — Gate 1 scope and authority design frozen" in scope)
ck("scope_system_first", "system-Python path" in scope and "explicit absolute interpreter path" in scope)
ck("scope_64", "total                          64" in scope)
ck("scope_no_managed_claim", "managed-Python integration is not the first gate" in scope)
ck("scope_no_global_mutation", "must not alter global shell files" in scope and "uv's managed installation directory" in scope)
ck("design_frozen", "DESIGN FROZEN" in design)
ck("design_observe_first", "observe and define supported system-Python discovery behavior" in scope)
ck("design_forbidden", all(x in design for x in ("writing `$PREFIX/bin/python*`", "patching uv", "using proot, root, Shizuku, or Docker")))
ck("evidence_design_only", "does not prove that uv naturally discovers" in evidence)
ck("readme_stage3d_active", "Stage 3-D  consumer integration                         active — Gate 1 design frozen" in readme)
ck("readme_current_context", "docs/PROJECT_CONTEXT_STAGE3D.md" in readme)
ck("current_status", "> **Status:** Current handoff context" in current)
ck("current_branch", "agent/stage3d-consumer-integration" in current)
ck("current_gate2", "Gate 2  read-only Termux discovery census      ACTIVE NEXT" in current)
ck("current_no_global_links", "Do not create global interpreter links" in current)
ck("historical_marked", "HISTORICAL FROZEN SNAPSHOT" in historical and "PROJECT_CONTEXT_STAGE3D.md" in historical)
ck("phase5_frozen", "FROZEN — Gate 4E independent transition freeze complete" in phase5 and "Gate 4D   bidirectional Termux target validation                  FROZEN" in phase5)
ck("ledger_next", "64-scenario read-only Termux consumer discovery census" in ledger)
ck("handoff_current", "../PROJECT_CONTEXT_STAGE3D.md" in handoff and "Stage 3-D Gate 2 read-only Termux discovery census     ACTIVE NEXT" in handoff)
ck("workflow_current", "docs/PROJECT_CONTEXT_STAGE3D.md" in text("docs/GITHUB_COLLABORATION_WORKFLOW.md") and "gate2-consumer-discovery-matrix.json" in text("docs/GITHUB_COLLABORATION_WORKFLOW.md"))
ck("protocol_current", "docs/PROJECT_CONTEXT_STAGE3D.md" in text("docs/handoff/COLLABORATION_PROTOCOL.md") and "gate2-consumer-discovery-matrix.json" in text("docs/handoff/COLLABORATION_PROTOCOL.md"))
ck("orientation_current", "docs/PROJECT_CONTEXT_STAGE3D.md" in text("docs/PROJECT_ORIENTATION.md") and "gate1-consumer-authority.json" in text("docs/PROJECT_ORIENTATION.md"))

required = [
 "docs/PROJECT_CONTEXT_STAGE3D.md", "docs/stages/STAGE3D_SCOPE.md",
 "experiments/stage3d-consumer-integration/GATE1_CONSUMER_AUTHORITY_DESIGN.md",
 "experiments/stage3d-consumer-integration/gate1-consumer-authority.json",
 "experiments/stage3d-consumer-integration/gate2-consumer-discovery-matrix.json",
 "experiments/stage3d-consumer-integration/run-gate1-consumer-authority-design.sh",
 "experiments/stage3d-consumer-integration/verify-gate1-consumer-authority-design.py",
 "docs/evidence/STAGE3D_GATE1_CONSUMER_AUTHORITY_DESIGN_RESULT.md",
]
ck("required_paths", all((ROOT/p).is_file() for p in required))
ck("runner_executable", (EXP/"run-gate1-consumer-authority-design.sh").stat().st_mode & 0o111 != 0)
ck("git_diff_check", subprocess.run(["git","-C",str(ROOT),"diff","--check","HEAD"],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode == 0)
py_files = [EXP/"verify-gate1-consumer-authority-design.py", ROOT/"scripts/verify-project-control-plane.py"]
ck("python_compile", subprocess.run([sys.executable,"-m","py_compile",*[str(p) for p in py_files]],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode == 0)

failed = sorted(k for k,v in checks.items() if not v)
result = {
 "schema_version":1,
 "verification_kind":"stage3d-gate1-consumer-authority-design-verification",
 "pass":not failed,
 "check_count":len(checks),
 "pass_count":sum(checks.values()),
 "failed_checks":failed,
 "checks":dict(sorted(checks.items())),
 "observed":{
   "authority_sha256":hashlib.sha256((EXP/"gate1-consumer-authority.json").read_bytes()).hexdigest(),
   "matrix_sha256":hashlib.sha256((EXP/"gate2-consumer-discovery-matrix.json").read_bytes()).hexdigest(),
   "scenario_count":len(rows),
   "tree_before_commit":subprocess.check_output(["git","-C",str(ROOT),"write-tree"],text=True).strip(),
 },
 "claim_boundary":"Repository scope and scenario design only. No Termux consumer behavior is accepted."
}
print(json.dumps(result,indent=2,sort_keys=True))
print()
print(f"STAGE3D_GATE1_CONSUMER_AUTHORITY_DESIGN_VERIFICATION={result['pass_count']}/{result['check_count']} {'PASS' if result['pass'] else 'FAIL'}")
raise SystemExit(0 if result["pass"] else 1)
