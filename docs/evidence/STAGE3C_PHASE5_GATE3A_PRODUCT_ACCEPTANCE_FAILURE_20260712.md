# Stage 3-C Phase 5 Gate 3A Product Acceptance Failure — 2026-07-12

> **Status:** FROZEN INFRASTRUCTURE FAILURE
> **Product result:** NOT FAILED
> **Acceptance claim:** NOT CLOSED

## Reported marker

```text
STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_ACCEPTANCE=FAIL rc=1
```

## Authoritative archive identity

```text
archive
  stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-190146.tgz

sha256
  850fe89dcd4b1baadad1d28f363df30401ff7b65a475168982da5699fe3d80d2

size
  48,093,068 bytes

members
  1,281

regular files / directories
  1,184 / 97

unsafe paths / symlinks / hardlinks / special entries
  0 / 0 / 0 / 0
```

## Result-index verification

```text
Gate 3A root result-index sha256
  df5b2f87aff019b0baed9f27f678548a0f6bbfb2363160eadd0216f8780882e7

Gate 3A root indexed files
  1,171 / 1,171 exact

hash / size / mode / missing / duplicate / coverage mismatches
  0

Phase 4 input result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

Phase 4 input indexed files
  294 / 294 exact

Phase 4I input result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

Phase 4I input indexed files
  523 / 523 exact
```

## Completed product evidence

Every product-facing component completed successfully:

```text
repair scenarios
  29 / 29 PASS

exact reinstall NOOP
  PASS

isolated repair roots
  6 / 6 PASS

sequential repair roots
  6 / 6 PASS

Gate 1 regression
  80 / 80 PASS

engine verification
  PASS

Python
  3.14.6 / Android / aarch64

HTTPS
  200

smoke-termux
  PASS

uv venv
  PASS

uv run anyio
  PASS

native closure
  81 ELF / 329 edges / 0 unresolved

system SONAME dlopen
  5 / 5

extension imports
  67 / 67

input mutation control
  PASS
```

Workflow return codes were zero for every component except the final acceptance verifier:

```text
acceptance_verification
  1
```

## Exact failure

The final verifier did not begin its 69 checks. Its log was:

```text
Traceback (most recent call last):
  File ".../verify-gate3a-product-acceptance.py", line 8, in <module>
    from gate3a_acceptance_verify_repairs import repair_checks
ModuleNotFoundError: No module named 'gate3a_acceptance_verify_repairs'
```

The shell launched the modular verifier directly with:

```text
python -I -B -S verify-gate3a-product-acceptance.py
```

Python isolated mode intentionally omitted the script directory from `sys.path`. The scenario runner did not have this problem because it was executed through `run-isolated-local-script.py`, which explicitly adds only the selected script directory.

## Classification

```text
product failure
  NO

repair failure
  NO

runtime failure
  NO

verification logic failure
  NO EVIDENCE

verifier bootstrap failure
  YES

Gate 3A accepted
  NO
```

The archive proves that the product-facing workflow reached all expected PASS states, but Gate 3A remains open because the independent 69-check verifier never executed.

## Correction

The verifier entrypoint now adds its own resolved directory to `sys.path` before importing sibling verification modules. This preserves isolated mode without enabling `PYTHONPATH`, user site packages, or current-working-directory imports.

A one-command Termux wrapper was also added. It performs:

```text
input TGZ hash verification
fresh extraction
Gate 3A execution
success or failure status capture
result-index regeneration
final evidence TGZ creation
archive SHA256 and size reporting
```

The wrapper packages evidence even when the workflow fails.

## Rerun boundary

A fresh complete Termux run is required. The prior successful component outputs cannot be promoted without a new archive containing a completed 69-check verifier result and an exact regenerated result-index.
