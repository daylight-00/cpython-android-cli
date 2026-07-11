# Stage 3-C Phase 2: Archive Ownership and Structural Namespace

> **Status:** ACTIVE
> **Input:** frozen Stage 3-C Phase 1 component inventory and runtime identities

## Question

```text
Can runtime-base, development-addon, and test-addon be represented as
three disjoint exact payload owners while sharing only explicit structural
directory namespace?
```

## Run

```sh
bash experiments/stage3c-archive-ownership/run-archive-ownership-model.sh
```

## Frozen inputs

```text
results/termux/stage3c-phase1-component-policy/component-inventory.tsv
results/termux/stage3c-phase1-component-policy/component-policy.json
results/termux/stage3c-phase1-component-policy/component-policy-verification.json
results/termux/stage3c-phase1-runtime-base-final-validation/verification.json
work/termux/stage3b-promoted-runtime/prefix
work/termux/stage3c-phase1-isolated-variants/runtime-base/prefix
```

Identities:

```text
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84

canonical fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

## Artifact ownership

```text
runtime-base          714 exact owned entries
development-addon     454 exact owned entries
test-addon           1788 exact owned entries
selected total       2956 exact owned entries
unsupported GUI       199 excluded entries
```

The exact path is the ownership unit. A parent directory needed to carry an addon descendant is emitted separately as `STRUCTURAL_PARENT` and does not become recursively owned by the addon.

## Candidate envelope

```text
<artifact-id>/
  metadata/
  payload/
    <prefix-relative paths>
```

```text
extraction semantics     staging, not installation
runtime-base             standalone runtime
addons                    overlays requiring matching runtime-base
absolute paths            forbidden
parent traversal          forbidden
special entries           forbidden
hardlinks                 forbidden in the candidate model
```

## Analysis outputs

```text
artifact-owned-paths.tsv
artifact-structural-directories.tsv
shared-namespace-directories.tsv
artifact-ownership-summary.tsv
excluded-paths.txt
ownership-model.json
```

The analyzer performs 64 checks, including:

```text
accepted Phase 1 evidence identity
2956 selected / 199 excluded coverage
exact owned-path overlap = 0
five relative, contained symlinks
symlink targets exist and remain same-artifact owned
81 ELF rows remain runtime-base-owned
canonical license row remains runtime-base-owned
all external structural parents are selected canonical directories
runtime-base is the only standalone artifact
both addons require the accepted runtime-base identity
canonical and runtime trees contain no pycache or special files
```

## Independent verifier

```text
verification.json
```

The 74-check verifier independently re-derives:

```text
all selected owned rows and fields
all structural parent rows
all shared namespace rows
artifact summaries
three output manifest hashes
envelope and ownership contract fields
addon prerequisites
license boundary
source and runtime non-mutation
```

## Expected markers

```text
STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_ANALYSIS=PASS
ARCHIVE_OWNERSHIP_ACCEPTED_INPUTS=PASS
ARCHIVE_EXACT_OWNED_PATH_OVERLAP=0 PASS
ARCHIVE_STRUCTURAL_NAMESPACE_MODEL=PASS
ARCHIVE_SELECTED_SYMLINK_POLICY=PASS
ARCHIVE_LICENSE_OWNERSHIP=PASS
ARCHIVE_OWNERSHIP_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_MODEL=PASS
```

## Results

```text
results/termux/stage3c-phase2-archive-ownership-model/
  input/
    component-inventory.tsv
    component-policy.json
    component-policy-verification.json
    phase1-final-verification.json
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

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase2-archive-ownership-model"
ARCHIVE="$HOME/Downloads/stage3c-phase2-archive-ownership-model-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS proves exact artifact ownership and explicit shared structural namespace. It does not create archive bytes or prove reproducibility, hostile-input extraction safety, installation transactions, upgrades, rollback, or uninstall behavior.
