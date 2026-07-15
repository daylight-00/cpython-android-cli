# CPython Android CLI + uv: Current Stage 3-C Project Context

> **Status:** HISTORICAL FROZEN SNAPSHOT — superseded by `PROJECT_CONTEXT_STAGE3D.md`
> **Frozen boundary:** Stage 2, Stage 3-A, Stage 3-B, and Stage 3-C Phase 5 through Gate 4E
> **Active boundary:** historical Gate 4 freeze; current work moved to Stage 3-D
> **Primary target:** Termux on Android arm64 (`aarch64-linux-android`)
> **Host build environment:** Frozen first product: separate Linux workstation; Gate 4A second product: accepted Termux-native producer exception
> **First-product baseline:** CPython 3.14.6

## 1. Project identity

This project is:

> **A CLI adaptation of an upstream CPython Android build for Termux, with uv integration and an evidence-driven distribution lifecycle.**

It preserves and studies:

```text
normal CPython CLI semantics
native stdlib imports and native closure
HTTPS trust and host-data boundaries
subprocess behavior
virtual environments
uv explicit-interpreter workflows
whole-prefix relocation
reproducible three-artifact packaging
transactional installation, recovery, repair, and uninstall
```

It is not a new general-purpose Python distribution, a Termux Python replacement, a uv-managed provider, a CPython fork, or an Android clone of `python-build-standalone`.

## 2. Governing method

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Keep these domains separate:

```text
CLI and initialization semantics
native loader behavior
Python path discovery
host CA and timezone-data integration
source/build provenance
archive and product identity
installation ownership and dependencies
transaction and recovery behavior
consumer integration
```

A success in one domain is never promoted into a claim about another domain without explicit evidence.

## 3. Authority hierarchy

```text
1. complete independently inspected Termux target evidence
2. frozen repository contracts and exact identities
3. independent local reconstruction
4. static source analysis
5. assumptions or chat memory
```

Console `PASS` output alone cannot close a target gate. Accepted target evidence requires a complete archive, safe members, exact indexes, raw process evidence, and independent semantic inspection.

## 4. Current stage map

```text
Stage 1-A  explicit runtime baseline                    FROZEN
Stage 1-B  PyConfig frontend comparison                 FROZEN
Stage 2    native bootstrap/workflow architecture       FROZEN
Stage 3-A  runtime closure and host-data boundaries     FROZEN
Stage 3-B  reproducible producer/product promotion      FROZEN
Stage 3-C  archive/install/recovery/ownership contract  FROZEN through Gate 3D
Gate 4A    second-product authority acquisition         FROZEN — A1-A6 complete
Gate 4B    cross-version transition contract            DESIGN FROZEN — 66 scenarios
Gate 4C    transition coordinator implementation        IMPLEMENTED — 69/69
Gate 4D    bidirectional Termux target validation       ACCEPTED — 66/66
Gate 4E    independent transition freeze                FROZEN PASS
Stage 3-D  consumer integration                         DEFERRED
```

## 5. Frozen runtime architecture

```text
R2 conditional self re-exec
        +
B0 PyConfig auto-discovery frontend
```

The launcher resolves its actual executable, derives the real prefix and library directory, normalizes loader state, preserves or discovers the CA bundle, re-execs only when required, and then enters normal PyConfig auto-discovery.

Frozen invariants include:

```text
normal CPython argv/exit behavior
no redundant ready-process re-exec
actual-executable self-location
component-exact loader-path normalization
automatic Python path discovery
separate CA repair policy
correct venv prefix/base_prefix identity
uv explicit-interpreter support
whole-prefix relocation
```

Gate 4 must consume this architecture; it is not a launcher redesign gate.

## 6. Frozen first-product model

The complete installed product contains three independently owned artifacts:

```text
runtime-base
development-addon
test-addon
```

Dependency rules:

```text
development-addon -> exact runtime-base
test-addon        -> exact runtime-base
no inter-addon dependency
runtime-base removal rejected while either addon remains
```

Product identity is not a version string. It includes exact archives, manifests, product lock, manifest index, ownership contract, source/build provenance, native closure, runtime behavior, and SHA-256 identities.

## 7. Frozen lifecycle and ownership rules

```text
exact-owned file or symlink
  remove or repair according to the active operation

modified-owned file or symlink during uninstall
  preserve-and-report, then deregister

unowned descendant
  preserve

owned directory
  remove only when empty

structural parent
  preserve as namespace when required
```

Do not conflate:

```text
empty registry
absence of matching owned payload
presence of approved residuals
transaction/tombstone state
physically empty prefix root
```

Gate 3D froze these as separate final-state dimensions.

## 8. Frozen transaction and recovery rules

Accepted crash boundaries:

```text
PREPARED       rc 90
late APPLYING  rc 93
COMMITTED      rc 92
```

Recovery behavior:

```text
pre-commit first recovery   -> ROLLED_BACK
pre-commit second recovery  -> NOOP_ROLLED_BACK
committed first recovery    -> FINALIZED_COMMIT
committed second recovery   -> zero transactions
```

Rollback tombstones and committed cleanup are evidence-bearing policy, not incidental implementation details.

## 9. Frozen Phase 5 authorities

### Gate 3B — preserve-and-report product acceptance

```text
archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

scenario / verifier
  29/29 / 62/62 PASS
```

### Gate 3C — addon lifecycle and dependency enforcement

```text
archive sha256
  43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a

root result-index sha256
  fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c

scenario / verifier / external audit
  50/50 / 103/103 / 27/27 PASS
```

### Gate 3D — final uninstall and ownership boundary

```text
archive sha256
  579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143

root result-index sha256
  5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60

result-tree-safety sha256
  47b571d79990cf6c5f1157f7784a5acfa47478b04a7c6f55185d3c4f38ab8a00

scenario / verifier / external audit
  44/44 / 138/138 / 37/37 PASS
```

### Gate 4A — second-product authority

```text
product             CPython 3.14.5 / android24 / aarch64
A4 materialization  25/25 PASS; static adjudication 26/26 PASS
A5 target evidence  10/10 candidate; 41/41 verifier; 34/34 independent audit
A6 freeze evidence  18/18 candidate; 18/18 verifier; 28/28 external audit
A6 archive sha256   4565b69e78c618f58fda59f928c086bbcf1cd02cfb28252f419e42e8cbc266aa
```

The authority freezes 2,946 disjoint owned paths across runtime-base, development-addon, and test-addon. HACL memzero uses the upstream fallback path with no secure-erasure guarantee, and bundled libmpdec is accepted for 3.14.5 only.

Historical `.tgz` evidence remains immutable. New evidence and ordinary assistant/user exchange archives use `.tar.zst`.

## 10. Active Gate 4 boundary

Gate 4 asks whether one complete frozen three-artifact product can transition to and from a second complete frozen product while preserving dependency, ownership, residual, collision, transaction, recovery, and runtime-behavior boundaries.

Gate 4A has now frozen the immediate stable predecessor as the second complete product authority:

```text
CPython version  3.14.5
upstream tag     v3.14.5
source commit    5607950ef232dad16d75c0cf53101d9649d89115
target           aarch64-linux-android / API 24
NDK              27.3.13750724
```

The exact v3.14.5 producer declares OpenSSL 3.0.20-0 rather than the first product's 3.5.7-0. This is a real source/dependency boundary, not a version-label exercise.

The acquisition sequence is:

```text
A1  selection and repository design          DESIGN FROZEN
A2  exact input and toolchain capture         FROZEN PASS
  A2a immutable remote inputs                 FROZEN PASS — 81/81 external audit
  A2b Termux-native binary toolchain          FROZEN PASS — 46/46 combined audit
A3  clean upstream Android replay             FROZEN PASS
A4  three-artifact materialization            FROZEN PASS — 26/26 adjudication
A5  standalone Termux validation              FROZEN PASS — 34/34 independent audit
A6  independent archive audit and freeze      FROZEN PASS — 28/28 external audit
```

### Frozen Gate 4B transition contract

The exact manifest comparison contains 2,958 union paths: 2,944 shared, 216 byte-identical, 2,728 requiring replacement, 12 unique to 3.14.6, 2 unique to 3.14.5, and no cross-artifact ownership transfers.

Gate 4B rejects direct cross-product artifact installation. A dedicated whole-product transition must preserve the installed artifact topology, require an exact source, preserve non-colliding unowned descendants, reject modified owned paths before mutation, replace the registry atomically without changing schema version 1, and use one recovery-compatible PREPARED/APPLYING/COMMITTED journal.

```text
Gate 4B design verifier  repository-only; no transition execution
scenario matrix           66
Gate 4C verifier          69/69 PASS
Gate 4D adjudication      66/66 PASS
Gate 4E verifier          independent archive and repository freeze PASS
```

Design authority:

```text
experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md
experiments/stage3c-gate4-transition/gate4b-transition-matrix.json
experiments/stage3c-gate4-transition/gate4b-cross-version-inventory.json
docs/evidence/STAGE3C_PHASE5_GATE4B_TRANSITION_CONTRACT_DESIGN_RESULT.md
experiments/stage3c-gate4-transition/GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION.md
docs/evidence/STAGE3C_PHASE5_GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION_RESULT.md
experiments/stage3c-gate4-transition/gate4c-transition-implementation-authority.json
```

### Accepted A2a remote-input authority

```text
result archive sha256
  e9c9ed69098017017b3cbf70e8237c040ede26d378f6530043cc5ff4e7469caf

root result-index sha256
  5d87e7727aef99b793ac8ddacf5e9d77f96701caf2377094013753edcda17fbe

external audit
  81/81 PASS
```

The original collector's 44/49 FAIL is preserved. Its five failures were caused by comparing an older lock `archive` object directly against a captured inventory that added valid safety fields. Independent audit verified every legacy identity/inventory field exactly and required the new safety fields separately. A2a is accepted without claiming A2b or any product artifact.

### Accepted A2b scoped toolchain authority

```text
asset sha256    7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7
producer commit 63b097b4db9b1d2ab445d6637eab16718f6c513b
original lld    cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b
overlay lld     eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09
combined audit  46/46 PASS
```

A repository authority decision accepts the exact preserved Android/aarch64 custom-r27d binary asset and an ephemeral `PT_TLS.p_align` overlay for the Gate 4A second-product producer. The original NDK remains unchanged. This scoped exception does not alter the frozen first-product workstation provenance or claim source-rebuild reproducibility for the custom NDK.

The frozen second-product authority contains:

```text
runtime-base archive and manifest
development-addon archive and manifest
test-addon archive and manifest
product lock and manifest index
ownership registry template
native closure and runtime behavior evidence
source/build provenance
byte-exact archive and manifest identities
```

A synthetic version label, manually edited first-product copy, or the official Python.org Android package used directly as project authority is rejected.

Gate 4B has frozen those choices as a dedicated whole-product, topology-preserving transition with exact-source preflight, zero owner transfers, transactional replace/remove/create planning, schema-1 registry replacement, and bidirectional recovery. Ordinary artifact install remains same-product only.

Gate 4C implements the frozen coordinator contract and passes 69/69 repository checks while preserving the frozen engine sources and schema-1 registry. Gate 4D accepted both directions across all four frozen topologies: 55 unaffected v1 scenarios remain authoritative, H01–H08 were rerun with corrected timezone and development-addon probes, C11–C12 were accepted by exact before/after evidence replay, and A04 was re-derived. Gate 4E freezes the resulting 66/66 authority. This does not accept a third product, schema migration, arbitrary mixed-version state, or Stage 3-D consumer integration.

## 11. Gate 4D target evidence and Gate 4E freeze

Gate 4D is accepted by two immutable target archives rather than by replacing the initial failure record.

```text
v1 full target run
  archive sha256       ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c
  result size          493427
  self-index           1223/1223 exact
  unaffected PASS      55
  classified harness false negatives  H01-H08, C11-C12, A04

v2 corrective focused retest
  archive sha256       98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2
  result size          720554
  self-index           529/529 exact
  focused happy paths  8/8 PASS
  final adjudication   66/66 PASS
  independent audit   16/16 PASS
```

The corrected timezone probe uses explicit `tzdata` through uv with an empty system TZ path. Development-addon acceptance compiles and imports a native extension against the installed target. C11 and C12 are accepted from their preserved before/after state evidence because the original expectation incorrectly required a collision path in source-only removal cases. A04 is derived only after the corrected happy and collision groups pass. Gate 4E freezes this provenance and the exact repository coordinator. The v1 FAIL archive remains part of the authority.

## 12. Repository and transport control plane

Repository source, scripts, documentation, and experiment history live in Git. Target-generated evidence is not committed wholesale.

Assistant/user exchange normally uses one `.tar.zst` per direction:

```text
agent -> user
  one .tar.zst containing patch, partial/full bundle when needed,
  manifests, verification material, and one wrapper

user -> agent
  one .tar.zst containing complete execution evidence
```

Choose transport according to topology:

```text
patch          narrow linear source change
partial bundle commit/ref topology matters but full history is unnecessary
full bundle    history rewrite, exact ref capture, or repository reconstruction
```

Commit and push timing is selected per gate. Destructive or history-changing operations require precondition checks, backups, exact ref maps, and rollback behavior.

Current authorship policy:

```text
future author and committer
  daylight-00 <hwjang00@snu.ac.kr>

historical user identities and GitHub signatures
  preserve

OpenAI/Codex/agent metadata
  correct only when explicitly required, and as surgically as topology permits
```

## 13. Non-reopening rule

Gate 4 consumes the first-product authorities as frozen inputs. It must not implicitly reopen:

```text
launcher and PyConfig architecture
archive identities
preserve-and-report ownership behavior
addon dependency policy
final-uninstall ownership policy
registry and journal semantics
accepted recovery behavior
```

A policy-changing intervention requires its own explicit authority decision and evidence gate.

## 14. Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3C.md
  -> docs/stages/STAGE3C_PHASE5_SCOPE.md
  -> docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md
  -> docs/evidence/STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL_ACCEPTANCE_RESULT.md
  -> docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md
  -> docs/GITHUB_COLLABORATION_WORKFLOW.md
  -> docs/handoff/COLLABORATION_PROTOCOL.md
```

`docs/PROJECT_CONTEXT_STAGE3.md` is retained as the historical Stage 3-A/3-B handoff snapshot.
