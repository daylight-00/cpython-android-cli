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
5. Read the package's dated project-state snapshot and perform only its immediate bounded task.

## Stable repository documents

- [`PROJECT_ORIENTATION.md`](PROJECT_ORIENTATION.md)
- [`session-operations/README.md`](session-operations/README.md)
- [`session-operations/COLLABORATION_AND_TRANSPORT.md`](session-operations/COLLABORATION_AND_TRANSPORT.md)
- [`session-operations/AGENT_WORK_METHOD.md`](session-operations/AGENT_WORK_METHOD.md)
- [`session-operations/SESSION_CYCLE.md`](session-operations/SESSION_CYCLE.md)
- [`session-operations/SESSION_CLOSE_INITIALIZATION.md`](session-operations/SESSION_CLOSE_INITIALIZATION.md)
- [`session-operations/HANDOFF_PACKAGE_SPEC.md`](session-operations/HANDOFF_PACKAGE_SPEC.md)
- [`session-operations/LESSONS_AND_CHANGELOG.md`](session-operations/LESSONS_AND_CHANGELOG.md)

These files describe collaboration and session mechanics. They are not project-stage authority.

## Project authority

The dated handoff selects the minimum project reading path. Do not infer current status from an older handoff, chat memory, a console marker, a file name, or an uninspected result archive.
