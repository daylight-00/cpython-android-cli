# Stage 3-C Phase 5 Gate 1: Installed Runtime Baseline First Target Failure

> **Status:** PRESERVED TARGET FAILURE — corrected rerun pending
> **Target:** Termux on Android arm64
> **Workflow result:** `STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=FAIL rc=61`

## Result archive identity

```text
stage3c-phase5-installed-runtime-baseline-results-20260712-140843.tgz

sha256
  efff3b0306f375a0d839afcf7d3c2784b8b34143043f44471536d065471dcd03

size
  24,034,984 bytes

members
  373

regular files / directories
  344 / 29

unsafe, link, or special entries
  0
```

The archive was independently inspected before extraction. It contains one result tree and no absolute paths, `..` traversal, links, or special entries.

## Result-index integrity

```text
result-index sha256
  1eccc39410dddb027a0d94d5a7f342a96a8636f0533a9c32087e0973f2615e28

indexed files
  337

hash mismatches
  0

size mismatches
  0

mode mismatches
  0

duplicate indexed paths
  0
```

Nested `result-index.log` files are intentionally excluded by the result-index writer. All declared indexed entries were present and matched.

## Workflow result

```text
install                       0
engine_verify                 0
base_probe                    0
smoke                         0
venv_probe                    0
uv_run_probe                  0
closure_inventory             0
closure_analysis              0
closure_extension_imports     0
final_verification           61
```

The independent verifier executed all 80 checks:

```text
checks                       80
passed                       78
failed                        2
```

Failed checks:

```text
phase4_result_index_exact
installed_fingerprint_exact
```

## Passed installed-product evidence

The failure was not an installation, runtime, HTTPS, uv, or native-closure failure.

```text
fresh install create actions             714
registry mutation count                   715
engine verification                      PASS
registry artifacts                          1
registry owned paths                      714
manifest-to-registry rows                exact

Python                                   3.14.6
platform                                 android
machine                                  aarch64
SOABI                                    cpython-314-aarch64-linux-android
MULTIARCH                                aarch64-linux-android
runtime and subprocess identity          installed prefix
HTTPS                                    200
uv venv                                  PASS
uv run --with anyio                      PASS

symlinks                                   3
ELF objects                               81
DT_NEEDED edges                          329
RUNTIME_INTERNAL edges                    80
ANDROID_SYSTEM edges                     249
unresolved edges                           0
inspection errors                          0
system SONAME dlopen                     5/5
extension imports                       67/67
```

## Immutable-state controls

Phase 4 input remained unchanged during the Gate 1 workflow:

```text
entries
  324 / 324

fingerprint before / after
  7fb5da48e4fd80441552921bd27be9c171fd20bd11db8882ba3fe0dac44a217b
```

The installed prefix also remained strictly unchanged during runtime validation:

```text
entries
  714 / 714

strict fingerprint before / after
  df52b53a438e0b7d28584ace0e945ea3a1505d2dff8fe9572a5b9b92c7c2ec4f

pycache paths
  0

special paths
  0
```

## Failure 1 — non-authoritative Phase 4 result directory

The Gate 1 input contained an internally coherent Phase 4 result tree, but its root result-index file did not match the accepted frozen Gate 5B identity.

```text
required accepted result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

observed input result-index sha256
  9fd87dc8a68282598bddb928c751ed08e81592ee52b787cd74c1a22ed2eb2410
```

All 294 entries declared by the observed Phase 4 result-index matched their files, but internal consistency does not make a later or alternate result directory authoritative. Gate 1 must consume a fresh extraction of the accepted Phase 4 TGZ or another directory whose root result-index has the accepted SHA-256.

The exact-input gate remains unchanged.

## Failure 2 — invalid cross-form strict fingerprint comparison

The verifier compared the installed tree against the Phase 1 runtime-base source-tree fingerprint:

```text
required by the first verifier
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

observed installed strict fingerprint
  df52b53a438e0b7d28584ace0e945ea3a1505d2dff8fe9572a5b9b92c7c2ec4f
```

That comparison was invalid. The strict product fingerprint includes:

```text
directory st_size
mtime_ns
```

The deterministic archive normalizes member mtimes to zero, and installation recreates directory metadata on the target filesystem. These values are valid same-tree mutation controls but are not portable identity fields across source assembly, archive serialization, extraction, and installation.

## Correction

The corrected Gate 1 contract separates two identities:

```text
strict fingerprint
  metadata-sensitive
  before/after mutation control only

portable installed-payload fingerprint
  relative path
  entry type
  mode
  regular-file size and SHA-256
  symlink target
```

The manifest-derived and independently extracted runtime-base payload produce the same portable identity:

```text
fingerprint kind
  stage3c-installed-payload-portable-v1

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

entries
  714

regular / directory / symlink / special
  654 / 57 / 3 / 0
```

The corrected workflow also checks the accepted Phase 4 result-index before installation and fails early with `rc=62` when the mutable input directory is not the accepted frozen evidence.

The verifier remains exactly 80 checks. The old strict source-to-installed equality check is replaced by the portable manifest-to-installed identity check; strict before/after immutability remains mandatory.

## Claim boundary

This failed run provides strong positive evidence for the installed runtime behavior, but it does not close Gate 1 because one frozen input identity was wrong and one verifier identity relation was invalid.

It does not reopen or invalidate Phase 4. It does not prove relocation, reinstall, repair, addon lifecycle, uninstall preservation, upgrade, downgrade, or physical power-loss persistence.
