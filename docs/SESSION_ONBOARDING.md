# Session Onboarding

This is the stable repository entry for a successor session.

## Start from the mandatory handoff package

1. Obtain the latest mandatory handoff `.tar.zst`.
2. Extract it into a new directory and run:

```bash
python3 tools/handoff_cycle.py verify .
python3 tools/handoff_cycle.py onboard .
```

3. Read `START_HERE.md` and `PROJECT_ORIENTATION.md` in the package.
4. Confirm repository branch, HEAD, tree, remote active ref, and `main` from `HANDOFF_MANIFEST.json`.
5. Read the package's dated snapshot and perform only its immediate bounded task.

<!-- BEGIN GENERATED CURRENT STATE -->
## Current reading path

> Generated from [`docs/current/STATE.json`](current/STATE.json).

1. [`docs/current/STATE.json`](current/STATE.json)
2. [`docs/CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md)
3. [`docs/navigation/README.md`](navigation/README.md)
4. [`docs/documentation/GENERATED_NAVIGATION.md`](documentation/GENERATED_NAVIGATION.md)
5. [`docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
6. [`docs/INDEX.md`](INDEX.md)

```text
immediate repository action  execute-document-lifecycle-phase4-mixed-document-correction
program gate held ready      E2-R1/UT-0 — exact official upstream control
program resume action        execute-e2-r1-ut0-exact-official-upstream-control
```
<!-- END GENERATED CURRENT STATE -->

## Stable repository documents

- [`documentation/DOCUMENT_LIFECYCLE.md`](documentation/DOCUMENT_LIFECYCLE.md)
- [`documentation/CURRENT_STATE_AUTHORITY.md`](documentation/CURRENT_STATE_AUTHORITY.md)
- [`documentation/document-registry.json`](documentation/document-registry.json)
- [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
- [`decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`](decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md)
- [`decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md`](decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md)
- [`session-operations/README.md`](session-operations/README.md)

## Authority rule

`current/STATE.json` is the sole temporal source. `CURRENT_CONTEXT.md`, `INDEX.md`, and the generated block above are renderings. The dated handoff supplies exact repository topology and execution scope for its transaction. Older handoffs, chat memory, console markers, and filenames do not override current state or frozen evidence.
