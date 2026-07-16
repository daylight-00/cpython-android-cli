# E2-P2 Gate 1 Standalone Façade Result

> **Status:** FROZEN — repository façade and synthetic package verification complete
> **Repository input:** `68828691fcae382cf49b9dbc2b5231f9e21f9282`, tree `eea4b6e7c8ffb3b49f2b3c45e9ac0639055bb118`

## Accepted result

```text
stable command                       present
build/package/verify contract        version 1
pinned Stage 3-B entry points         exact
synthetic package reproducibility    PASS
facade execution and drift rejection PASS
archive mutation rejection           PASS
E2-P1 contract verification          preserved 68/68
Epoch 1 control verification         preserved except branch_active
```

The synthetic package run produces two independent E2-P1 envelopes and requires every release asset to be byte-identical. The general envelope verifier then rejects an archive-byte mutation.

## Transaction correction

The first repository transaction stopped before commit and push because the
independent verifier scanned the entire checkout for ignored bytecode residue.
That was broader than the E2-P2 ownership boundary: unrelated historical
`__pycache__` state could reject an otherwise exact façade change. The corrected
transaction scopes the check to `components/standalone/` and
`experiments/epoch2-standalone-build-facade/`, removes residue only under those
new paths, preserves the failed worktree before recovery, and uses file-backed
regression capture so compiler or compressor descendants cannot hold a pipe open.
The retained failed result archive has SHA-256
`3cb8e27e9ec9b8abcadc5fd342f29c8cc05bbdc66efa548cf31da74cb2492e50`.

## Gate 2 preflight correction

The first read-only Gate 2 preflight completed without a build and retained result archive SHA-256 `3b11605e4711adde6d52f11c7b38454ee0110528175bc3c74c45664b5dc36361`. It exposed an exec-boundary defect: `config/defaults.env` and ordinary `.local/env` assignments were visible to shell callers but were not exported to the Python façade. Consequently the public `plan build` and `plan package` commands failed before producer inspection, and the reported 18 blockers included cascading plan/provenance failures rather than 18 independent host deficiencies.

The correction exports the tracked target/version defaults and machine-local façade inputs from `scripts/lib/project-env.sh`, pins the corrected loader blob in the façade contract, and adds an isolated shell-to-Python regression. No CPython build, package, Android execution, or qualification occurred during this correction.

## Real-product status

```text
real CPython build       not run
real E2-P1 envelope      not produced
Android execution        not run
Termux qualification     not run
selectability            false
publication              not permitted
installer conversion     not started
```

## Next action

Run E2-P2 Gate 2 on the configured Linux workstation through the stable façade:

```text
components/standalone/bin/cpython-android-standalone build
components/standalone/bin/cpython-android-standalone package
components/standalone/bin/cpython-android-standalone verify --scope envelope --release-dir <release-dir>
```

The returned product remains unqualified and unselectable pending independent review and E2-P3 target qualification.
