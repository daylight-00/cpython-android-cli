# Agent Work Method

## Scope first

For each unit, state the exact input authority, one bounded claim, proved/not-proved boundaries, expected mutations, and success/fail-closed outputs. Separate product defects, host adaptations, probe defects, and control-wrapper defects.

## Implementation

1. Resolve branch, HEAD, tree, remote active ref, and main.
2. Read only the minimum relevant authority.
3. Implement in an isolated workspace.
4. Validate syntax, hashes, archive safety, patch applicability, and success/failure control paths.
5. Package one wrapper that captures return codes and still attempts final status, archive, and upload.
6. Preserve every failed attempt and make the smallest justified correction.

Wrappers resolve paths from `BASH_SOURCE`, use explicit repository paths, and isolate fallible commands from an outer `set -e`. Optional absence must return success and be recorded explicitly.

## Evidence inspection order

```text
1. Drive metadata and reported size
2. archive member table and safety
3. self-excluding result index
4. final/workflow status
5. summary JSON and command RC catalog
6. generated verifier/audit summaries
7. bounded output around first meaningful failure
8. full raw log only when bounded evidence is insufficient
```

A verifier PASS may only mean a failure archive is structurally valid. Confirm the actual stage status separately.

## Failure discipline

Record the first meaningful boundary, blocked downstream stages, and mutation controls. Distinguish real product failures from verifier/wrapper false negatives. Do not weaken a valid gate merely to obtain PASS.

## Communication and documentation

Provide short updates at meaningful boundaries. Final status includes return codes, repository identities, archive path/SHA/Drive destination, and gate state. Put stable operations in `docs/session-operations/`, changing state in dated `docs/handoff/`, and frozen results in `docs/evidence/` plus the experiment directory. Do not leave material conclusions only in chat.
