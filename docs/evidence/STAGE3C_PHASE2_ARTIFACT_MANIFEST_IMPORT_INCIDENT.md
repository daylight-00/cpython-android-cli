# Stage 3-C Phase 2 Artifact Manifest Import Incident

> **Status:** FIRST TARGET RUN FAILED — preserved and diagnosed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase2-artifact-manifest-schema-results-20260711-205317.tgz`

## Result archive identity

```text
sha256
  1b82ba4f800cac2e84a07edee7734053854da513085afad85b726f53ebf6d923
```

The uploaded TGZ contains 29 members. All archive member names are relative and no device or FIFO entry is present.

## Observed workflow result

```text
manifest_generation          1
source_mutation              0
independent_verification     1
workflow pass            false
```

No manifest, manifest index, generation result, or final verification was produced.

## Exact failure

Generator:

```text
Traceback (most recent call last):
  File ".../generate-artifact-manifests.py", line 11, in <module>
    from artifact_manifest_contract import (...)
ModuleNotFoundError: No module named 'artifact_manifest_contract'
```

Verifier:

```text
Traceback (most recent call last):
  File ".../verify-artifact-manifests.py", line 9, in <module>
    from artifact_manifest_contract import (...)
ModuleNotFoundError: No module named 'artifact_manifest_contract'
```

## Root cause

The target workflow invoked both tools as:

```text
python -I -B -S <script>
```

On the accepted target runtime, isolated mode does not place the selected script directory on `sys.path`. Therefore the sibling project module:

```text
artifact_manifest_contract.py
```

was not importable.

This is a workflow bootstrap defect. It is not an ownership, product identity, component manifest, or source mutation failure.

## Preserved successful controls

Canonical promoted source:

```text
entries before/after
  3155 / 3155

fingerprint before/after
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

pycache
  0

special files
  0
```

Runtime-base:

```text
entries before/after
  714 / 714

fingerprint before/after
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

pycache
  0

special files
  0
```

```text
source mutation check
  PASS
```

The accepted ownership evidence and product lock were copied successfully into the result tree before the import failure.

## Correction

The corrected workflow retains:

```text
-I
-B
-S
```

It does not enable `PYTHONPATH`, user site packages, or arbitrary current-working-directory imports.

A small isolated bootstrap now:

```text
resolves the selected local script
adds only that script's parent directory to sys.path
replaces sys.argv with the selected script and its arguments
executes the script with runpy.run_path(..., run_name="__main__")
```

This narrowly permits the generator and verifier to import their tracked sibling contract module while preserving the intended isolated environment.

## Non-relaxation rule

The correction does not change:

```text
42 generator checks
48 independent verifier checks
ownership manifest identities
artifact entry counts
product identity
canonical JSON contract
manifest index integrity requirements
canonical or runtime-base mutation gates
claim boundary
```

The failed TGZ remains first-run evidence and must not be rewritten as a PASS.
