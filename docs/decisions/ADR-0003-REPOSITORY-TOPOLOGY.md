# ADR-0003: Incubate Logically, Then Promote the Standalone Product

- **Status:** Superseded by ADR-0006
- **Date:** 2026-07-16

## Context

The current repository contains implementation, experiments, frozen evidence, handoffs, and collaboration rules. Creating a clean standalone repository immediately would duplicate code before the artifact boundary is stable. Keeping every future product permanently coupled in one repository would obscure ownership and release cadence.

## Decision

Use the current repository as an Epoch 2 incubator:

1. declare component ownership;
2. create stable build/package/verify and install/uninstall interfaces;
3. make the installer an artifact-only consumer;
4. validate both sides in the same repository;
5. promote the standalone component into `cpython-android-standalone` with relevant history preserved.

The current repository remains the installer, engineering-history, and evidence authority unless a later ADR changes that role.

## Consequences

- No premature code duplication.
- Experiments and failed evidence remain available without cluttering the eventual product surface.
- Repository promotion has explicit acceptance gates.
- A third shared-code repository is avoided unless concrete duplication later justifies it.

## Supersession

ADR-0006 replaces history-preserving component promotion with a clean Epoch 3 product repository initialized from an accepted upstream-derived product seed. The current repository remains the permanent research and source-producer laboratory.
