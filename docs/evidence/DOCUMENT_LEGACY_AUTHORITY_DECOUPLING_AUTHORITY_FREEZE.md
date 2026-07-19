# Document Legacy Authority Decoupling Authority Freeze

> **Authority:** `experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json`
> **SHA-256:** `c24beeaf69bcdbbc1f73fabc7ec1195b6f0b5a416b33ad2bfa0c7f386c70f924`
> **Result:** frozen PASS

## Accepted evidence

- the original baseline contains exactly 24 grandfathered tuples;
- all 24 historical document bytes were recovered from Git history;
- all 24 bytes were materialized as immutable compatibility snapshots;
- every snapshot digest equals the authority-recorded digest;
- all six original authority files and their tuple values remain unchanged;
- live and generated document paths no longer carry historical digest semantics;
- future live/generated file-identity bindings remain forbidden;
- the Phase 4 documentation layer authority is preserved without recursive replay;
- bulk physical document relocation is not required.

## Claim boundary

This freeze changes documentation authority interpretation only. It does not change product bytes, experimental evidence, selection, publication, emulator qualification, or the accepted dual-real-device compatibility claim.

The documentation lifecycle migration is complete. Active work returns to E2-R1 / UT-0 exact official upstream control.
