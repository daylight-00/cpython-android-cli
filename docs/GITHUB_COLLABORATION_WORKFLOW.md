# Git, Termux, Drive, and Assistant Collaboration Workflow

> **Status:** Active project workflow
> **Repository:** `daylight-00/cpython-android-cli`
> **Default branch:** `main`
> **Canonical device checkout:** `$HOME/projects/cpython-android-cli`
> **Compatibility note:** this historical filename is retained so existing links remain valid.
> **Canonical cross-session rules:** [`session-operations/README.md`](session-operations/README.md).
> This file remains a detailed compatibility reference; stable session mechanics are maintained in `docs/session-operations/`.

## Purpose

This document defines how the project owner, the real Termux target, local Git work, Google Drive transport, and the assistant environment collaborate.

```text
Git repository
  source, scripts, documentation, experiment history, and commit topology

Termux device
  authoritative Android execution and target-generated evidence

assistant environment
  repository reconstruction, design, implementation, audit, and package preparation

Google Drive
  connector-visible transport for bounded archives and repository packages
```

No layer substitutes for another.

## Authority order

For architecture and project state:

```text
1. current canonical Git history and default-branch content
2. current context, scope, handoff, and evidence documents
3. frozen machine-readable contracts and exact identities
4. experiment recipes and source analysis
5. chat transcript as temporary coordination context
```

For target behavior:

```text
complete independently inspected Termux evidence
  > local reconstruction
  > static assumptions
```

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3F.md
  -> docs/stages/STAGE3F_SCOPE.md
  -> experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json
  -> experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md
  -> experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json
  -> experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json
  -> docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md
  -> docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md
  -> docs/handoff/2026-07-16-stage3f-gate4-retention-correction-acceptance.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/evidence/STAGE3E_FINAL_SUMMARY.md
  -> docs/handoff/COLLABORATION_PROTOCOL.md
```

Do not reconstruct current state from chat memory alone.

## Roles

The project owner:

```text
operates the authoritative Termux target
makes final scope and policy decisions
runs bounded wrappers
transports complete archives through rclone
```

The assistant:

```text
inspects and reconstructs the repository
implements narrow changes
creates commits, patches, or bundles as appropriate
builds one-shot wrappers and machine verifiers
publishes connector-visible packages
retrieves and independently audits target archives
keeps claim boundaries explicit
```

The owner should perform the minimum manual work needed to bridge the real device and the connector.

## Git execution model

The assistant works from a real local Git repository or an exact bundle reconstruction. GitHub connector operations are not the default project workflow.

Use normal Git object and ref semantics:

```text
commit/tree identity checks
clean-working-tree preconditions
explicit parent topology
bounded branches
git bundle verify
git fsck
atomic or force-with-lease push only when topology requires it
```

Do not rewrite or force-update history without an exact backup bundle, old-to-new maps, remote precondition checks, and rollback behavior.

## Authorship policy

Future project commits use one identity for both author and committer:

```text
daylight-00 <hwjang00@snu.ac.kr>
```

Set both global and repository-local configuration when a wrapper establishes the working environment.

Historical policy:

```text
existing user identities                 preserve
existing GitHub committers/signatures    preserve
OpenAI/Codex/agent metadata              correct only when explicitly requested
```

When correction is required, modify only the commits and metadata fields actually affected by non-user identities. Preserve trees, messages, parent topology, timestamps, timezones, unaffected commit OIDs, and unaffected signatures whenever topology permits.

## Choosing patch, partial bundle, or full bundle

The assistant chooses the smallest transport that safely represents the intended change.

```text
patch
  narrow linear source/docs change on an exact expected base

partial bundle
  selected commits or refs where topology matters

full bundle
  complete repository reconstruction, history rewrite, broad ref movement,
  or exact backup/rollback authority
```

Commit and push timing is deliberately flexible. It depends on gate risk, target validation needs, and ref topology rather than a fixed PR ritual.

## Drive exchange rule

For ordinary assistant/user file exchange, minimize connector calls and preserve an archive record by using one `.tar.zst` per direction whenever practical.

Agent-to-user archive normally contains:

```text
patch or bundle
manifest and SHA-256 inventory
verification contracts and maps
one APPLY_AND_RUN.sh wrapper
rollback or backup material when needed
```

User-to-agent archive normally contains:

```text
complete stdout/stderr
raw return codes
applied HEAD and tree
machine-readable summaries
result indexes and safety reports
all bounded scenario evidence
```

Historical `.tgz` authorities remain immutable. Do not recompress or rename them as replacement evidence. New archives use `.tar.zst`.

## Standard bounded workflow

```text
1. read current context, scope, handoff, and frozen identities
2. choose one narrow repository or target claim
3. reconstruct the exact expected base
4. implement code and low-level English documentation
5. run local/static and repository regression checks
6. package one bounded .tar.zst with one wrapper
7. user downloads with rclone and runs the wrapper once
8. wrapper preserves PASS or FAIL evidence and uploads one result .tar.zst
9. assistant retrieves and independently audits the archive
10. accept/freeze or issue the smallest correction
11. commit/push/main integration at the safest point for that gate
12. open only the next smallest authority boundary
```

A failed target run is evidence. Never overwrite or hide it.

## Wrapper requirements

A wrapper should, where applicable:

```text
verify package SHA-256 identities
verify expected repository HEAD and tree
require a clean worktree
set the approved Git identity
create a bounded backup/ref map before mutation
apply the patch or import the bundle
verify the resulting tree and refs
run repository regressions
run the target workflow when requested
create a complete PASS-or-FAIL result archive
write an exact root result-index
upload archive/checksum/status through rclone
print one final status block
```

Mutation must stop before application or push when a precondition differs.

## Push discipline

Push behavior is selected by topology:

```text
new branch
  normal push, preferably atomic when multiple refs move

fast-forward integration
  ordinary fast-forward push

history correction
  exact leases, atomic update when supported, backup bundle, rollback plan
```

Never claim CI passed when no registered CI status exists. Repository-local validation and target evidence must be named precisely.

## Target evidence acceptance

Every accepted target archive is independently inspected for:

```text
archive SHA-256 and byte size
valid compression and single safe root
no absolute or parent-traversal paths
no unexpected links, special entries, or duplicate members
exact result-index membership, type, mode, size, and SHA-256
canonical JSON/JSONL where claimed
raw process-record/output consistency
all return codes and failed-check arrays
input fingerprints before and after
exact archive, manifest, source, product-lock, and contract identities
independent reconstruction of the most important semantic checks
```

A console marker alone is never acceptance.

## Tracked versus generated state

```text
tracked in Git
  source, scripts, docs, small machine contracts, selected evidence conclusions

generated and ignored
  runtime trees, bulk results, target scratch roots, caches, packaged products

transported through Drive
  bounded repository packages and complete evidence archives
```

Workstation/device build-product synchronization may still use the tracked `scripts/sync/` rsync workflows. That is distinct from assistant/user Drive exchange.

## Sandbox boundary

Assistant-local paths such as `/mnt/data` are temporary working material, not repository truth. They become project state only after deliberate commit or inclusion in a verified transport package.

Do not infer a repository commit from a sandbox file, and do not invent a sandbox link for a file that exists only in Drive or Git.

## Claim discipline

Every gate states both what is proved and what remains unproved.

Never promote:

```text
process exit into power-loss durability
trace order into physical persistence
source inventory into runtime integration
archive extraction into installation correctness
installation correctness into installed-runtime behavior
design verification into target acceptance
```

The real Termux target and independent archive audit remain mandatory for target claims.
