# CPython Android CLI + uv: Current Stage 3-C Project Context

> **Status:** Current handoff context
> **Frozen boundary:** Stage 2, Stage 3-A, Stage 3-B, and Stage 3-C Phase 5 through Gate 3D
> **Active boundary:** Gate 4 second-product authority acquisition — CPython 3.14.5 selected; exact input capture pending
> **Primary target:** Termux on Android arm64 (`aarch64-linux-android`)
> **Host build environment:** Separate Linux workstation
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
Gate 4A    second-product authority acquisition         ACTIVE — 3.14.5 selected, input capture pending
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

Historical `.tgz` evidence remains immutable. New evidence and ordinary assistant/user exchange archives use `.tar.zst`.

## 10. Active Gate 4 boundary

Gate 4 asks whether one complete frozen three-artifact product can transition to and from a second complete frozen product while preserving dependency, ownership, residual, collision, transaction, recovery, and runtime-behavior boundaries.

The immediate task is **not** an upgrade runner. Gate 4A has selected the immediate stable predecessor as the second-product input:

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
A2  exact input and toolchain capture         pending
A3  clean upstream Android replay             pending
A4  three-artifact materialization            pending
A5  standalone Termux validation              pending
A6  independent archive audit and freeze      pending
```

The authority must ultimately contain:

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

Only after the second authority is frozen may the repository decide:

```text
whole-product or artifact transition ordering
mixed-product compatibility policy
collision and residual policy
registry/product-lock replacement
bidirectional PREPARED/APPLYING/COMMITTED recovery
second-recovery idempotence
post-upgrade and post-downgrade runtime behavior
```

No upgrade, downgrade, compatibility, migration, or Gate 4 target claim is currently frozen.

## 11. Repository and transport control plane

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

## 12. Non-reopening rule

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

## 13. Current reading path

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
