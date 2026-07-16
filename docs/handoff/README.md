# Successor Session Handoff

Read in order:

```text
README.md
docs/PROJECT_CONTEXT_STAGE3F.md
docs/stages/STAGE3F_SCOPE.md
experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md
experiments/stage3f-publication-acquisition/gate1-authority.json
docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md
experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md
experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json
experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json
docs/evidence/STAGE3F_GATE2_REPOSITORY_TRANSACTION_RESULT.md
experiments/stage3f-publication-acquisition/GATE3_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION.md
experiments/stage3f-publication-acquisition/loopback_acquisition.py
experiments/stage3f-publication-acquisition/verify-gate3-loopback-acquisition.py
experiments/stage3f-publication-acquisition/gate3-loopback-acquisition-authority.json
docs/evidence/STAGE3F_GATE3_LOOPBACK_TRANSPORT_ACQUISITION_RESULT.md
docs/handoff/2026-07-16-stage3f-gate3-loopback-freeze.md
docs/PROJECT_CONTEXT_STAGE3E.md
docs/evidence/STAGE3E_FINAL_SUMMARY.md
docs/PROJECT_CONTEXT_STAGE3D.md
docs/handoff/STAGE3D_EVIDENCE_LEDGER.md
docs/handoff/COLLABORATION_PROTOCOL.md
```

```text
Gate 4 cross-version transition                         FROZEN — 66/66
Stage 3-D Gate 6 bounded managed-Python feasibility     FROZEN — A/B/C accepted
Stage 3-E Gate 1 distribution authority design          FROZEN
Stage 3-E Gate 2 isolated dual-version boundary census  FROZEN — external re-audit 117/117
Stage 3-E Gate 3 managed-Python distribution contract   FROZEN
Stage 3-E Gate 4 persistent-root target validation      FROZEN — 37/37, independent 74/74
Stage 3-E Gate 5 independent distribution freeze        FROZEN
Stage 3-F Gate 1 publication/acquisition authority      FROZEN — repository-only design
Stage 3-F Gate 2 immutable publication snapshot         FROZEN — 18/18 local verification
Stage 3-F Gate 3 loopback transport/acquisition         FROZEN — 31/31 local verification
Stage 3-F Gate 4 Termux target acquisition              ACTIVE NEXT
```

Gate 3 freezes implementation behavior using synthetic artifacts and isolated cache roots only. The next action is a bounded Termux loopback matrix using the actual frozen CPython archive bytes.

Do not use public endpoints, invoke uv, execute products, install archives, or mutate the Stage 3-E managed root in Gate 4. Preserve complete PASS-or-FAIL evidence and independently audit the target archive before acceptance.
