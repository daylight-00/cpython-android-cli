#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, os, shutil, stat, subprocess, sys
from pathlib import Path
from typing import Any

P4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"


def cjson(v: Any) -> bytes: return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()
def readj(p: Path) -> dict[str, Any]:
    v = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v, dict): raise ValueError(p)
    return v
def writej(p: Path, v: dict[str, Any]) -> None: p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(cjson(v))
def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def kind(p: Path) -> str:
    try: s = p.lstat()
    except FileNotFoundError: return "absent"
    if stat.S_ISLNK(s.st_mode): return "symlink"
    if stat.S_ISDIR(s.st_mode): return "directory"
    if stat.S_ISREG(s.st_mode): return "regular"
    return "special"
def snap(p: Path) -> dict[str, Any]:
    k = kind(p); r: dict[str, Any] = {"path": str(p), "type": k}
    if k == "absent": return r
    s = p.lstat(); r["mode"] = f"{stat.S_IMODE(s.st_mode):04o}"
    if k == "regular": r.update(size=s.st_size, sha256=sha(p))
    elif k == "symlink": r["target"] = os.readlink(p)
    return r
def tree_paths(root: Path) -> list[Path]:
    out: list[Path] = []
    for cur, ds, fs in os.walk(root, followlinks=False):
        ds.sort(); fs.sort(); base = Path(cur)
        out.extend(base / x for x in ds); out.extend(base / x for x in fs)
    return sorted(out, key=lambda p: p.relative_to(root).as_posix())
def portable(prefix: Path) -> dict[str, Any]:
    h = hashlib.sha256(); counts = {x: 0 for x in ("directory", "regular", "symlink", "special")}
    for p in tree_paths(prefix):
        rel = p.relative_to(prefix).as_posix(); s = p.lstat(); mode = f"{stat.S_IMODE(s.st_mode):04o}"
        if stat.S_ISREG(s.st_mode): k, size, digest, target = "regular", str(s.st_size), sha(p), ""
        elif stat.S_ISDIR(s.st_mode): k, size, digest, target = "directory", "", "", ""
        elif stat.S_ISLNK(s.st_mode): k, size, digest, target = "symlink", "", "", os.readlink(p)
        else: k, size, digest, target = "special", "", "", ""
        counts[k] += 1; h.update("\t".join((rel, k, mode, size, digest, target)).encode("utf-8", "surrogateescape") + b"\n")
    return {"fingerprint": h.hexdigest(), "entry_count": sum(counts.values()), "type_counts": counts}
def registry(root: Path) -> dict[str, Any]:
    p = root / ".cpython-android-cli/registry.json"; data = p.read_bytes(); v = json.loads(data)
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "artifact_count": len(v["artifacts"]), "owned_path_count": len(v["owned_paths"])}
def txs(root: Path) -> list[dict[str, Any]]:
    d = root / ".cpython-android-cli/transactions"; out: list[dict[str, Any]] = []
    if not d.is_dir(): return out
    for t in sorted(x for x in d.iterdir() if x.is_dir()):
        j = t / "journal.json"; row: dict[str, Any] = {"name": t.name, "journal_exists": j.is_file()}
        if j.is_file():
            v = readj(j); row.update(state=v.get("state"), operation=v.get("operation"), artifact=v.get("artifact"), mutations=v.get("mutations", []), recovery=v.get("recovery"))
        out.append(row)
    return out
def identity(root: Path) -> dict[str, Any]: return {"portable": portable(root / "prefix"), "registry": registry(root), "transactions": txs(root)}
def mrecord(e: dict[str, Any]) -> dict[str, Any]: return {"path": e["payload_path"], "type": e["type"], "mode": e["mode"], "size": e.get("size"), "sha256": e.get("sha256"), "symlink_target": e.get("symlink_target")}
def matches_snap(s: dict[str, Any], e: dict[str, Any]) -> bool:
    if s.get("type") != e.get("type") or s.get("mode") != e.get("mode"): return False
    if e.get("type") == "regular": return s.get("size") == e.get("size") and s.get("sha256") == e.get("sha256")
    if e.get("type") == "symlink": return s.get("target") == e.get("symlink_target")
    return True


def invoke(local: Path, engine: Path, contract: Path, root: Path, op: str, out: Path, artifact: str | None = None, crash: list[str] | None = None) -> dict[str, Any]:
    cmd = [sys.executable, "-I", "-B", "-S", str(local), str(engine), "--installation-root", str(root), "--operation", op, "--output", str(out)]
    if op == "install": cmd += ["--contract-results", str(contract)]
    if artifact: cmd += ["--artifact", artifact]
    if crash: cmd += crash
    run = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    log = out.with_suffix(".log"); log.parent.mkdir(parents=True, exist_ok=True); log.write_text(run.stdout, encoding="utf-8")
    result = readj(out) if out.is_file() else None
    record = {"returncode": run.returncode, "result": result, "log": log.name, "output_exists": out.is_file(), "command_tail": cmd[-6:]}
    writej(out.with_name(out.stem + "-process.json"), record)
    return record


def clone(seed: Path, dst: Path, probe: str) -> dict[str, Any]:
    shutil.copytree(seed, dst, symlinks=True, copy_function=shutil.copy2)
    sr, dr = seed / ".cpython-android-cli/registry.json", dst / ".cpython-android-cli/registry.json"
    sp, dp = seed / "prefix" / probe, dst / "prefix" / probe
    return {"root_inode_separate": seed.stat().st_ino != dst.stat().st_ino, "registry_inode_separate": sr.stat().st_ino != dr.stat().st_ino, "probe_inode_separate": sp.stat().st_ino != dp.stat().st_ino}


def mutate(p: Path, name: str, mode: str) -> dict[str, Any]:
    before = snap(p)
    if name == "regular-bytes": p.write_bytes(b"stage3c-phase4i-corrupted-regular\n"); os.chmod(p, int(mode, 8))
    elif name == "regular-mode": os.chmod(p, 0o644 if int(mode, 8) != 0o644 else 0o600)
    elif name == "regular-wrong-type": p.unlink(); p.mkdir(mode=0o755)
    elif name == "symlink-target": p.unlink(); os.symlink("stage3c-phase4i-invalid-target", p)
    elif name in {"missing-regular", "missing-symlink"}: p.unlink()
    else: raise ValueError(name)
    return {"kind": name, "before": before, "after": snap(p)}


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in ("phase4-results", "contract-results", "manifest", "local-script-runner", "engine", "work-root", "output-dir"): ap.add_argument("--" + n, required=True, type=Path)
    ap.add_argument("--require-pass", action="store_true"); a = ap.parse_args()
    p4, contract, manifest_path, local, engine, work, out = [getattr(a, n.replace("-", "_")).resolve() for n in ("phase4-results", "contract-results", "manifest", "local-script-runner", "engine", "work-root", "output-dir")]
    shutil.rmtree(work, ignore_errors=True); shutil.rmtree(out, ignore_errors=True); work.mkdir(parents=True); out.mkdir(parents=True)
    manifest = readj(manifest_path); owned = [e for e in manifest["entries"] if e["entry_class"] == "OWNED_PAYLOAD"]
    regs = sorted((e for e in owned if e["type"] == "regular" and e.get("size", 0) > 0 and e.get("elf") is not True), key=lambda e: e["payload_path"])
    syms = sorted((e for e in owned if e["type"] == "symlink"), key=lambda e: e["payload_path"])
    if not regs or not syms: raise RuntimeError("missing deterministic candidates")
    cand = {"regular": regs[0], "symlink": syms[0]}
    accepted = {"schema_version": 1, "pass": sha(p4 / "result-index.json") == P4_INDEX, "expected_result_index_sha256": P4_INDEX, "observed_result_index_sha256": sha(p4 / "result-index.json")}; writej(out / "accepted-inputs.json", accepted)

    seed = work / "seed"; so = out / "seed"
    seed_install = invoke(local, engine, contract, seed, "install", so / "install.json", "runtime-base")
    seed_verify = invoke(local, engine, contract, seed, "verify", so / "verify.json")
    seed_id = identity(seed); writej(so / "identity.json", seed_id)

    success_specs = {"exact-noop": None, "regular-bytes": "regular", "regular-mode": "regular", "regular-wrong-type": "regular", "symlink-target": "symlink", "missing-regular": "regular", "missing-symlink": "symlink"}
    success: dict[str, Any] = {}; clone_rows: dict[str, Any] = {}
    for name, ck in success_specs.items():
        root, ro = work / "success" / name, out / "success" / name
        clone_rows["success/" + name] = clone(seed, root, cand["regular"]["payload_path"]); before = identity(root)
        row: dict[str, Any] = {"schema_version": 1, "name": name, "clone": clone_rows["success/" + name], "before": before}
        if name == "exact-noop":
            op = invoke(local, engine, contract, root, "install", ro / "install.json", "runtime-base"); verify = invoke(local, engine, contract, root, "verify", ro / "verify.json"); after = identity(root)
            row.update(operation=op, verify=verify, after=after, classification="exact-same-version-noop")
            row["pass"] = op["returncode"] == 0 and op["result"].get("noop") is True and op["result"].get("action_counts") == {"noop": 714} and op["result"].get("mutation_count") == 0 and verify["returncode"] == 0 and before == after
        else:
            e = cand[ck]; rel = e["payload_path"]; p = root / "prefix" / rel
            row.update(candidate=mrecord(e), mutation=mutate(p, name, e["mode"]), corrupted=identity(root))
            pre = invoke(local, engine, contract, root, "verify", ro / "pre-verify.json")
            op = invoke(local, engine, contract, root, "install", ro / "install.json", "runtime-base")
            post = invoke(local, engine, contract, root, "verify", ro / "post-verify.json")
            after = identity(root); final = snap(p)
            row.update(pre_verify=pre, operation=op, post_verify=post, after=after, final_path=final, classification=("missing-leaf-repair-supported" if name.startswith("missing-") else "in-place-registered-repair-regression"))
            row["pass"] = pre["returncode"] == 44 and pre["result"].get("bad_paths") == [rel] and op["returncode"] == 0 and op["result"].get("action_counts") == {"noop": 713, "repair": 1} and op["result"].get("mutation_count") == 2 and post["returncode"] == 0 and post["result"].get("bad_paths") == [] and after["portable"]["fingerprint"] == PORTABLE and after["registry"] == before["registry"] and after["transactions"] == [] and matches_snap(final, mrecord(e))
        writej(ro / "scenario.json", row); success[name] = row

    boundaries = {
        "prepared": (["--crash-after-prepared"], 90, "PREPARED", [], 0, False),
        "intent-1": (["--crash-after-intents", "1"], 93, "APPLYING", [("created", "INTENT")], 0, False),
        "mutation-1": (["--crash-after-mutations", "1"], 91, "APPLYING", [("created", "APPLIED")], 1, False),
        "intent-2": (["--crash-after-intents", "2"], 93, "APPLYING", [("created", "APPLIED"), ("registry", "INTENT")], 2, False),
        "mutation-2": (["--crash-after-mutations", "2"], 91, "APPLYING", [("created", "APPLIED"), ("registry", "APPLIED")], 2, False),
        "committed": (["--crash-after-commit"], 92, "COMMITTED", [("created", "APPLIED"), ("registry", "APPLIED")], 0, True),
    }
    crashes: dict[str, Any] = {}
    for leaf_kind in ("regular", "symlink"):
        e = cand[leaf_kind]; rel = e["payload_path"]
        for boundary, (flags, expected_rc, state, mutations, restored, committed) in boundaries.items():
            name = f"{leaf_kind}-{boundary}"; root, ro = work / "crash" / name, out / "crash" / name
            clone_rows["crash/" + name] = clone(seed, root, cand["regular"]["payload_path"])
            p = root / "prefix" / rel; before_registry = registry(root); mutation = mutate(p, "missing-" + leaf_kind, e["mode"])
            crash_run = invoke(local, engine, contract, root, "install", ro / "crash-install.json", "runtime-base", flags)
            tx_before = txs(root); recover1 = invoke(local, engine, contract, root, "recover", ro / "recover-1.json"); tx_after1 = txs(root); recover2 = invoke(local, engine, contract, root, "recover", ro / "recover-2.json"); tx_after2 = txs(root); verify = invoke(local, engine, contract, root, "verify", ro / "verify.json"); final = snap(p); after_registry = registry(root)
            observed_mut = [(x.get("kind"), x.get("status")) for x in (tx_before[0].get("mutations", []) if len(tx_before) == 1 else [])]
            action1 = recover1.get("result", {}).get("actions", [{}])[0] if recover1.get("result") else {}
            action2s = recover2.get("result", {}).get("actions", []) if recover2.get("result") else []
            if committed:
                passed = crash_run["returncode"] == expected_rc and len(tx_before) == 1 and tx_before[0].get("state") == state and observed_mut == mutations and action1.get("action") == "FINALIZED_COMMIT" and tx_after1 == [] and recover2["returncode"] == 0 and recover2["result"].get("transaction_count") == 0 and tx_after2 == [] and verify["returncode"] == 0 and verify["result"].get("bad_paths") == [] and matches_snap(final, mrecord(e)) and after_registry == before_registry
            else:
                passed = crash_run["returncode"] == expected_rc and len(tx_before) == 1 and tx_before[0].get("state") == state and observed_mut == mutations and action1.get("action") == "ROLLED_BACK" and action1.get("restored_count") == restored and len(tx_after1) == 1 and tx_after1[0].get("state") == "ROLLED_BACK" and recover2["returncode"] == 0 and action2s and action2s[0].get("action") == "NOOP_ROLLED_BACK" and tx_after2 == tx_after1 and verify["returncode"] == 44 and verify["result"].get("bad_paths") == [rel] and final.get("type") == "absent" and after_registry == before_registry
            row = {"schema_version": 1, "name": name, "leaf_kind": leaf_kind, "boundary": boundary, "candidate": mrecord(e), "mutation": mutation, "expected": {"returncode": expected_rc, "journal_state": state, "mutations": mutations, "restored_count": restored, "committed": committed}, "crash_run": crash_run, "transactions_before_recovery": tx_before, "recover_1": recover1, "transactions_after_recovery_1": tx_after1, "recover_2": recover2, "transactions_after_recovery_2": tx_after2, "verify": verify, "final_path": final, "registry_before": before_registry, "registry_after": after_registry, "pass": passed}
            writej(ro / "scenario.json", row); crashes[name] = row

    clone_summary = {"schema_version": 1, "pass": all(all(v.values()) for v in clone_rows.values()), "scenario_count": len(clone_rows), "scenarios": clone_rows}; writej(out / "clone-separation.json", clone_summary)
    precommit = [v for v in crashes.values() if not v["expected"]["committed"]]; committed_rows = [v for v in crashes.values() if v["expected"]["committed"]]
    checks = {
        "accepted_phase4_input": accepted["pass"],
        "seed_install_pass": seed_install["returncode"] == 0 and seed_install["result"].get("pass") is True,
        "seed_install_create_714": seed_install["result"].get("action_counts") == {"create": 714},
        "seed_install_mutations_715": seed_install["result"].get("mutation_count") == 715,
        "seed_verify_pass": seed_verify["returncode"] == 0 and seed_verify["result"].get("bad_paths") == [],
        "seed_portable_exact": seed_id["portable"]["fingerprint"] == PORTABLE,
        "seed_registry_714": seed_id["registry"]["artifact_count"] == 1 and seed_id["registry"]["owned_path_count"] == 714,
        "seed_transactions_empty": seed_id["transactions"] == [],
        "clone_count_19": clone_summary["scenario_count"] == 19,
        "clone_inode_separation": clone_summary["pass"],
        "success_names_exact": set(success) == set(success_specs),
        "success_all_pass": all(v["pass"] for v in success.values()),
        "exact_noop_pass": success["exact-noop"]["pass"],
        "in_place_regressions_four": sum(v["classification"] == "in-place-registered-repair-regression" and v["pass"] for v in success.values()) == 4,
        "missing_repairs_two": sum(v["classification"] == "missing-leaf-repair-supported" and v["pass"] for v in success.values()) == 2,
        "success_registry_exact": all(v["before"]["registry"] == v["after"]["registry"] for k, v in success.items() if k != "exact-noop"),
        "success_portable_exact": all(v["after"]["portable"]["fingerprint"] == PORTABLE for v in success.values()),
        "success_transactions_empty": all(v["after"]["transactions"] == [] for v in success.values()),
        "crash_count_12": len(crashes) == 12,
        "crash_names_exact": set(crashes) == {f"{k}-{b}" for k in ("regular", "symlink") for b in boundaries},
        "crash_all_pass": all(v["pass"] for v in crashes.values()),
        "crash_returncodes_exact": all(v["crash_run"]["returncode"] == v["expected"]["returncode"] for v in crashes.values()),
        "crash_journal_states_exact": all(len(v["transactions_before_recovery"]) == 1 and v["transactions_before_recovery"][0].get("state") == v["expected"]["journal_state"] for v in crashes.values()),
        "crash_mutation_kinds_exact": all([(x.get("kind"), x.get("status")) for x in v["transactions_before_recovery"][0].get("mutations", [])] == [tuple(x) for x in v["expected"]["mutations"]] for v in crashes.values()),
        "precommit_count_10": len(precommit) == 10,
        "precommit_rollback_actions": all(v["recover_1"]["result"]["actions"][0]["action"] == "ROLLED_BACK" for v in precommit),
        "precommit_restored_counts": all(v["recover_1"]["result"]["actions"][0]["restored_count"] == v["expected"]["restored_count"] for v in precommit),
        "precommit_missing_state_restored": all(v["final_path"]["type"] == "absent" for v in precommit),
        "precommit_registry_exact": all(v["registry_before"] == v["registry_after"] for v in precommit),
        "precommit_verify_bad_path": all(v["verify"]["result"]["bad_paths"] == [v["candidate"]["path"]] for v in precommit),
        "precommit_retained_rolledback": all(len(v["transactions_after_recovery_1"]) == 1 and v["transactions_after_recovery_1"][0]["state"] == "ROLLED_BACK" for v in precommit),
        "precommit_second_recover_noop": all(v["recover_2"]["result"]["actions"][0]["action"] == "NOOP_ROLLED_BACK" for v in precommit),
        "committed_count_two": len(committed_rows) == 2,
        "committed_finalize_actions": all(v["recover_1"]["result"]["actions"][0]["action"] == "FINALIZED_COMMIT" for v in committed_rows),
        "committed_paths_exact": all(matches_snap(v["final_path"], v["candidate"]) for v in committed_rows),
        "committed_registry_exact": all(v["registry_before"] == v["registry_after"] for v in committed_rows),
        "committed_verify_pass": all(v["verify"]["result"]["bad_paths"] == [] for v in committed_rows),
        "committed_transactions_clean": all(v["transactions_after_recovery_1"] == [] and v["transactions_after_recovery_2"] == [] for v in committed_rows),
        "committed_second_recover_zero": all(v["recover_2"]["result"]["transaction_count"] == 0 for v in committed_rows),
    }
    if len(checks) != 39: raise RuntimeError(f"unexpected check count {len(checks)}")
    failed = sorted(k for k, v in checks.items() if not v)
    summary = {"schema_version": 1, "pass": not failed, "check_count": 39, "checks": checks, "failed_checks": failed, "accepted_input": accepted, "seed": {"install": seed_install, "verify": seed_verify, "identity": seed_id}, "candidates": {k: mrecord(v) for k, v in cand.items()}, "success_scenarios": sorted(success), "crash_scenarios": sorted(crashes), "claim_boundary": {"proved": "The candidate intervention repairs missing registered regular and symlink leaves and preserves recovery semantics at six crash boundaries for each leaf type.", "not_proved": "Gate 3A product acceptance and downstream Gate 1 or Gate 2 regressions remain unproved."}}
    writej(out / "scenario-summary.json", summary); print(json.dumps(summary, indent=2, sort_keys=True)); print("\nSTAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION=" + ("PASS" if summary["pass"] else "FAIL"))
    return 81 if a.require_pass and not summary["pass"] else 0


if __name__ == "__main__": raise SystemExit(main())
