# Legacy Authority Decoupling Design

> **Lifecycle:** completed Phase 5 contract
> **Predecessor:** `d201957a11861147bdbe11b6a91bf68fb6714a4d` / `1c0c692d7763487ad2ba0d91a7f2bf04b6e0b423`

## Inputs

- the immutable 24-entry grandfathered baseline;
- the six original authority files;
- complete Git history containing every recorded document byte sequence;
- the Phase 4 stable/current/plan/history layer model.

## Acceptance conditions

1. Every baseline tuple resolves to one snapshot with the same SHA-256.
2. Every original authority still contains its exact tuple.
3. Snapshot paths are immutable, registered historical records, and never live/generated paths.
4. A live-path byte change is irrelevant to compatibility resolution.
5. A snapshot, map, baseline, or original authority mutation fails verification.
6. No new file-identity binding targets a live/generated document.
7. Phase 4 authority bytes remain frozen through a predecessor snapshot.
8. Documentation migration closes and program work resumes at E2-R1 / UT-0.

## Non-goals

No historical authority rewrite, product claim change, device execution, or bulk path relocation is authorized.
