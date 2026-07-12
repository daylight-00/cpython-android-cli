# Phase 4 Missing-Leaf Repair Intervention Handoff — 2026-07-12

> **Branch:** `agent/phase4-missing-leaf-repair-intervention`
> **Current action:** authoritative Termux intervention run
> **Gate 3A product acceptance:** blocked

## Frozen diagnostic authority

```text
archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

scenario checks
  17/17

independent verifier
  31/31
```

The frozen diagnostic proves missing registered regular and symlink repair are unsupported by the prior engine.

## Candidate implementation

```text
recovery_operations_missing_leaf.py
  wraps the frozen install operation
  rewrites only absent-path replaced intents to created intents
  skips only the corresponding nonexistent install-leaf-backup move
  restores frozen module globals in finally

recovery_engine_missing_leaf.py
  injects the candidate install operation into the frozen CLI engine
```

Existing mismatching paths retain the frozen `replaced` behavior.

## Target scope

```text
7 success/regression roots
12 crash-recovery roots
19 independent cloned roots total
39 scenario checks
51 independent checks
```

## Local validation

```text
Python compile                    PASS
shell bash -n                     PASS
synthetic absent-path rewrite     PASS
synthetic existing-path backup    PASS
independent verifier fixture      51/51 PASS
```

## Authority rule

Do not merge the corrective PR or call Gate 3A accepted from local validation. Run the Termux workflow, upload the complete TGZ, independently inspect it, and preserve any failure without weakening the expected recovery matrix.
