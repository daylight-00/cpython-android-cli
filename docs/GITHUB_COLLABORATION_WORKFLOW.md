# GitHub, Termux, and Assistant Collaboration Workflow

> **Status:** Active project workflow
> **Repository:** `daylight-00/cpython-android-cli`
> **Default branch:** `main`
> **Canonical device checkout:** `$HOME/projects/cpython-android-cli`

## Purpose

This document defines how the user, the real Termux device, GitHub, and the assistant environment collaborate on this project.

The workflow separates three kinds of authority:

```text
GitHub repository
  shared source, scripts, documentation, and commit history

Termux device checkout
  authoritative Android runtime execution and generated target evidence

assistant environment
  repository inspection, reasoning, text/code preparation, and connector-mediated publication
```

No one layer substitutes for the others.

## Source-of-truth order

For architecture and project state:

```text
1. current GitHub default-branch commits
2. current handoff and stage documents
3. selected evidence documents
4. experiment recipes and machine-readable verifier contracts
5. chat transcript as temporary coordination context
```

Do not reconstruct the project from chat memory alone.

Current reading path:

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3.md
  -> docs/stages/STAGE3B_SCOPE.md
  -> docs/stages/STAGE3B_PHASE5_SCOPE.md
  -> docs/evidence/
```

For target behavior, real-device output outranks assistant-side assumptions.

## GitHub connector execution model

The assistant's GitHub integration is API-mediated. It is not necessarily a local clone with a working tree and index.

Conceptual read path:

```text
assistant
  -> authenticated GitHub connector
  -> repository / commit / file API
  -> remote repository object
```

Typical read operations include:

```text
repository metadata
recent commits
commit diffs
file content at a ref
pull-request metadata and patches
```

A file read returns both content and its current blob SHA.

## Text write model and optimistic concurrency

Text-file updates use the current blob SHA as an optimistic concurrency token.

Conceptual update:

```text
fetch current file at branch
  -> receive content + blob SHA
  -> prepare complete replacement text
  -> update only if SHA still matches
```

If the file changed after it was fetched, the update must not overwrite the newer version blindly. Re-fetch, compare, and reapply the intended change.

Rules:

```text
never force-push as a normal workflow
never overwrite concurrent user work silently
prefer small intentional commits
preserve failed experiments and their explanations
keep result claims narrower than the evidence
```

## Branch and pull-request policy

For multi-file changes, probe-contract changes, or architecture/status updates, the default assistant publication path is:

```text
main
  -> agent/<bounded-description> branch
  -> small commits
  -> pull request
  -> review of changed files and diff
  -> non-force merge to main
```

A narrow one-file correction may use a direct contents update only when that is already the agreed workflow and concurrency risk is low. A branch and PR remain preferred when changes alter executable probes, validation contracts, or multiple authoritative documents.

Do not rewrite or squash evidence history merely to make the graph look tidy. A PR may be squash-merged when it represents one coherent publication unit, but the branch's intermediate commits should still be intentional and reviewable.

## Authorship and attribution

Connector-created commits are made through the authenticated GitHub account and may appear with the repository owner's normal author/committer identity.

Do not infer from Git commit authorship alone whether text was typed on the device, prepared by the assistant, or created through the connector. The commit message, PR description, and project evidence should explain the change's purpose and provenance.

## Real-device responsibility

The authoritative target experiments run on the user's Termux device.

Typical prompt:

```text
u0_a534@localhost:~/projects/cpython-android-cli$
```

The assistant must not claim that an unrelated Linux sandbox reproduces:

```text
Android linker behavior
Termux host paths
Android/APEX provider state
Termux CA integration
target uv behavior
whole-prefix relocation on Android
```

Normal target loop:

```text
assistant
  inspect current GitHub state
  derive the smallest discriminating next gate
  repair or add bounded helpers
  record rationale and claim boundary
  publish through GitHub
  provide exact Termux commands

user
  fast-forward the device checkout
  run commands on the real device
  paste complete stdout/stderr and requested result files

assistant
  classify the exact result
  distinguish product failure from probe failure
  update evidence and status documents
  publish the next bounded step
```

## Device synchronization

Normal synchronization from the canonical checkout:

```sh
cd "$HOME/projects/cpython-android-cli"
git pull --ff-only
```

When an explicit remote branch must be followed before merge:

```sh
git fetch origin
git merge --ff-only origin/<branch>
```

The assistant should not instruct the user to use `git reset --hard` to accommodate rewritten remote history.

Before running a new target gate, the user may verify:

```sh
git status --short
git log -1 --oneline
```

Local user modifications must not be discarded silently.

## Git versus generated-artifact transport

The project intentionally separates tracked source state from generated target products.

```text
Git
  src/
  scripts/
  config/
  docs/
  experiments/

ignored generated state
  out/
  work/
  results/
  dist/
  cache/
  tools/
```

Generated launcher and package products use the project's declared transport workflow, commonly rsync, rather than being committed to Git.

The current high-level split is:

```text
source, scripts, docs, experiment history
  -> GitHub

generated out/<target>/<profile>/ products
  -> declared workstation/Termux transport
```

Do not upload ignored runtime trees or bulk result directories merely to move them between machines.

## Assistant sandbox boundary

Files created in an assistant sandbox such as `/mnt/data` or `/tmp` are not automatically repository state.

```text
GitHub file or commit
  shared project truth

assistant-local file
  temporary design, validation, or artifact material
```

A local assistant file becomes project state only after its content is deliberately published to the correct repository path and branch.

Do not invent `sandbox:` download links for files that exist only on GitHub. Conversely, do not cite a GitHub path as if an assistant-local file were already committed.

## Evidence preservation

Generated target evidence normally remains under ignored `results/` or `work/` paths on the device.

For each bounded gate, preserve at minimum:

```text
complete stdout/stderr
exact command and input paths
machine-readable summary JSON
row-level TSV when aggregates hide detail
runtime fingerprint before and after
final marker lines
```

Selected conclusions are promoted into `docs/evidence/` as compact, reviewable records.

Distinguish:

```text
raw generated evidence
  detailed device-local result tree

selected evidence document
  durable interpretation and claim boundary

stage scope/status document
  sequence, acceptance conditions, and next action
```

Do not rerun expensive target work merely because a downstream summarizer changed when the raw evidence remains valid.

## Probe-failure discipline

A failed validation run may mean:

```text
product defect
host/environment difference
probe implementation defect
invalid control design
mutation introduced by validation
missing or stale input
```

Do not collapse these categories.

When a probe is wrong:

```text
record the failed boundary
identify the invalid assumption
repair the smallest contract
preserve the original incident
freshly reassemble mutable candidates when metadata may have changed
rerun only the necessary gate
```

The Stage 3-B Phase 5 bytecode incident is the reference example: semantic closure passed, but an isolated child ignored shell-level `PYTHON*` controls and mutated the candidate. The probe was repaired and the candidate was freshly reassembled rather than surgically cleaned.

## Documentation and commit discipline

For each meaningful transition:

```text
1. inspect current branch content and recent commits
2. identify the authoritative status documents
3. make the smallest executable change required
4. document the rationale and claim boundary
5. publish through a bounded branch/PR when appropriate
6. run on the real target
7. record exact result in docs/evidence
8. update stage acceptance conditions and next action
```

Do not leave major conclusions only in chat.

Experiment recipe and result document have different responsibilities:

```text
experiment recipe
  how evidence is generated

verifier
  machine-readable pass/fail contract

result document
  what was observed and what follows

scope document
  where the result sits in the stage sequence
```

## Current project-specific operating contract

For the active Stage 3-B Phase 5 work:

```text
candidate runtime
  work/termux/stage3b-promoted-runtime/prefix

frozen runtime control
  work/termux/stage2c/runtime/prefix

candidate-specific result roots
  results/termux/stage3b-*

frozen Stage 3-A result root
  read-only evidence
```

Both candidate and frozen runtime trees receive before/after mutation fingerprints during validation workflows.

The next gate should be selected from the open Phase 5 acceptance conditions rather than from packaging or consumer-integration work.

## References used to establish this workflow

This project workflow incorporates lessons from:

```text
daylight-00/termux-native-desktop
  docs/refactor/0062-next-session-handoff-vscode-control-and-collaboration-workflow.md

  real-device authority
  ff-only synchronization
  evidence-preserving small commits
  GitHub documents as shared truth
  assistant sandbox as non-authoritative working material

daylight-00/chatgpt-session-workspace-study
  docs/part-1-project-workflow/github-connector.md

  API-mediated connector model
  blob-SHA optimistic concurrency
  branch/ref and contents operations
  branch + pull request publication path
  connector capability boundaries
```

The CPython Android CLI project adopts those ideas only where they fit its own tracked/generated-state split and target-validation workflow.
