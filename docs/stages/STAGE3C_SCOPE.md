# Stage 3-C Scope: Distribution Archive and Installation Contract

> **Status:** ACTIVE — Phase 1 and Phase 2 frozen, Phase 3 archive serialization active
> **Input:** frozen Stage 3-B promoted product and frozen Stage 3-C component/manifest contracts
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Stage question

> What archive layout and installation contract allow downstream users or tools to inspect, verify, stage, install, upgrade, uninstall, and relocate the runtime without project-specific knowledge?

## Design principle

```text
freeze product semantics
then freeze ownership and manifests
then serialize archives
then design installation transactions
```

Stage 3-C does not choose a tar command first and infer product semantics afterward.

## Non-reopening rule

Packaging must preserve or explicitly revalidate:

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

Component ownership and schema-v1 identities must not be changed merely to simplify archive or installer implementation.

## Phase roadmap

```text
Phase 1  product roles, component split, isolated validation      FROZEN
Phase 2  archive ownership, shared namespace, manifest model      FROZEN
Phase 3  reproducible archive serialization                       ACTIVE
Phase 4  installation transaction prototype                       DEFERRED
Phase 5  extracted and installed target validation                DEFERRED
```

## Frozen Phase 1 boundary

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
docs/evidence/STAGE3C_PHASE1_RUNTIME_BASE_FINAL_RESULT.md
```

Canonical promoted source:

```text
entries
  3155

fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Runtime-base:

```text
entries
  714

strict fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

native closure
  81 ELF / 329 edges / unresolved 0

extension imports
  67/67

production relocation
  PASS
```

## Frozen Phase 2 boundary

```text
docs/stages/STAGE3C_PHASE2_FINAL.md
docs/evidence/STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_RESULT.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA_RESULT.md
```

Exact selected ownership:

```text
runtime-base          714
development-addon     454
test-addon           1788
selected total       2956
unsupported GUI       199 excluded
exact owned overlap     0
```

Shared structural namespace:

```text
lib
lib/python3.14
```

Frozen manifest identities:

```text
manifest index
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

runtime-base
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

development-addon
  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a

test-addon
  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

## Active Phase 3 question

> Can each frozen schema-v1 artifact be serialized twice to byte-identical normalized tar.gz archives and independently verified through safe staging extraction?

Detailed scope:

```text
docs/stages/STAGE3C_PHASE3_SCOPE.md
```

Implementation:

```text
experiments/stage3c-reproducible-archives/
```

Candidate serialization contract:

```text
format                     POSIX pax tar + gzip
gzip level                 9
gzip filename              empty
gzip mtime                 0
tar member mtime           0
uid/gid                    0/0
uname/gname                empty
envelope directory mode    0755
metadata file mode         0644
payload mode               exact manifest mode
hardlinks                  forbidden
special entries            forbidden
PAX headers                path/linkpath only when required
```

Required Phase 3 validation:

```text
accepted Phase 2 hashes exact
source paths match manifests before serialization
three archives generated twice
build A/B byte-identical SHA-256 and size
exact gzip header
exact tar member order and set
normalized owner/time/mode metadata
metadata bytes exact
regular payload hashes exact
symlink targets exact
unsafe paths and entry types zero
safe staging extraction
extracted metadata and payload identity
source mutation controls
```

## Phase 4: installation transactions

After Phase 3 freezes archive bytes and safe staging extraction, Phase 4 defines:

```text
installed ownership registry
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

The installer must never delete an unowned file merely because it is under a shared parent directory.

## Phase 5: runtime and lifecycle validation

Required extracted-runtime matrix:

```text
stage at A
manifest and payload verification
runtime smoke and native closure at A
fresh uv venv and uv run at A
move complete payload A -> B
runtime smoke and native closure at B
fresh uv venv and uv run at B
stale A-prefix assertions
portable source/B fidelity
```

Required installed-lifecycle matrix:

```text
fresh install
installed ownership/hash verification
same-version reinstall
upgrade
failed-upgrade rollback
uninstall exact owned paths only
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

Generated archives and bulk target evidence remain outside Git and are uploaded as stage-qualified TGZ bundles.

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

Build the three frozen artifacts twice with normalized pax tar/gzip metadata, retain build A, independently verify every member, and safely extract into staging without claiming installation semantics.
