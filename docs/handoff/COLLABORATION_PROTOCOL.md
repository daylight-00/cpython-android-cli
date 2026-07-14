# Collaboration Protocol for Successor Sessions

> **Compatibility notice:** canonical cross-session rules moved to [`../session-operations/README.md`](../session-operations/README.md).
> Keep this historical document for prior links and context; update stable mechanics only in `docs/session-operations/`.

> **Purpose:** preserve the exact working relationship used to advance this repository.
> **Applies to:** all successor assistant sessions working with the project owner.

## Roles

The project owner operates the authoritative Termux target and makes final scope decisions.

The assistant acts as:

```text
evidence-driven architect and implementer
auditor and claim-boundary enforcer
local Git and repository-history operator
Google Drive package publisher/retriever
pressure source against convenience-driven scope drift
```

The governing philosophy is:

```text
maximum effect from minimum conditions
```

Every dependency, mutation, package, helper, exception, and workaround must justify itself.

## Authority hierarchy

```text
1. complete Termux target evidence uploaded by the user
2. frozen repository evidence and exact identities
3. independent local reconstruction
4. static source review
5. assumptions or memory
```

Only the Termux target can close a target gate. Local validation may close repository-fact checks, not Android behavior claims.

## Standard workflow

```text
1. inspect current context, frozen scope, and exact identities
2. define one narrow claim with proved/not-proved boundaries
3. reconstruct the exact expected Git base
4. implement code and low-level English documentation
5. perform local/static and repository regression validation
6. choose patch, partial bundle, or full bundle by topology
7. package one agent-to-user .tar.zst with one wrapper
8. user downloads through rclone and runs the wrapper once
9. wrapper uploads one complete PASS-or-FAIL .tar.zst
10. assistant retrieves and independently audits the archive
11. freeze PASS evidence or preserve/document FAIL evidence
12. commit and push at the safest point for the gate
13. fast-forward the canonical branch only after validation
14. open only the next smallest authority boundary
```

Do not skip failure preservation.

## User interaction

The owner should perform the minimum manual work needed to bridge the real device and the connector. Prefer one copy command and one wrapper command.

Do not ask the owner to inspect or paste large logs. The wrapper must collect and upload the complete bounded archive.

Every final status block should expose at least:

```text
workflow/archive/upload return codes
applied HEAD and tree
result archive path
result archive SHA-256 when available
uploaded Drive destination
push status when applicable
```

## Drive and archive policy

Ordinary assistant/user exchange should use one `.tar.zst` per direction whenever practical.

```text
agent -> user
  patch/bundle + manifest + verifier + wrapper + rollback authority

user -> agent
  complete execution/evidence result tree
```

Historical `.tgz` evidence is immutable accepted authority. New archives and ordinary exchange packages use `.tar.zst`.

## Patch and bundle selection

```text
patch
  narrow linear change on an exact base

partial bundle
  selected commit/ref topology is material

full bundle
  history rewrite, exact reconstruction, broad ref capture, or backup/rollback
```

The assistant decides commit and push timing flexibly from risk and topology. A fixed PR/squash ritual is not required.

## Git authorship and history policy

Future author and committer:

```text
daylight-00 <hwjang00@snu.ac.kr>
```

Preserve historical user identities and GitHub committers/signatures. Correct OpenAI, Codex, or agent metadata only when explicitly required, and only as surgically as commit topology permits.

History-changing work requires:

```text
original full bundle
rewritten bundle
old-to-new commit map
old-to-new ref map
unaffected-object and signature verification
remote precondition/lease checks
atomic update where possible
rollback behavior
```

## Target archive inspection

For every uploaded result archive:

```text
compute archive SHA-256 and size
validate compression and one safe root
reject absolute paths and parent traversal
reject unexpected hardlinks, symlinks, and special entries
extract into a temporary directory
read scenario, verification, workflow-status, safety, and result-index data
recompute exact result-index path/type/mode/size/SHA identities
check all raw return codes, stdout/stderr, and output references
check canonical JSON or JSONL where claimed
check immutable input fingerprints before and after
check exact source, manifest, archive, product-lock, and contract identities
reconstruct important semantic checks independently
```

Never accept a final `PASS` marker alone.

## Failure handling

A failed target run is evidence, not noise.

```text
preserve archive identity
identify the first meaningful failing boundary
separate product, host, probe, and control-design failures
verify downstream gates blocked correctly
verify immutable input remained unchanged
write a dedicated failure record when material
make the smallest correction
retain strict gates unless the gate itself was invalid
run a corrected bounded rerun
```

Do not hide or overwrite failed attempts.

## Claim discipline

Every gate must state both:

```text
proved
not proved
```

Never promote a process-exit test into power-loss durability, source inventory into runtime integration, extraction into installation correctness, or repository design into target acceptance.

## Documentation discipline

Repository documentation is English. User-facing explanation is normally Korean.

Preserve exact:

```text
filenames and paths
SHA-256, Git object, commit, and tree identities
check counts and return codes
entry counts and source/target paths
deferred claims and non-reopening rules
```

Do not leave major conclusions only in chat.

## Project invariants

Do not silently reopen:

```text
Stage 2 launcher/PyConfig architecture
Stage 3-A native closure and host-data boundary
Stage 3-B producer/product identities
Phase 1 component semantics
Phase 2 ownership and structural non-ownership
Phase 3 reproducible archive and safe extraction
Phase 4 transaction, recovery, locking, and durability
Gate 3B preserve-and-report policy
Gate 3C addon dependency/composition policy
Gate 3D final-uninstall ownership policy
```

Gate 4 begins with a second independently frozen product authority. It does not begin with transition implementation.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3C.md
  -> docs/stages/STAGE3C_PHASE5_SCOPE.md
  -> docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md
  -> docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md
  -> docs/GITHUB_COLLABORATION_WORKFLOW.md
```
