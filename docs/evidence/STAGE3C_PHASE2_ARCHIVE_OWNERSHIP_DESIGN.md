# Stage 3-C Phase 2 Archive Ownership Model Design

> **Status:** IMPLEMENTED — target evidence pending
> **Input:** frozen Stage 3-C Phase 1 component and runtime identities

## Problem

The frozen component manifest assigns each canonical product path exactly once. Archive composition additionally needs parent directory entries. A parent needed to carry an addon descendant must not be mistaken for duplicate recursive ownership.

The design therefore separates:

```text
OWNED_PAYLOAD
  exact component-selected product path

STRUCTURAL_PARENT
  canonical parent directory required to represent an owned descendant
  but owned by another selected artifact
```

## Artifact model

```text
runtime-base
  components
    RUNTIME_BASE
    RUNTIME_METADATA
    LICENSE
  standalone
  714 exact owned paths

development-addon
  components
    DEVELOPMENT
    DEVELOPMENT_METADATA
  overlay requiring runtime-base
  454 exact owned paths

test-addon
  components
    OPTIONAL_TEST_SUITE
    OPTIONAL_TEST_DEMO
  overlay requiring runtime-base
  1788 exact owned paths
```

```text
selected total             2956
unsupported GUI excluded    199
canonical total            3155
```

## Candidate envelope

```text
<artifact-id>/
  metadata/
  payload/
    <prefix-relative product paths>
```

Extraction is staging, not installation. `metadata/` is not copied into the installed runtime prefix.

Forbidden candidate entries:

```text
absolute paths
parent traversal
devices
fifos
sockets
hardlinks
```

## Exact ownership

```text
ownership unit
  exact manifest path

exclusive owned overlap
  zero

shared directory namespace
  explicit structural relationship, not recursive ownership
```

Development and test addons carry prerequisites for the accepted runtime-base component manifest and strict fingerprint.

## Directory removal direction

```text
remove an owned regular file or symlink by exact path
remove an owned directory only when empty
never recursively delete a structural parent
preserve unowned descendants and sentinels
```

This is ownership-model input for a later transaction design, not an installer implementation.

## Symlink policy

All five selected symlinks must be:

```text
relative
lexically prefix-contained
targeting an existing canonical product path
targeting a path owned by the same artifact
```

## License policy

```text
installed in-prefix license row
  owned only by runtime-base
  lib/python3.14/LICENSE.txt

independent artifact redistribution
  every archive must embed license material or mapping under metadata/
```

This avoids duplicate installed-path ownership while keeping addons independently understandable.

## Implementation

```text
experiments/stage3c-archive-ownership/
  analyze-archive-ownership.py
  verify-archive-ownership.py
  run-archive-ownership-model.sh
```

Analyzer:

```text
64 checks
exact owned-path manifest
structural-parent manifest
shared-namespace manifest
artifact summaries
candidate envelope and prerequisite model
```

Independent verifier:

```text
74 checks
re-derives every owned, structural, shared, and summary row
recomputes all three manifest hashes
checks frozen source and runtime non-mutation
```

## Output contract

```text
input/component-inventory.tsv
input/component-policy.json
input/component-policy-verification.json
input/phase1-final-verification.json
artifact-owned-paths.tsv
artifact-structural-directories.tsv
shared-namespace-directories.tsv
artifact-ownership-summary.tsv
excluded-paths.txt
ownership-model.json
canonical-before.json
canonical-after.json
runtime-before.json
runtime-after.json
source-mutation-check.txt
workflow-status.json
verification.json
```

## Claim boundary

A PASS proves disjoint exact payload ownership and explicit structural namespace requirements for the three selected artifacts.

It does not prove archive serialization, reproducibility, extraction safety, installation collision handling, upgrades, rollback, or uninstall transactions.
