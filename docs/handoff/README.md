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
experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json
experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md
experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json
experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json
docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md
docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md
docs/handoff/2026-07-16-stage3f-gate4-retention-correction-acceptance.md
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
Stage 3-F Gate 4 Termux retained acquisition            FROZEN — 16/16, independent 31/31
Stage 3-F Gate 5 independent publication freeze          ACTIVE NEXT
```

Gate 4 v1 is preserved as a fail-closed retention-gap result. Corrected Gate 4A retains exact archive bytes, passes strict payload fidelity, completes the Termux loopback matrix, and is independently accepted. The historical Gate 2 snapshot is unselectable for acquisition; the retained Gate 4 snapshot is active.

The next action is Gate 5 independent freeze. Do not open public endpoints, uv automatic acquisition, product execution, installation, origin authentication, recovery, concurrency, durability, or third-product scope.
