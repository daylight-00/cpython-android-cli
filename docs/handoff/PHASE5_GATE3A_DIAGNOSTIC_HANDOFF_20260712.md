# Stage 3-C Phase 5 Gate 3A Diagnostic Handoff — 2026-07-12

> **Current boundary:** authoritative Termux reinstall/repair diagnostic census pending
> **Workflow:** `experiments/stage3c-installed-runtime-lifecycle/run-gate3a-reinstall-repair-diagnostic.sh`
> **Product acceptance:** not yet open

## Frozen ancestry

```text
Phases 1–4                         FROZEN
Phase 5 Gate 1                     FROZEN 80/80
Phase 5 Gate 2                     FROZEN 46/46
```

Gate 2 accepted archive SHA-256:

```text
8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e
```

## Architecture finding

The frozen install planner classifies every mismatching registered non-directory as `repair`. The execution path then backs up the existing path using `durable_move()` before publishing the frozen member.

`durable_move()` uses `os.replace(source, destination)`. When the registered source path is absent, the expected target behavior is `FileNotFoundError`, an APPLYING journal, rollback to ROLLED_BACK, and retained transaction residue.

Previous Phase 4 evidence proved in-place byte corruption repair. It did not close missing regular or symlink repair.

## Required diagnostic classifications

```text
exact reinstall                        NOOP
regular byte corruption                supported in-place repair
regular mode corruption                supported in-place repair
symlink target corruption              supported in-place repair
regular replaced by directory          supported wrong-type repair
missing registered regular             expected unsupported
missing registered symlink             expected unsupported
```

## Authority rule

A diagnostic PASS means the observations match the source-derived matrix. It must not be written as `STAGE3C_PHASE5_GATE3A=PASS`.

If missing-leaf failure is confirmed:

```text
preserve the TGZ and dedicated evidence
freeze the diagnostic census only
do not proceed to Gate 3B
decide whether Phase 4 must be explicitly reopened for intervention
```

Any Phase 4 intervention must be separately authorized, documented, and revalidated through affected downstream gates. It cannot be hidden inside a Phase 5 validation commit.

## First action

Run the command in:

```text
experiments/stage3c-installed-runtime-lifecycle/README.md
```

Upload the complete TGZ rather than console markers alone.
