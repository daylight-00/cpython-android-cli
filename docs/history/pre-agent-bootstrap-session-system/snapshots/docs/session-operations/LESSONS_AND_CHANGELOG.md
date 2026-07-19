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
- Derive expected post-tree with an isolated index after every patch change when a predeclared post-tree is part of the contract.
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

## 2026-07-15 — transient workspace versus evidence archive

- Temporary uv virtual environments, copied prefixes, shims, caches, and managed-directory decoys may contain normal symlinks and must not be archived as evidence payload.
- Preserve root-level definitions, process records, stdout/stderr, selected-path metadata, summaries, and invariant snapshots; hash them before pruning transient workspaces.
- Run result-tree safety after pruning and before the self-excluding index. A packaging failure after target PASS does not require target re-execution when retained evidence is exact and independently verified.

## 2026-07-15 — minimum sufficient validation

- Gate 4 and Gate 5 corrections showed that extra validation layers can create false-negative surface without increasing product assurance.
- Classify work as repository-only, locally provable behavior, or target authority; require evidence proportional to that class.
- Reuse frozen evidence by exact SHA-256 and Git identity instead of rerunning or copying it into unrelated transactions.
- Use one semantic verifier per authority boundary. Add meta-verification only when that verifier changes or fails.
- A changed harness or verifier must pass three fixtures before target use: success, expected negative, and incomplete or missing outcome.
- Discovery-sensitive tests must isolate physical cwd ancestry and ambient virtual environments, not only `HOME` and `PATH` variables.
- A state-transition verifier must validate the intended post-state; stale pre-state wording is not a valid invariant.
- Ordinary append-only fast-forward repository transactions need exact base/content, focused repository checks, commit/push/readback, and clean post-state—not a target rerun or backup bundle.

## 2026-07-15 — Drive upload fallback discipline

- Use the normal Google Drive connector raw-file upload as the single first attempt for assistant-generated artifacts.
- If that attempt fails, stop connector upload work for that artifact in the current turn. Do not try Docs import, format conversion, native-file creation, alternate upload endpoints, or repeated retries.
- Expose the exact local artifact through a user-visible file link immediately. A later Drive retry requires a later turn or explicit user request.

## 2026-07-15 — artifact naming and wrapper state discipline

- The project Termux download directory is `$HOME/Downloads`, and execution commands must use the artifact's actual file name. A user-visible display label is not the saved file name.
- Do not `source` generated status or manifest data unless every value is shell-quoted by construction. Prefer JSON or explicit parsing for values that may contain spaces or punctuation.
- Never remove a directory while the wrapper or one of its child processes still uses it as the current working directory. Move to a stable directory before cleanup.
- Apply isolated `HOME` and XDG values only to the target child commands that require them. Restore the real user environment before rclone upload or any operation that depends on user configuration.
