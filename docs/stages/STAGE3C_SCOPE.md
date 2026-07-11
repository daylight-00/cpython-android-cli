# Stage 3-C Scope: Distribution Archive and Installation Contract

> **Status:** ACTIVE — contract design
> **Input:** frozen Stage 3-B promoted product and target-equivalence model
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Question

> What archive layout and installation contract allow downstream users or tools to inspect, verify, install, upgrade, uninstall, and relocate the runtime without project-specific knowledge?

## Entry conditions

Stage 3-C begins only because Stage 3-B is frozen.

The input model already proves:

```text
producer source/toolchain/dependency inputs are explicit
promoted dependency and CPython products exist
promoted runtime assembly succeeds on Termux
canonical runtime behavior passes
native closure has zero unresolved edges
67/67 tested extension imports pass
CA and timezone-data boundaries are explicit
whole-prefix relocation passes
candidate/frozen controls remain unchanged
relocated source/B product fidelity passes
```

Authoritative input:

```text
docs/stages/STAGE3B_FINAL.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## Design principle

```text
freeze the contract
before
optimizing the archive or installer
```

Stage 3-C must not choose a tar command first and infer the contract afterward.

## Non-reopening rule

Packaging must not silently reopen frozen producer or runtime semantics.

Any archive or installation transformation must preserve or explicitly revalidate:

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

## Phase proposal

```text
Phase 1  archive and installation requirements       ACTIVE
Phase 2  payload and manifest model                  DEFERRED
Phase 3  reproducible archive prototype              DEFERRED
Phase 4  installation transaction prototype          DEFERRED
Phase 5  extracted/installed target validation        DEFERRED
```

The phase split is provisional until Phase 1 freezes the requirements.

## Phase 1 question

> What exact consumer-facing guarantees must the distribution product provide, and which generated files belong to the runtime, development, metadata, license, and optional-debug roles?

## Contract dimensions

### 1. Payload boundary

Select and justify one of:

```text
single combined archive
runtime archive + development archive
runtime archive + development archive + debug archive
```

Candidate runtime role:

```text
launcher and interpreter entry points
stdlib
extension modules
runtime-internal native libraries
required runtime data
runtime manifest
license references or license payload
```

Candidate development role:

```text
headers
libpython development files
sysconfig development metadata
link information
pkg-config or equivalent metadata, if selected
```

Candidate optional-debug role:

```text
unstripped objects
symbols
source maps or build-id indexes, if produced
```

No role split is accepted until complete path ownership is machine-checked.

### 2. Archive root and install-prefix model

Define:

```text
archive root name
whether payload is prefix-relative
allowed final installation prefixes
whether extraction itself is installation
whether a staging root is supported
ownership of parent directories
symlink policy
entry-point naming policy
```

The contract must preserve whole-prefix relocation rather than hard-code one final absolute installation path.

### 3. Ownership and transaction semantics

Define:

```text
owned relative path set
pre-existing path collision policy
fresh-install behavior
same-version reinstall behavior
upgrade behavior
downgrade behavior
uninstall behavior
partial-failure rollback
interrupted-operation recovery
concurrent-operation policy
```

The installer must not delete unowned files merely because they reside under the same parent directory.

### 4. Machine-readable manifest

The manifest must be versioned and sufficient for independent verification.

Minimum candidate fields:

```text
schema version
product name and runtime version
source revision identity
SDK/NDK/API/target identity
dependency identities and source hashes
build profile and command-model identity
payload role for every path
entry type
mode
regular-file size and SHA-256
symlink target
license mapping
archive-level checksum references
```

Directory `st_size` must not be treated as product identity.

### 5. Reproducibility contract

Select one primary definition:

```text
byte-identical archive
or
manifest-identical payload with normalized archive metadata
```

The decision must explicitly define:

```text
path ordering
timestamps and epoch source
uid/gid and owner names
file and directory modes
symlink representation
hardlink policy
PAX or other extended headers
compression algorithm and parameters
archive/compressor tool identities
locale and timezone
```

If byte-identical archives are not initially required, payload identity must still be independently verifiable from the manifest.

### 6. Provenance and license boundary

Define which evidence is embedded in the deliverable versus retained externally.

Candidate embedded material:

```text
concise build/provenance manifest
dependency inventory
source archive hashes
license texts and notices
validation contract version
```

Candidate external material:

```text
full build logs
large inventories
complete experiment evidence
CI or workstation diagnostics
```

The archive must remain independently understandable without embedding the entire repository history.

### 7. Validation matrix

Required archive validation:

```text
archive checksum verification -> PASS
manifest schema validation -> PASS
archive entries equal manifest entries -> PASS
regular-file hashes equal manifest -> PASS
symlink targets equal manifest -> PASS
forbidden unexpected entries -> 0
```

Required extracted-runtime validation:

```text
extract at A -> canonical smoke PASS
native closure at A -> PASS
fresh uv venv at A -> PASS
uv run at A -> PASS
move complete extracted prefix A -> B
canonical smoke at B -> PASS
native closure at B -> PASS
fresh uv venv at B -> PASS
uv run at B -> PASS
stale A-prefix assertions -> PASS
source payload versus B portable fidelity -> PASS
```

Required installation validation:

```text
fresh install -> PASS
verify installed ownership and hashes -> PASS
same-version reinstall -> defined result
upgrade -> PASS
failed upgrade rollback -> PASS
uninstall -> only owned paths removed
post-uninstall unowned sentinel files preserved -> PASS
```

## Evidence and output layout

Proposed tracked paths:

```text
docs/stages/STAGE3C_SCOPE.md
docs/evidence/STAGE3C_PHASE1_*.md
experiments/stage3c-*/
```

Proposed generated paths:

```text
dist/
results/termux/stage3c-*/
work/termux/stage3c-*/
```

Generated archives and bulk validation output remain outside Git.

## Phase 1 acceptance conditions

```text
[ ] consumer personas and operations defined
[ ] runtime/development/debug role decision selected
[ ] complete path-role classification method defined
[ ] archive root and prefix-relative layout selected
[ ] install ownership rules selected
[ ] collision/upgrade/uninstall semantics selected
[ ] manifest schema v1 drafted
[ ] reproducibility definition selected
[ ] timestamp/uid/gid/mode/symlink normalization defined
[ ] provenance and license embedding boundary selected
[ ] archive validation matrix selected
[ ] extracted relocation validation matrix selected
[ ] installation transaction validation matrix selected
[ ] non-goals recorded
```

## Non-goals for Phase 1

```text
building a final release archive
writing a production installer
uv managed-Python provider integration
multi-ABI/API release matrix
PGO/LTO or size optimization
release signing
SBOM standard selection
publication infrastructure
```

These may become later Stage 3-C or Stage 3-D questions after the core distribution contract is frozen.

## First action

Inventory the promoted product by semantic role without modifying it.

The first experiment should produce a complete candidate classification:

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

The first hard gate is:

```text
UNKNOWN=0
```

Only after every promoted path has an explicit role should the project select the archive split and manifest schema.
