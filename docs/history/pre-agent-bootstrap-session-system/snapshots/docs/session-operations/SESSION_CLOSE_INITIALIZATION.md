# Session Close Initialization

This is the canonical instruction when the owner asks to end a session. The owner may simply say: “Read `docs/session-operations/SESSION_CLOSE_INITIALIZATION.md` and prepare the handoff.”

## 1. Freeze the closing observation

Record branch/HEAD/tree, remote active/main, last accepted gate, open gate, pending work/result, exact Drive IDs/names/sizes/known hashes, and open dispositions. A result left for the successor is `EXISTS — UNAUDITED`; do not partially accept it during close preparation.

## 2. Separate documentation domains

- Stable collaboration/tooling: `docs/session-operations/`.
- Changing project state: new dated `docs/handoff/<date>-<boundary>.md`.
- Frozen project claims: `docs/evidence/`, `docs/stages/`, and experiments.

Do not repeat stable operating rules in every dated handoff. Mark old distributed operating documents as compatibility references to the canonical directory.

## 3. Prepare repository documentation change

Create a narrow patch on the exact tree, one application wrapper, changed-file/claim manifest, link validation, and isolated-index expected-tree calculation. Do not commit or push directly to the owner's checkout.

## 4. Build package(s)

Follow `HANDOFF_PACKAGE_SPEC.md`. Required handoff files are `START_HERE.md`, `PROJECT_ORIENTATION.md`, `HANDOFF_MANIFEST.json`, `SHA256SUMS`, and `tools/handoff_cycle.py`.

Package count:

```text
new owner action        work + mandatory handoff + optional backup
unexecuted prior work   mandatory handoff + optional backup
existing unaudited result mandatory handoff + optional backup
```

## 5. Validate the full cycle

- Run `handoff_cycle.py verify`, `onboard`, and `close-readiness` on the extracted handoff.
- Check one safe root, internal hashes, links, manifest fields, and absence of stale delivery claims.
- Render one mock next dated handoff/manifest from the templates and validate the mock package.
- Record the review in machine-readable and human-readable validation files.

## 6. Publish

Use a new descriptive Drive folder. Record intended destination inside the package. Record actual upload and raw-readback receipt externally after the immutable archive exists. Do not leave an “upload failed/not uploaded” statement inside a package that is later successfully delivered.

## 7. Final response

Report closing state, refactor, package count/purpose, final external hashes/sizes/Drive IDs, successor's first action, and local links. Do not ask the owner to run a new project workflow after closure.
