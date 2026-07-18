# E2-P3 Archive Qualification Harness Correction

## Scope

This authority corrects two harness-only false negatives discovered by the first real-Termux archive-only execution. The frozen archive, sidecars, 35-check target matrix, product bytes, producer authority, and package authority are unchanged.

## Failed execution evidence

```text
result archive        0864173ef3b6b735ef3168b26aed6c5052296289a7c0771cb05754318fb63a79
profile               termux-real
result                33/35
failed checks         venv_relocation, wheel_tag_android24
repository            unchanged at ecfe4fafb048e9649f9cb91657c36b45b838ab7d
```

All runtime identity, relocation, ELF closure, 67/67 extension imports, HTTPS, offline pip, uv explicit-interpreter, product fidelity, and archive immutability checks passed.

## Defect adjudication

### `venv_relocation`

The created venv was valid and reported the expected lexical executable path and frozen base prefix. The harness called `Path.resolve()` on `venv/bin/python`, followed the normal venv symlink to the base interpreter, and then incorrectly required that resolved target to remain inside the venv directory.

The corrected check compares the reported executable and prefix lexically while retaining resolved equality for `base_prefix`.

### `wheel_tag_android24`

The base `install_only_stripped` runtime intentionally does not carry `pip`. The harness attempted to import `pip._vendor.packaging.tags` from the base runtime even though the same execution successfully created a venv with pip and installed an offline wheel.

The corrected check reads compatible tags from pip's vendored packaging inside the newly created venv. The required tag remains `android_24_arm64_v8a`.

## Verification

```text
failed-real-result audit       24/24
static replay                  9/9
static result verifier         19/19
regression                     21/21
external correction audit      31/31
historical verifier            24/26, exact two-failure adjudication
current repository verifier    33/33 staged and commit
```

## Claim boundary

This correction does not qualify the real-Termux profile. It only freezes corrected harness semantics and authorizes a retry against the same frozen envelope. Emulator qualification, combined qualification, metadata finalization, selectability, publication, installer conversion, and transition behavior remain separate gates.
