# Session-Operation Lessons and Changelog

This records collaboration/tooling lessons, not project acceptance history.

## 2026-07-14 — full-cycle onboarding review

- A package-relative handoff snapshot must not reuse repository-relative Markdown links. Use package links for package files and plain `repo:` paths for repository documents.
- Do not embed mutable upload failure/status claims in immutable archive content. The final upload/readback receipt is external.
- A successor should receive a concise project philosophy capsule before being sent into a long repository reading path.
- Onboarding is incomplete unless the same package also explains and mechanically validates the next session-close cycle.
- Added a validator, complete-cycle document, package specification, and templates.

## 2026-07-14 — structured recurring handoff

- Separated stable session operations from dated project state.
- Defined work, mandatory handoff, and miscellaneous backup packages.
- Defined two-package close when existing work/result is intentionally left for the successor.
- Made index/summary-first evidence inspection the default.

## Wrapper lessons

- Outer `set -e` can bypass status/archive/upload; capture fallible workflows in a controlled child context.
- Optional absence must return `0` and be recorded.
- Resolve repository paths explicitly; scripts invoked by absolute path may still run Git in the caller directory.
- Derive expected post-tree with an isolated index after every patch change.
- Avoid logging patterns that keep inherited descriptors open and appear hung.

## Connector and evidence lessons

- Resolve duplicate Drive folders by exact IDs and direct children.
- Raw readback is part of publishing.
- `.bin` mount suffix does not imply content conversion.
- Local upload paths must be below `/mnt/data`; first-turn rewrite may be blocked.
- A verifier PASS can describe a valid failure capture, not a project PASS.
- Review maintenance warnings after build success unless they explain the active failure.

## 2026-07-15 — post-commit idempotency verification

- An `already-applied` runner must not compare the empty post-commit index against the package patch.
- Staged-patch and `git write-tree` checks belong only to the pre-commit `apply-pending` branch.
- The idempotent branch must verify the committed parent, tree, subject, author/committer, signoff, exact committed diff, remote ref, and clean worktree.
- A rerun-only status failure does not invalidate an earlier complete PASS archive, but the contradictory result must be preserved and classified.
