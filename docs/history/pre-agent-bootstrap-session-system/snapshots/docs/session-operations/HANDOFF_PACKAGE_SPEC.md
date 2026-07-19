# Mandatory Handoff Package Specification

## Required root files

```text
START_HERE.md
PROJECT_ORIENTATION.md
HANDOFF_MANIFEST.json
SHA256SUMS
tools/handoff_cycle.py
```

Recommended directories:

```text
reference-docs/
project-state/
pending-inputs/
repository-update/
validation/
```

## Link namespaces

Package-internal Markdown links must resolve inside the extracted root. Repository paths are written as plain code paths or with a `repo:` prefix; they are not package-relative links. This prevents the package/repository path confusion found in the first review.

## Manifest minimum

The manifest records schema version, handoff ID/class, repository identity, gate state, immediate task, reading order, audit order, pending input coordinates, open dispositions, intended Drive destination, and repository-update status.

Do not place the archive's own final SHA-256 in the archive. Record that externally after creation. Do not record mutable upload status inside immutable content unless the same Drive file is deliberately updated in place and re-read after the final update.

## Reading budget

`START_HERE.md` should be short. The first conceptual read is `PROJECT_ORIENTATION.md`. Stable operation snapshots should be linked, not copied into the start page. The dated project snapshot contains only current coordinates, immediate action, claim boundary, and open dispositions.

## Validation

The included validator checks required files, internal SHA256SUMS coverage, manifest shape, reading-order targets, package-internal links, stale delivery phrases, and full-cycle assets. Archive-level safety is checked separately before extraction and recorded under `validation/`.
