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

- [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md)
- [`INDEX.md`](INDEX.md)
- [`PROJECT_ORIENTATION.md`](PROJECT_ORIENTATION.md)
- [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
- [`roadmap/EPOCH2_ROADMAP.md`](roadmap/EPOCH2_ROADMAP.md)
- [`session-operations/README.md`](session-operations/README.md)
- [`documentation/DOCUMENT_LIFECYCLE.md`](documentation/DOCUMENT_LIFECYCLE.md): document lifecycle, authority domains, registry rules, and migration phases.
- [`documentation/document-registry.json`](documentation/document-registry.json): complete machine-readable Markdown/JSON lifecycle registry.
- [`session-operations/COLLABORATION_AND_TRANSPORT.md`](session-operations/COLLABORATION_AND_TRANSPORT.md)
- [`session-operations/AGENT_WORK_METHOD.md`](session-operations/AGENT_WORK_METHOD.md)
- [`session-operations/SESSION_CYCLE.md`](session-operations/SESSION_CYCLE.md)
- [`session-operations/SESSION_CLOSE_INITIALIZATION.md`](session-operations/SESSION_CLOSE_INITIALIZATION.md)
- [`session-operations/HANDOFF_PACKAGE_SPEC.md`](session-operations/HANDOFF_PACKAGE_SPEC.md)
- [`session-operations/LESSONS_AND_CHANGELOG.md`](session-operations/LESSONS_AND_CHANGELOG.md)

The epoch, orientation, and roadmap files describe current project direction. The `session-operations/` files describe collaboration mechanics and are not runtime or target authority.

## Project authority

`CURRENT_CONTEXT.md` identifies the active epoch and predecessor authority. The dated handoff selects the minimum immediate task and exact repository topology. Do not infer current status from an older handoff, chat memory, a console marker, a file name, or an uninspected result archive.
