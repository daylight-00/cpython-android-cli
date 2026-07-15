# Complete Session Cycle

This is the repeatable receive-to-next-handoff lifecycle.

## Phase 1 — Receive and initialize

```text
mandatory handoff .tar.zst received
  -> verify archive and internal hashes
  -> read START_HERE and PROJECT_ORIENTATION
  -> confirm repository identities
  -> read dated project snapshot
  -> state immediate bounded task and non-claims
```

Run the included package tool before any evidence audit:

```bash
python3 tools/handoff_cycle.py verify <extracted-root>
python3 tools/handoff_cycle.py onboard <extracted-root>
python3 tools/handoff_cycle.py close-readiness <extracted-root>
```

## Phase 2 — Execute the bounded project loop

First classify the work using `AGENT_WORK_METHOD.md`:

```text
R  repository-only change
L  locally provable behavior change
T  new target-authority claim
```

Then execute only the required loop:

```text
inspect exact input
  -> implement or audit
  -> run class-required checks
  -> preserve the first meaningful PASS or FAIL receipt/evidence
  -> independently audit only claim-bearing target evidence
  -> update repository authority only when justified
  -> open only the next smallest boundary
```

Frozen evidence is reused by exact SHA-256 and Git identity. Repository-only changes do not trigger target reruns. A changed harness or verifier receives success, expected-negative, and incomplete fixtures before target use.

Never use the handoff snapshot as acceptance authority for a pending result. Fetch and inspect the exact evidence object.

## Phase 3 — Maintain documentation separation

- Update `docs/session-operations/` only for stable collaboration/tooling lessons.
- Update a dated `docs/handoff/` file for current state and next action.
- Update stage/evidence/experiment documents for actual project progress.
- Mark legacy cross-session documents as compatibility references, not competing canonical rules.

## Phase 4 — Close and regenerate

1. Freeze the closing observation without advancing unaudited claims.
2. Select the smallest output: a lightweight repository receipt for R, focused local evidence for L, or a complete target archive for T.
3. Create a backup bundle only for history rewrite, destructive ref movement, or non-reconstructible mutation.
4. Render a dated handoff from `templates/DATED_HANDOFF_TEMPLATE.md`.
5. Start `HANDOFF_MANIFEST.json` from `templates/HANDOFF_MANIFEST.example.json`.
6. Build the package according to `HANDOFF_PACKAGE_SPEC.md`.
7. Run the validator, required archive-safety checks, and a mock onboarding read.
8. Upload to a new Drive folder and perform raw-byte readback.
9. Report the external final SHA-256, size, Drive file ID, and successor's first action.

## Completion test

A session handoff is complete only when a context-free successor can answer, from the package alone:

```text
What is this project and what is it not?
What evidence is authoritative?
What is frozen and what remains open?
What exact action comes next?
What must not be inferred or reopened?
How are artifacts exchanged and audited?
How is the next handoff produced and validated?
```
