# ADR-0005: Enforce an Artifact-Only Installer Boundary

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

A repository split is unsafe while the installer still knows producer workspace layout, source checkout paths, dependency build directories, or launcher sources.

## Decision

The installer may consume only:

```text
release index or explicit local artifact selection
standalone archive
versioned product metadata
checksums and trust policy
installation target and profile policy
registry and transaction state
```

The installer must not consume:

```text
CPython source checkout
producer build tree
dependency build directories
launcher source
repository-relative staging layout
```

The decisive integration test deletes or isolates producer state and installs from the release envelope alone.

## Consequences

- Standalone and installer can acquire independent release cadences.
- Repository promotion becomes mechanical rather than architectural.
- Failures can be assigned to producer qualification, acquisition, or lifecycle boundaries.
- Shared schema compatibility must be explicit instead of relying on internal paths.
