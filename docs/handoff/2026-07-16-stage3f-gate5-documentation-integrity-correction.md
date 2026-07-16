# Stage 3-F Gate 5 Documentation-Integrity Correction Handoff — 2026-07-16

The first Gate 5 commit `71ded3869f38ed59118435f119a35591aee29f75` is preserved but rejected as the final documentation state because fixture-derived replacements shortened six production documents. Continue from the corrective fast-forward commit, not by resetting or rewriting history.

Read `docs/evidence/STAGE3F_GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md` and `experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json` before relying on the Gate 5 record. The corrected tree must retain the full README, collaboration workflow, context, orientation, handoff, and scope documents and must pass the structural integrity verifier.

Stage 3-F remains bounded to the retained loopback acquisition authority. Broader publication, trust, uv acquisition, execution, installation, recovery, concurrency, durability, or third-product work requires a new stage.


## Correction v1 false-negative

The first documentation-correction wrapper result `69bfe223c5fb4f0dec42cf5b99ac35d346be9aaddb7438b82ce59e1d38af494a` made no repository mutation. Its only failed check treated pre-existing ignored bytecode anywhere in the working tree as newly created residue. Correction v2 captures the preflight bytecode inventory and rejects only new residue; standalone verification falls back to rejecting tracked bytecode.
