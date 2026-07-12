#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, os, shutil, stat, subprocess, sys
from pathlib import Path

P4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"


def cjson(v): return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()
def readj(p):
    v = json.loads(p.read_text())
    if not isinstance(v, dict): raise ValueError(p)
    return v
def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def writej(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(cjson(v))


def kind(p):
    try: s = p.lstat()
    except FileNotFoundError: return "absent"
    if stat.S_ISLNK(s.st_mode): return "symlink"
    if stat.S_ISDIR(s.st_mode): return "directory"
    if stat.S_ISREG(s.st_mode): return "regular"
    return "special"


def snap(p):
    k = kind(p); r = {"path": str(p), "type": k}
    if k == "absent": return r
    s = p.lstat(); r["mode"] = f"{stat.S_IMODE(s.st_mode):04o}"
    if k == "regular": r.update(size=s.st_size, sha256=sha(p))
    elif k == "symlink": r["target"] = os.readlink(p)
    return r


def paths(root):
    out = []
    for cur, ds, fs in os.walk(root, followlinks=False):
        ds.sort(); fs.sort(); b = Path(cur)
        out += [b / x for x in ds] + [b / x for x in fs]
    return sorted(out, key=lambda p: p.relative_to(root).as_posix())


def portable(prefix):
    h = hashlib.sha256(); counts = {x: 0 for x in ("directory", "regular", "symlink", "special")}
    for p in paths(prefix):
        rel = p.relative_to(prefix).as_posix(); s = p.lstat(); mode = f"{stat.S_IMODE(s.st_mode):04o}"
        if stat.S_ISREG(s.st_mode): k, size, digest, target = "regular", str(s.st_size), sha(p), ""
        elif stat.S_ISDIR(s.st_mode): k, size, digest, target = "directory", "", "", ""
        elif stat.S_ISLNK(s.st_mode): k, size, digest, target = "symlink", "", "", os.readlink(p)
        else: k, size, digest, target = "special", "", "", ""
        counts[k] += 1; h.update("\t".join((rel, k, mode, size, digest, target)).encode("utf-8", "surrogateescape") + b"\n")
    return {"fingerprint": h.hexdigest(), "entry_count": sum(counts.values()), "type_counts": counts}


def registry(root):
    p = root / ".cpython-android-cli/registry.json"; data = p.read_bytes(); v = json.loads(data)
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "artifact_count": len(v["artifacts"]), "owned_path_count": len(v["owned_paths"])}


def txs(root):
    d = root / ".cpython-android-cli/transactions"; out = []
    if not d.is_dir(): return out
    for t in sorted(x for x in d.iterdir() if x.is_dir()):
        j = t / "journal.json"; row = {"name": t.name, "journal_exists": j.is_file()}
        if j.is_file():
            v = readj(j); row.update(state=v.get("state"), operation=v.get("operation"), artifact=v.get("artifact"), mutations=v.get("mutations", []), preserved=v.get("preserved", []))
        out.append(row)
    return out


def identity(root): return {"portable": portable(root / "prefix"), "registry": registry(root), "transactions": txs(root)}
def mrecord(e): return {"path": e["payload_path"], "type": e["type"], "mode": e["mode"], "size": e.get("size"), "sha256": e.get("sha256"), "symlink_target": e.get("symlink_target")}


def engine(local, script, contract, root, op, output, artifact=None):
    cmd = [sys.executable, "-I", "-B", "-S", str(local), str(script), "--installation-root", str(root), "--operation", op, "--output", str(output)]
    if op == "install": cmd += ["--contract-results", str(contract)]
    if artifact: cmd += ["--artifact", artifact]
    run = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    log = output.with_suffix(".log"); log.parent.mkdir(parents=True, exist_ok=True); log.write_text(run.stdout)
    return {"returncode": run.returncode, "result": readj(output), "log": log.name}


def clone(seed, dst, probe):
    shutil.copytree(seed, dst, symlinks=True, copy_function=shutil.copy2)
    sr, dr = seed / ".cpython-android-cli/registry.json", dst / ".cpython-android-cli/registry.json"
    sp, dp = seed / "prefix" / probe, dst / "prefix" / probe
    return {"root_inode_separate": seed.stat().st_ino != dst.stat().st_ino, "registry_inode_separate": sr.stat().st_ino != dr.stat().st_ino, "probe_inode_separate": sp.stat().st_ino != dp.stat().st_ino}


def mutate(p, name, mode):
    before = snap(p)
    if name == "regular-bytes": p.write_bytes(b"stage3c-gate3a-corrupted-regular\n"); os.chmod(p, int(mode, 8))
    elif name == "regular-mode": os.chmod(p, 0o600 if int(mode, 8) != 0o600 else 0o644)
    elif name == "symlink-target": p.unlink(); os.symlink("stage3c-gate3a-invalid-target", p)
    elif name == "regular-wrong-type": p.unlink(); p.mkdir(mode=0o755)
    elif name in {"missing-regular", "missing-symlink"}: p.unlink()
    else: raise ValueError(name)
    return {"kind": name, "before": before, "after": snap(p)}


def main():
    ap = argparse.ArgumentParser()
    for name in ("phase4-results", "contract-results", "manifest", "local-script-runner", "engine", "work-root", "output-dir"): ap.add_argument("--" + name, required=True, type=Path)
    ap.add_argument("--require-pass", action="store_true"); a = ap.parse_args()
    p4, contract, manifest_path, local, eng, work, out = [getattr(a, x.replace("-", "_")).resolve() for x in ("phase4-results", "contract-results", "manifest", "local-script-runner", "engine", "work-root", "output-dir")]
    shutil.rmtree(work, ignore_errors=True); shutil.rmtree(out, ignore_errors=True); work.mkdir(parents=True); out.mkdir(parents=True)
    manifest = readj(manifest_path); owned = [e for e in manifest["entries"] if e["entry_class"] == "OWNED_PAYLOAD"]
    regs = sorted((e for e in owned if e["type"] == "regular" and e.get("size", 0) > 0 and e.get("elf") is not True), key=lambda e: e["payload_path"])
    syms = sorted((e for e in owned if e["type"] == "symlink"), key=lambda e: e["payload_path"])
    if not regs or not syms: raise RuntimeError("missing deterministic candidates")
    cand = {"regular": regs[0], "symlink": syms[0]}; expected = {e["payload_path"]: mrecord(e) for e in owned}
    accepted = {"schema_version": 1, "pass": sha(p4 / "result-index.json") == P4_INDEX, "expected_result_index_sha256": P4_INDEX, "observed_result_index_sha256": sha(p4 / "result-index.json")}; writej(out / "accepted-inputs.json", accepted)

    seed = work / "seed"; so = out / "seed"
    seed_install = engine(local, eng, contract, seed, "install", so / "install.json", "runtime-base")
    seed_verify = engine(local, eng, contract, seed, "verify", so / "verify.json")
    seed_id = identity(seed); writej(so / "identity.json", seed_id)

    specs = {"exact-noop": None, "regular-bytes": "regular", "regular-mode": "regular", "symlink-target": "symlink", "regular-wrong-type": "regular", "missing-regular": "regular", "missing-symlink": "symlink"}
    scenarios, clones = {}, {}
    for name, ck in specs.items():
        root, ro = work / name, out / "scenarios" / name
        clones[name] = clone(seed, root, cand["regular"]["payload_path"]); before = identity(root)
        r = {"schema_version": 1, "name": name, "root": str(root), "before": before, "clone": clones[name]}
        if name == "exact-noop":
            op = engine(local, eng, contract, root, "install", ro / "install.json", "runtime-base"); verify = engine(local, eng, contract, root, "verify", ro / "verify.json"); after = identity(root)
            r.update(operation=op, verify=verify, after=after, classification="exact-same-version-noop")
            r["pass"] = op["returncode"] == 0 and op["result"].get("noop") is True and op["result"].get("action_counts") == {"noop": 714} and op["result"].get("mutation_count") == 0 and verify["returncode"] == 0 and verify["result"].get("pass") is True and before == after
        else:
            e = cand[ck]; rel = e["payload_path"]; p = root / "prefix" / rel
            r.update(candidate=mrecord(e), mutation=mutate(p, name, e["mode"]), corrupted=identity(root))
            pre = engine(local, eng, contract, root, "verify", ro / "pre-verify.json"); op = engine(local, eng, contract, root, "install", ro / "install.json", "runtime-base"); r.update(pre_verify=pre, operation=op)
            if name.startswith("missing-"):
                t0 = txs(root); rec1 = engine(local, eng, contract, root, "recover", ro / "recover-1.json"); t1 = txs(root); rec2 = engine(local, eng, contract, root, "recover", ro / "recover-2.json"); t2 = txs(root); post = engine(local, eng, contract, root, "verify", ro / "post-verify.json"); after = identity(root)
                rows = {x["path"] for x in readj(root / ".cpython-android-cli/registry.json")["owned_paths"]}
                r.update(transactions_before_recover=t0, recover_1=rec1, transactions_after_recover_1=t1, recover_2=rec2, transactions_after_recover_2=t2, post_verify=post, after=after, final_path=snap(p), registry_row_present=rel in rows, classification="missing-leaf-repair-unsupported")
                r["pass"] = pre["returncode"] == 44 and pre["result"].get("bad_paths") == [rel] and op["returncode"] == 44 and "FileNotFoundError" in op["result"].get("error", "") and len(t0) == 1 and t0[0].get("state") == "APPLYING" and rec1["returncode"] == 0 and rec1["result"].get("actions", [{}])[0].get("action") == "ROLLED_BACK" and len(t1) == 1 and t1[0].get("state") == "ROLLED_BACK" and rec2["returncode"] == 0 and rec2["result"].get("actions", [{}])[0].get("action") == "NOOP_ROLLED_BACK" and t2 == t1 and post["returncode"] == 44 and post["result"].get("bad_paths") == [rel] and r["final_path"]["type"] == "absent" and r["registry_row_present"] is True
            else:
                post = engine(local, eng, contract, root, "verify", ro / "post-verify.json"); after = identity(root)
                r.update(post_verify=post, after=after, final_path=snap(p), classification="in-place-registered-repair-supported")
                r["pass"] = pre["returncode"] == 44 and pre["result"].get("bad_paths") == [rel] and op["returncode"] == 0 and op["result"].get("action_counts") == {"noop": 713, "repair": 1} and op["result"].get("mutation_count") == 2 and post["returncode"] == 0 and post["result"].get("pass") is True and after["portable"]["fingerprint"] == PORTABLE and after["registry"] == before["registry"] and after["transactions"] == [] and r["final_path"]["type"] == e["type"]
        writej(ro / "scenario.json", r); scenarios[name] = r

    clone_summary = {"schema_version": 1, "pass": all(all(x.values()) for x in clones.values()), "scenarios": clones}; writej(out / "clone-separation.json", clone_summary)
    checks = {"accepted_phase4_input": accepted["pass"], "seed_install_pass": seed_install["returncode"] == 0 and seed_install["result"].get("pass") is True, "seed_install_create_714": seed_install["result"].get("action_counts") == {"create": 714}, "seed_install_mutations_715": seed_install["result"].get("mutation_count") == 715, "seed_verify_pass": seed_verify["returncode"] == 0 and seed_verify["result"].get("pass") is True, "seed_registry_714": seed_id["registry"]["artifact_count"] == 1 and seed_id["registry"]["owned_path_count"] == 714, "seed_portable_exact": seed_id["portable"]["fingerprint"] == PORTABLE, "seed_transactions_empty": seed_id["transactions"] == [], "clone_inode_separation": clone_summary["pass"], "scenario_names_exact": set(scenarios) == set(specs), "all_scenarios_classified": all(x.get("classification") for x in scenarios.values()), "all_scenarios_match_expected_observation": all(x.get("pass") is True for x in scenarios.values()), "supported_repairs_four": sum(x.get("classification") == "in-place-registered-repair-supported" for x in scenarios.values()) == 4, "unsupported_missing_two": sum(x.get("classification") == "missing-leaf-repair-unsupported" for x in scenarios.values()) == 2, "exact_noop_one": sum(x.get("classification") == "exact-same-version-noop" for x in scenarios.values()) == 1, "candidate_regular_exact": scenarios["regular-bytes"]["candidate"] == expected[cand["regular"]["payload_path"]], "candidate_symlink_exact": scenarios["symlink-target"]["candidate"] == expected[cand["symlink"]["payload_path"]]}
    if len(checks) != 17: raise RuntimeError(len(checks))
    failed = sorted(k for k, v in checks.items() if not v)
    summary = {"schema_version": 1, "pass": not failed, "check_count": 17, "checks": checks, "failed_checks": failed, "accepted_input": accepted, "seed": {"install": seed_install, "verify": seed_verify, "identity": seed_id}, "candidates": {k: mrecord(v) for k, v in cand.items()}, "scenario_names": sorted(scenarios), "classifications": {k: v["classification"] for k, v in sorted(scenarios.items())}, "claim_boundary": {"proved": "The frozen engine's exact same-version NOOP and in-place registered repair behavior were classified independently from missing-leaf failure and recovery-residue behavior.", "not_proved": "Gate 3A product acceptance, missing-leaf repair, preservation policy, addon lifecycle, uninstall, upgrade, and downgrade remain unproved."}}
    writej(out / "scenario-summary.json", summary); print(json.dumps(summary, indent=2, sort_keys=True)); print("\nSTAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC=" + ("PASS" if summary["pass"] else "FAIL"))
    return 71 if a.require_pass and not summary["pass"] else 0


if __name__ == "__main__": raise SystemExit(main())
