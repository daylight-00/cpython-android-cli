# Stage 3-C Phase 5 Gate 2: First Installed Runtime Relocation Failure

> **Status:** PRESERVED TARGET FAILURE — verifier count correction pending rerun
> **Target:** Termux on Android arm64
> **Workflow result:** `STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=FAIL rc=65`

## Archive identity

```text
stage3c-phase5-installed-runtime-relocation-results-20260712-161446.tgz

sha256
  ccbe1aab6c98f161cd3fa0ba9a5c116c2bff9423caf389fdff10c7d51270f15f

size
  24,212,459 bytes

members
  434

regular files / directories
  401 / 33

unsafe, link, or special archive entries
  0
```

The archive was inspected before extraction. It contains no absolute paths, parent traversal, links, or special entries.

## Result-index integrity

```text
root result-index sha256
  4da55e60a31c41d6c7ee449eae233a6bd16328538381ea44866c72c817e18ba7

root indexed files
  393 / 393 exact

baseline result-index sha256
  8d26a1a058f36682bcbc9c8bd8f1fc44f0328f05dee14772cc641fc5e1f9661a

baseline indexed files
  341 / 341 exact

embedded Phase 4 result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

embedded Phase 4 indexed files
  294 / 294 exact

hash, size, mode, missing, and duplicate mismatches
  0
```

## Workflow result

```text
baseline                         0
move                             0
engine_verify                    0
base_probe                       0
smoke                            0
venv_probe                       0
uv_run_probe                     0
closure_inventory                0
closure_analysis                 0
closure_extension_imports        0
relocated_baseline_verification  0
stale_prefix_scan                0
final_verification              65
```

The independent Gate 2 verifier executed all 46 checks:

```text
checks
  46

passed
  45

failed
  1

failed check
  installation_root_entry_count_717
```

## Passed relocation evidence

```text
location A Gate 1 prerequisite      80/80 PASS
accepted Phase 4 identity           exact
whole installation-root move        PASS
same filesystem                     PASS
installation-root inode preserved   PASS
location A root absent              PASS
location B root present             PASS
location B Python executable        PASS
registry before / after             exact
engine verify at location B         PASS
stale A references in moved tree    0
stale A references in B probes      0
location B Gate 1 revalidation      80/80 PASS
```

Relocated runtime result:

```text
Python                              3.14.6
platform                            android
machine                             aarch64
SOABI                               cpython-314-aarch64-linux-android
MULTIARCH                           aarch64-linux-android
HTTPS                               200
uv venv                             PASS
uv run --with anyio                 PASS
ELF objects                         81
DT_NEEDED edges                    329
unresolved edges                     0
system SONAME dlopen                5/5
extension imports                  67/67
```

## Payload and mutation identities

```text
portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

portable entries
  714 / 714 / 714

strict payload fingerprint
  ebd8b16feec5c76ca5b0291709a35d891eb09ed26f12f0a52a76692193849409

strict entries
  714 / 714 / 714

installation-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

installation-root entries
  719 / 719 / 719

pycache paths
  0

special paths
  0
```

The three values are location A, location B immediately after the move, and location B after all probes. All identities remained exact.

## Root cause

The verifier incorrectly expected `717` entries in the complete installation root. The frozen Phase 4 engine intentionally leaves a five-entry management surface outside the 714-entry payload tree:

```text
prefix/                                  directory
.cpython-android-cli/                    directory
.cpython-android-cli/lock                regular file
.cpython-android-cli/registry.json       regular file
.cpython-android-cli/transactions/       directory
```

Therefore:

```text
payload entries inside prefix            714
management and prefix-root entries         5
complete installation-root entries       719

complete root type counts
  directories                            60
  regular files                         656
  symlinks                                3
  special                                 0
```

The omitted entries were the durable installation lock and the empty recovery transaction root. Both are intentional Phase 4 state, not relocation contamination.

## Correction

Replace the single incorrect check with an exact complete-root shape check:

```text
entry_count       719
directory_count    60
regular_count     656
symlink_count       3
special paths       0
```

The check must hold at location A, location B immediately after `mv`, and location B after all runtime probes. The verifier remains exactly 46 checks.

No installer, registry, transaction, recovery, durability, relocation, runtime, or claim-boundary semantics are changed.

## Claim boundary

This failed run is strong positive relocation evidence but does not freeze Gate 2 because the committed verifier rejected the authoritative result. A corrected Termux rerun and uploaded TGZ inspection remain required.

Cross-filesystem copy relocation, reinstall, repair, addon lifecycle, uninstall preservation, upgrade, downgrade, and physical power-loss persistence remain outside this gate.
