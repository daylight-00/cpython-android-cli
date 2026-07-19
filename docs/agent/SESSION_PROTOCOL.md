# Session Protocol

> **Revision:** 2
> **Role:** mandatory collaboration, transport, execution, and evidence ABI
> **Read requirement:** every agent session reads this file in full before work

## SP-01 — Session input authority

The owner's full Git bundle and matching SHA-256 sidecar are the session's sole repository input authority. Verify the sidecar and `git bundle verify` before repository interpretation. Do not infer repository state from chat, filenames, web pages, or a previous local clone.

## SP-02 — Isolated reconstruction

Use local Git to reconstruct a separate workspace. Record bundle refs, branch, HEAD, tree, and cleanliness. The agent never assumes access to or mutates the owner's canonical S22 checkout.

## SP-03 — Directional Google Drive transport

The transport direction determines the responsible interface:

- **agent → owner:** the agent attempts one raw-file upload through the Google Drive connector. The owner receives the package with `rclone` from the designated Drive location.
- **owner → agent:** the owner uploads one complete result archive and sidecar with `rclone` to the designated Drive folder. The agent discovers the folder, lists direct children when needed, and fetches the exact raw bytes through the Google Drive connector.

The Google Drive connector is always the agent's first transport and receipt-readback interface when available. Resolve duplicate names with parent, folder ID, creation time, and direct-child listing. Compare reported size and SHA-256 whenever raw bytes can be fetched.

## SP-04 — Connector failure boundary

For agent-generated files, attempt the normal raw-file Drive upload exactly once when supported. If that connector call fails, do not retry, convert formats, use a native Google file, call another endpoint, invoke command-line upload, or attempt another transport. Expose the exact artifact under `/mnt/data` with its real filename as the user-visible fallback.

For owner-generated results, attempt retrieval through the Google Drive connector. If connector discovery or raw-byte fetch fails, stop and report the exact connector failure. Do not substitute `curl`, `wget`, network Git, assistant-side `rclone`, web download, or an unrelated attachment path in the same turn.

## SP-05 — Network and artifact acquisition

Do not assume DNS or outbound command-line downloads work. `curl`, `wget`, and network Git are not artifact authority paths in the assistant environment. Web search may establish metadata or locate an official reference, but exact claim-bearing bytes must arrive through Drive, a user attachment, or a bounded owner-run acquisition package.

## SP-06 — GitHub prohibition

Do not use the GitHub connector, GitHub API, `gh`, or remote Git for repository clone, fetch, pull, push, branch management, issue/PR context, or file inspection in this project. Repository exchange is bundle- and package-based. The owner's transaction runner performs canonical push and remote readback.

## SP-07 — Responsibility split

```text
owner
  chooses final scope and policy
  operates canonical S22 checkout and real devices
  runs one bounded wrapper
  performs canonical commit/push through that wrapper
  supplies full bundles and PASS-or-FAIL receipts

agent
  verifies and reconstructs the bundle
  reads only the mandated context
  designs and implements bounded changes in isolation
  writes semantic verifiers and negative fixtures
  delivers one runner package
  retrieves and audits complete receipts
  preserves claim and non-claim boundaries
```

Do not ask the owner to edit files, interpret large logs, or execute loosely coupled commands when one wrapper can perform the workflow.

## SP-08 — Transport loop

```text
new session
  owner -> agent: full Git bundle + SHA-256 sidecar

repository or local change
  agent -> owner: one .tar.zst package + sidecar + one apply.sh or RUN.sh

execution result
  owner -> agent: owner uploads one complete receipt/result .tar.zst + sidecar with rclone;
                  agent retrieves it through the Google Drive connector
```

The designated default exchange folder is `HW-T-results` unless a task explicitly names another folder. Group related artifacts into one archive per direction whenever practical. Binary connector mounts may use a `.bin` suffix; content identity, not suffix, is authority. A connector-fetched `.bin` file is accepted only after its SHA-256 matches the owner-supplied sidecar.

## SP-09 — One-runner owner interface

This is the mandatory one-runner owner interface. The owner should normally execute one command. The runner resolves its own paths and performs applicable checksum, repository precondition, apply, stage, verification, commit, push, remote readback, post-verification, receipt creation, Drive upload, rollback, and final status reporting.

Use `$HOME/Downloads/<actual-filename>` for Termux exchange. Display labels are not filenames.

## SP-10 — Work classification

Classify the task before validation:

```text
R  repository-only change with no new behavior or target claim
L  locally provable artifact, reconstruction, or code behavior
T  new Android/Termux product, installation, transition, durability, or device claim
```

The classification and non-claims appear in the onboarding certificate and package manifest.

## SP-11 — Minimum sufficient validation

```text
R  exact base and clean state; exact changed paths; syntax/diff; relevant repository verifier;
   commit, push, remote readback, clean post-state

L  all relevant R checks; focused local reconstruction, unit, or artifact evidence;
   before/after identities for the changed authority

T  all relevant R/L checks; one bounded PASS-or-FAIL target archive;
   one independent audit of claim-bearing evidence
```

Do not rerun or rearchive frozen target evidence when its bytes, Git boundary, and claim remain unchanged.

## SP-12 — Verifier design

Use one semantic verifier per authority boundary. A changed harness or verifier must pass success, expected-negative, and incomplete/missing fixtures. Discovery-sensitive tests isolate physical working-directory ancestry, ambient virtual environments, ignored runtime trees, and cleanup behavior. Do not add verifier-of-verifier layers unless the verifier itself changed or failed.

## SP-13 — Git transaction discipline

An ordinary append-only transaction requires exact base HEAD/tree, clean main, exact changed content and modes, expected staged tree, focused verification, commit, push, remote readback, and clean post-state. History rewrite or destructive ref movement additionally requires an exact backup bundle, ref map, leases, and rollback behavior.

Cross-session content authority is the Git tree when commit metadata differs. Project commits use `daylight-00 <hwjang00@snu.ac.kr>` unless explicitly changed.

## SP-14 — Wrapper failure containment

Do not let an outer `set -e` bypass final status, archive creation, upload, or rollback. Capture fallible stages and return codes explicitly. Resolve paths from the runner location and use explicit repository paths. Optional absence returns success and is recorded. Never remove a directory while the runner or child process uses it as its current working directory.

## SP-15 — Archive safety

New archives use `.tar.zst`. Require one safe root, no absolute or parent-traversal paths, no duplicate members, no unexpected links, and no special file types. Record final SHA-256 and size outside the archive. Archive claim-bearing outputs and receipts, not disposable workspaces, caches, copied products, or unchanged authorities.

## SP-16 — Result inspection order

```text
1. Drive metadata and size
2. archive safety and member table
3. self-excluding result index
4. final/workflow status
5. summary JSON and return-code catalog
6. single claim-bearing verifier or audit
7. bounded output around the first meaningful failure
8. full raw log only when bounded evidence is insufficient
```

A console marker alone is never acceptance.

## SP-17 — Failure discipline

Preserve the first meaningful failure and all available receipts. Distinguish product failure from harness, verifier, packaging, transport, or cleanup failure. Mark blocked downstream stages explicitly. Do not weaken a valid gate merely to obtain PASS. Make the smallest justified correction and retain contradictory failed attempts.

## SP-18 — Context and communication discipline

Read only the immutable bootstrap closure and task-selected modules. Do not perform broad repository summarization during onboarding. Report short updates at meaningful boundaries. Do not leave material decisions only in chat; place stable rules, current state, or frozen evidence in their authoritative repository layer.

## SP-19 — Session closure without handoff packages

Ordinary mandatory handoff packages are retired. A session closes when current state and task routing are accurate, evidence is frozen where required, generated views match, repository verifiers pass, commit/push/remote readback succeed, and main is clean. The repository itself is the successor authority.

The owner creates the next full bundle with:

```bash
bash tools/export-agent-session-bundle.sh
```

A dated handoff is created only when the task itself is historical analysis or an explicit exceptional decision requires one; it is never the normal session transport.

## SP-20 — Device and external-input boundaries

Use S22, Note9, emulator, or another target only when `AGENT_TASK.json` explicitly requires class T evidence for that target. For exact upstream bytes that the assistant cannot acquire, search Drive first; if absent, create one bounded owner-run acquisition runner instead of improvising network workarounds. No device or external-input absence is silently converted into a broader claim.
