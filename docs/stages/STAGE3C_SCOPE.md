# Stage 3-C Scope: Distribution Archive and Installation Contract

> **Status:** ACTIVE — Phase 1 frozen, Phase 2 ownership/manifest model active
> **Input:** frozen Stage 3-B promoted product and frozen Stage 3-C Phase 1 component split
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Stage question

> What archive layout and installation contract allow downstream users or tools to inspect, verify, stage, install, upgrade, uninstall, and relocate the runtime without project-specific knowledge?

## Design principle

```text
freeze the contract
before
optimizing the archive or installer
```

Stage 3-C does not choose a tar command first and infer product semantics afterward.

## Non-reopening rule

Packaging must consume frozen producer and runtime semantics. It must preserve or explicitly revalidate:

```text
R2 conditional self re-exec
B0 PyConfig auto-discovery
runtime and subprocess identity
native closure
67-extension surface
CA integration policy
timezone data boundary
uv explicit-interpreter workflow
venv prefix/base_prefix identity
whole-prefix relocatability
stale-prefix absence
product path/content/symlink fidelity
```

Component ownership frozen in Phase 1 must not be changed merely to simplify archive construction.

## Phase roadmap

```text
Phase 1  product roles, component split, isolated validation      FROZEN
Phase 2  archive ownership, shared namespace, manifest model      ACTIVE
Phase 3  reproducible archive prototype                           DEFERRED
Phase 4  installation transaction prototype                       DEFERRED
Phase 5  extracted and installed target validation                DEFERRED
```

The Phase 1 boundary is authoritative:

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
docs/evidence/STAGE3C_PHASE1_RUNTIME_BASE_FINAL_RESULT.md
```

## Frozen Phase 1 result

Canonical promoted source:

```text
entries       3155
ELF             81
symlinks         5
fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Frozen selected artifacts:

```text
runtime-base
  714 entries
  38,759,749 regular-file bytes
  strict fingerprint
    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

development-addon
  454 component-owned entries
  4,973,375 regular-file bytes

test-addon
  1788 component-owned entries
  33,476,790 regular-file bytes

unsupported-gui-source
  199 entries
  not distributed
```

```text
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

Runtime-base validation:

```text
native closure                  81 ELF / 329 edges / unresolved 0
Android-system SONAME dlopen    5/5
extension imports               67/67
production relocation           A -> B PASS
source/B entries                714 / 714
portable added/removed/changed  0 / 0 / 0
portable fingerprint
  5e3a46e454163b35f1c3bca6c381253fe0e025695f67fe874deedea006034fab
```

## Phase 2 question

> How can the three frozen distributable components be represented as independently inspectable artifacts and safely composed under one installation prefix while preserving exact payload ownership and shared directory structure?

Detailed scope:

```text
docs/stages/STAGE3C_PHASE2_SCOPE.md
```

## Phase 2 contract dimensions

### 1. Exact payload ownership

For every artifact, derive and freeze:

```text
owned relative paths
owned regular files
owned directories
owned symlinks
owned ELF objects
```

Required invariant:

```text
exact owned path overlap = 0
```

### 2. Shared structural namespace

Archive structure may require parent directories that another artifact owns or that several addons share.

The model must distinguish:

```text
OWNED_PAYLOAD
STRUCTURAL_PARENT
```

A structural directory is not recursive ownership of every descendant.

### 3. Archive envelope and prefix model

Candidate staging shape:

```text
<artifact-id>/
  metadata/
  payload/
```

The contract must define:

```text
archive root name
payload root
prefix-relative paths
whether extraction is staging or installation
addon overlay target
entry-point naming
symlink policy
forbidden path and entry types
```

### 4. Machine-readable manifest

Minimum candidate fields:

```text
schema version
artifact and component identity
product/Python/ABI/API identity
source and component-manifest identity
entry class
relative path
entry type
mode
regular-file size and SHA-256
symlink target
ELF marker
license mapping
addon prerequisite
```

Directory `st_size` is not product identity.

### 5. License boundary

The installed canonical license path is runtime-base-owned.

Independently redistributed addons must remain understandable without duplicating installed-path ownership. Candidate solution:

```text
runtime-base owns the in-prefix license row
all distributable archives embed license mapping/text in metadata/
```

### 6. Addon prerequisites

Development and test addons are overlays, not standalone Python distributions. They must require a matching:

```text
product identity
Python version
target ABI/API
component-manifest identity
runtime-base installation
```

### 7. Ownership and uninstall direction

Candidate ownership unit:

```text
exact manifest path
```

Candidate directory rule:

```text
remove owned files and symlinks
remove a directory only when empty
never recursively delete a shared structural parent
preserve unowned sentinel files
```

Collision, reinstall, upgrade, rollback, and registry transactions remain Phase 4 questions, but Phase 2 must provide sufficient ownership data for them.

## Phase 3: reproducible archive prototype

After Phase 2 freezes payload and manifest semantics, Phase 3 selects and validates:

```text
byte-identical archive or normalized manifest-identical archive
path ordering
timestamp and epoch source
uid/gid and owner names
file and directory modes
symlink representation
hardlink prohibition or policy
PAX/extended headers
compression algorithm and parameters
archive/compressor identities
locale and timezone
```

Archive validation must include:

```text
archive checksum
manifest schema
archive entries equal manifest
regular-file hashes equal manifest
symlink targets equal manifest
unexpected entries = 0
path traversal and unsafe entry rejection
```

## Phase 4: installation transaction prototype

Phase 4 defines:

```text
installation registry
fresh install
pre-existing path collision
same-version reinstall
upgrade and downgrade
partial-failure rollback
interrupted-operation recovery
concurrent-operation policy
uninstall
unowned sentinel preservation
```

The installer must never delete an unowned file merely because it is under the same parent directory.

## Phase 5: extracted and installed validation

Required extracted-runtime matrix:

```text
extract/stage at A
manifest and payload verification
runtime smoke at A
native closure at A
fresh uv venv at A
uv run at A
move complete payload prefix A -> B
runtime smoke at B
native closure at B
fresh uv venv at B
uv run at B
stale A-prefix assertions
source payload versus B portable fidelity
```

Required installation matrix:

```text
fresh install
installed ownership/hash verification
same-version reinstall result
upgrade
failed-upgrade rollback
uninstall owned paths only
unowned sentinel preservation
```

## Evidence and generated layout

Tracked:

```text
docs/stages/STAGE3C_*.md
docs/evidence/STAGE3C_*.md
experiments/stage3c-*/
```

Generated:

```text
dist/
results/termux/stage3c-*/
work/termux/stage3c-*/
```

Generated archives and bulk validation output remain outside Git and are uploaded as stage-qualified TGZ evidence.

## Deferred beyond core Stage 3-C

```text
uv managed-Python provider integration
multi-ABI/API release matrix
PGO/LTO and size optimization
release signing
SBOM standard selection
publication infrastructure
published provenance attestations
```

## Current action

Derive exact archive ownership and structural-parent requirements from the frozen Phase 1 component inventory before creating any archive bytes.
