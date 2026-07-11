# Stage 3-C Phase 2 Scope: Archive Ownership and Manifest Model

> **Status:** ACTIVE — contract design
> **Input:** frozen Stage 3-C Phase 1 component and runtime identities
> **Primary target:** Termux on Android arm64

## Phase question

> How should the frozen runtime, development, and test components be represented as independently inspectable archives and safely overlaid into one relocatable installation prefix without confusing payload ownership with shared directory structure?

## Frozen input

```text
runtime-base
  714 entries
  fingerprint
    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

development-addon
  454 component-owned entries

test-addon
  1788 component-owned entries

selected total
  2956 entries

unsupported-gui-source
  199 entries
  not distributed

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

Authoritative Phase 1 boundary:

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
docs/evidence/STAGE3C_PHASE1_RUNTIME_BASE_FINAL_RESULT.md
```

## Design pressure

The component partition assigns every canonical path exactly once. Archive creation introduces a different problem:

```text
payload ownership
  exact file, symlink, or directory row selected by the component manifest

structural namespace
  parent directories needed so an archive can carry an owned descendant
```

These must not be conflated.

Examples:

```text
development-addon owns include/python3.14/Python.h
but may require an archive path through include/ and include/python3.14/

test-addon owns lib/python3.14/test/...
but depends on the runtime namespace lib/ and lib/python3.14/
```

A duplicated directory entry in two archives must not imply two packages recursively own the same subtree.

## Candidate archive set

```text
runtime-base
  standalone runtime payload

development-addon
  overlay requiring a matching runtime-base

test-addon
  overlay requiring a matching runtime-base

unsupported-gui-source
  excluded from distribution
```

The addons are not standalone Python distributions.

## Candidate envelope model

Phase 2 will evaluate the following staging-oriented shape:

```text
<artifact-id>/
  metadata/
    manifest.json
    provenance.json
    licenses/
  payload/
    <prefix-relative product paths>
```

Candidate properties:

```text
archive extraction is staging, not installation
payload paths are prefix-relative
payload/ is independently inspectable
runtime-base payload/ may itself be exercised as a relocated prefix
metadata is outside the installed runtime payload
addons overlay payload paths into a matching runtime-base prefix
absolute archive paths are forbidden
.. path escape is forbidden
device, fifo, socket and other special entries are forbidden
hardlinks are forbidden unless explicitly introduced and revalidated later
```

This is a candidate until machine evidence closes the ownership and namespace gate.

## Ownership model to derive

For every selected artifact, derive:

```text
exact owned path set
owned regular-file set
owned directory set
owned symlink set
owned ELF set
required structural parent-directory set
structural parents owned by runtime-base
structural parents shared by multiple addons
exact path overlaps between artifacts
```

Required invariant:

```text
exact owned payload overlap = 0
```

Structural-parent overlap is expected and must be represented explicitly rather than hidden.

## Candidate installation ownership semantics

```text
exclusive ownership unit
  exact manifest path

shared directory namespace
  not recursive exclusive ownership

addon prerequisite
  matching product name, Python version, target ABI/API, and component-manifest identity

uninstall candidate rule
  remove owned non-directory entries
  remove an owned directory only when empty
  never recursively remove a shared structural parent

pre-existing exact path
  transaction policy deferred until the ownership model is frozen
```

The later installer must preserve unowned sentinel files under shared parents.

## License boundary

The canonical in-prefix license row remains owned by `runtime-base`.

Each independently redistributed addon still requires an understandable license mapping. Candidate approach:

```text
installed payload license path
  owned only by runtime-base

archive-envelope license material
  embedded in every distributable artifact outside payload/
```

This avoids duplicate installed-path ownership while keeping every archive independently redistributable and inspectable.

## Manifest schema direction

Phase 2 does not yet freeze the complete schema, but the ownership analysis must prepare fields for:

```text
schema version
artifact identity and role
product/Python/ABI/API identity
component-manifest identity
relative payload path
entry class: owned payload or structural parent
entry type
mode
regular-file size and SHA-256
symlink target
ELF marker
license mapping
addon prerequisite
```

Archive-header timestamps, uid/gid, owner names, compression, and byte reproducibility remain Phase 3 questions.

## First gate: exact archive ownership analysis

The first Phase 2 experiment must consume, without modifying:

```text
results/termux/stage3c-phase1-component-policy/component-inventory.tsv
results/termux/stage3c-phase1-component-policy/component-policy.json
results/termux/stage3c-phase1-component-policy/component-policy-verification.json
results/termux/stage3c-phase1-runtime-base-final-validation/verification.json
work/termux/stage3b-promoted-runtime/prefix
```

It must emit:

```text
artifact-owned-paths.tsv
artifact-structural-directories.tsv
shared-namespace-directories.tsv
artifact-ownership-summary.tsv
ownership-model.json
verification.json
source-mutation-check.txt
```

First-gate checks:

```text
accepted Phase 1 manifests and fingerprints match
selected owned entries equal 714 + 454 + 1788
excluded GUI entries equal 199
all exact selected paths map to one artifact
exact owned-path overlap is zero
all structural parents exist as canonical directories
all selected entries are regular files, directories, or symlinks
all five selected symlinks are relative and prefix-contained
all 81 ELF rows remain runtime-base-owned
license payload path remains runtime-base-owned
runtime and canonical source identities remain unchanged
```

## Acceptance conditions

```text
[ ] accepted Phase 1 evidence chain verified
[ ] exact owned path sets derived for three artifacts
[ ] exact owned overlap = 0
[ ] structural parent sets derived
[ ] runtime-owned shared namespace identified
[ ] addon prerequisites selected
[ ] installed ownership unit selected
[ ] directory uninstall rule selected
[ ] archive-envelope versus installed-payload license rule selected
[ ] candidate envelope root and payload root selected
[ ] ownership model independently verified
[ ] canonical source mutation control passes
[ ] claim boundary recorded
```

## Non-goals

```text
creating the final tar archive
choosing gzip, zstd or other compression
normalizing archive timestamps or uid/gid
claiming byte-identical reproducibility
implementing installation transactions
implementing upgrade or rollback
adding unsupported GUI source
changing the frozen component partition
```

## Result archive convention

```sh
RESULTS="$PWD/results/termux/stage3c-phase2-archive-ownership-model"
ARCHIVE="$HOME/Downloads/stage3c-phase2-archive-ownership-model-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A Phase 2 ownership PASS will prove that the frozen components can be represented by disjoint exact payload ownership plus explicit shared structural namespace requirements.

It will not yet prove an archive is reproducible, safely extractable under hostile input, transactionally installable, upgradeable, or uninstallable.
