# Agent Work Method

## Scope first

For each unit, state the exact input authority, one bounded claim, proved/not-proved boundaries, expected mutations, and success/fail-closed outputs. Separate product defects, host adaptations, probe defects, and control-wrapper defects.

## Minimum sufficient validation

Classify the work before building checks:

```text
R — repository-only
    documentation, control metadata, or source changes that make no new target claim

L — local behavior
    code behavior that can be proved in the repository or an isolated local reconstruction

T — target authority
    a new Android/Termux behavior, product, installation, transition, or durability claim
```

Required evidence is proportional to the class:

```text
R  exact base and clean state
   exact changed paths and replacement identities
   syntax/diff plus the relevant repository verifier
   commit, push, remote readback, and clean post-state

L  all R checks
   focused unit or regression evidence for the changed behavior
   before/after fingerprints for the mutated authority

T  all relevant R/L checks
   one bounded PASS-or-FAIL target archive
   one independent audit of the claim-bearing evidence
```

Do not rerun, duplicate, or rearchive frozen evidence when its SHA-256, Git tree, and claim boundary are unchanged. Ordinary append-only fast-forward changes do not require a repository backup bundle; bundles are required for history rewriting, destructive ref movement, or otherwise non-reconstructible mutation.

Use one semantic verifier per authority boundary. Do not add a verifier-of-verifier unless the verifier itself changed or failed. When a harness or verifier changes, its minimum fixture set is:

```text
success
expected negative
incomplete or missing outcome
```

Discovery-sensitive tests must also account for physical working-directory ancestry and ambient virtual-environment state. Logical environment-variable isolation alone is insufficient when the tested tool walks parent directories.

## Implementation

1. Resolve branch, HEAD, tree, remote active ref, and main.
2. Read only the minimum relevant authority and assign R, L, or T.
3. Implement in an isolated workspace.
4. Run only the checks required by that class and the changed failure surface.
5. Package one wrapper that captures return codes and still attempts final status, receipt/archive creation, and upload.
6. Preserve failed attempts and make the smallest justified correction.

Wrappers resolve paths from `BASH_SOURCE`, use explicit repository paths, and isolate fallible commands from an outer `set -e`. Optional absence must return success and be recorded explicitly.

## Evidence inspection order

```text
1. Drive metadata and reported size
2. archive member table and safety, when an archive is required
3. self-excluding result index
4. final/workflow status
5. summary JSON and command RC catalog
6. the single claim-bearing verifier or audit summary
7. bounded output around the first meaningful failure
8. full raw log only when bounded evidence is insufficient
```

A verifier PASS may only mean a failure archive is structurally valid. Confirm the actual stage status separately.

## Failure discipline

Record the first meaningful boundary, blocked downstream stages, and mutation controls. Distinguish real product failures from verifier/wrapper false negatives. Stop blocked downstream validation except for receipt, rollback, and evidence preservation. Do not weaken a valid gate merely to obtain PASS.

## Communication and documentation

Provide short updates at meaningful boundaries. Final status includes return codes, repository identities, receipt/archive path and SHA-256, Drive destination, and gate state. Put stable operations in `docs/session-operations/`, changing state in dated `docs/handoff/`, and frozen results in `docs/evidence/` plus the experiment directory. Do not leave material conclusions only in chat.
