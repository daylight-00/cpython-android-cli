# Stage 3-C Phase 2 Artifact Manifest Input-Copy Incident

> **Status:** SECOND TARGET RUN FAILED — preserved and diagnosed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase2-artifact-manifest-schema-corrected-results-20260711-211629.tgz`

## Result archive identity

```text
sha256
  6629b360c564af12fb34f55735ab1e08c8615666b4cdf93a5eb564938e4864ca
```

The uploaded TGZ contains 30 members. All member names are relative and no device, FIFO, or other special entry is present.

## Observed workflow result

```text
manifest_generation          1
source_mutation              0
independent_verification     1
workflow pass            false
```

The isolated local-script bootstrap worked. Both tools imported `artifact_manifest_contract.py` and entered their `main()` functions.

## Primary failure

The generator failed while reading the accepted ownership evidence copy:

```text
FileNotFoundError:
  results/termux/stage3c-phase2-artifact-manifest-schema/
    input/ownership/canonical-before.json
```

The generator intentionally reads these four accepted ownership-result identities:

```text
canonical-before.json
canonical-after.json
runtime-before.json
runtime-after.json
```

The workflow copied the ownership model, verifier outputs, TSVs, summaries, and mutation result into `input/ownership/`, but omitted these four fingerprint files.

This is a result-staging wiring defect. It is not a component, ownership, product-lock, manifest-schema, or source-mutation failure.

## Secondary failure

Because generation stopped before creating:

```text
generation.json
manifest-index.json
manifests/*.manifest.json
```

the independent verifier then attempted to hash the absent `manifest-index.json` and raised another `FileNotFoundError`.

That traceback is secondary to the generator input-copy failure.

## Preserved successful controls

Canonical promoted source:

```text
entries before/after
  3155 / 3155

fingerprint before/after
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Runtime-base:

```text
entries before/after
  714 / 714

fingerprint before/after
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

```text
source mutation check
  PASS
```

The accepted ownership model, structural verifier, safety verifier, product lock, and Phase 1 final verification were copied into the result tree.

## Correction

The corrected workflow:

```text
requires all four accepted ownership fingerprint files
copies all four files into input/ownership/
keeps the current-run canonical/runtime before/after fingerprints separate
runs the 48-check verifier only after successful generation
emits an explicit blocked verification JSON when generation fails
```

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

Both failed target TGZs remain preserved evidence and must not be rewritten as PASS results.
