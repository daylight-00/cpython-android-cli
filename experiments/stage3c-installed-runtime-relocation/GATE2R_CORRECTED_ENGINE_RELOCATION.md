# Stage 3-C Phase 5 Gate 2R: Corrected-Engine Relocation Regression

> **Status:** ACTIVE — authoritative Termux evidence pending
> **Prerequisite:** frozen Gate 3A corrected reinstall and repair product acceptance
> **Target:** Termux on Android arm64

## Regression question

> Does a complete installation root created by the accepted corrected engine retain exact ownership identity and full runtime behavior after a same-filesystem inode-preserving move?

## Frozen input

```text
Gate 3A archive
  stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-191758.tgz

archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

Gate 3A checks
  29/29 repair scenarios
  80/80 Gate 1 regression
  69/69 acceptance verifier
```

## Design

The historical Gate 2 workflow and its 46-check verifier remain unchanged in repository authority.

At execution time, temporary copies are created outside the result and work roots. The temporary copies apply only these adapters:

```text
Gate 1 baseline
  ENGINE_OVERRIDE support
  original SCRIPT_DIR preserved

historical relocation
  ENGINE_OVERRIDE support
  BASELINE_RUNNER_OVERRIDE support
  corrected engine forwarded to the baseline runner
  original SCRIPT_DIR preserved
```

The accepted corrected engine is used for:

```text
fresh runtime-base installation at location A
engine verification at location A
engine verification at location B
```

Temporary script patching is machine-recorded and must match exactly once at each authorized replacement site.

## Historical relocation contract

The unchanged historical verifier must pass all 46 checks:

```text
location A Gate 1              80/80
location B Gate 1              80/80
same filesystem                true
installation-root inode        preserved
location A absent              true
location B present             true
complete-root shape            719 / 60 / 656 / 3
complete-root identity         exact across move and probes
registry                       byte exact
portable identity              f860caf... exact
strict same-tree identity      exact
stale location-A references    0
transaction residue            0
HTTPS                          200
uv venv / uv run               PASS / PASS
native closure                 81 / 329 / 0
system SONAME                  5/5
extension imports              67/67
```

## Corrected-engine authority verifier

An additional 15-check verifier requires:

```text
accepted Gate 3A result-index exact
accepted Gate 3A 69/69 and workflow all zero
accepted Phase 4 result-index exact
historical relocation 46/46 and workflow all zero
fresh baseline create 714 / mutations 715
corrected engine file SHA exact
corrected operations file SHA exact
all six temporary patch sites applied exactly once
canonical authority JSON
```

## One-command Termux run

The wrapper verifies and extracts the accepted Gate 3A TGZ, runs the complete regression, captures status and result indices, and packages evidence on PASS or FAIL.

```sh
cd "$HOME/projects/cpython-android-cli" && \
git fetch origin agent/phase5-gate2r-corrected-engine-relocation && \
git switch --detach origin/agent/phase5-gate2r-corrected-engine-relocation && \
bash experiments/stage3c-installed-runtime-relocation/run-gate2r-corrected-engine-relocation-termux.sh
```

No separate extraction or `tar` command is required.

## Expected markers

```text
INSTALLED_RUNTIME_RELOCATION_GATE1_PREREQUISITE=80/80 PASS
INSTALLED_RUNTIME_RELOCATION_REVALIDATION=80/80 PASS
STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=PASS
GATE2R_HISTORICAL_RELOCATION=46/46 PASS
GATE2R_CORRECTED_ENGINE_AUTHORITY=PASS
GATE2R_VERIFICATION=15/15 PASS
STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION=PASS
TERMUX_EVIDENCE_ARCHIVE=...
TERMUX_EVIDENCE_ARCHIVE_SHA256=...
TERMUX_EVIDENCE_ARCHIVE_SIZE=...
TERMUX_WORKFLOW_RETURN_CODE=0
```

## Claim boundary

A PASS proves same-filesystem rename-style relocation of a complete root created and verified by the accepted corrected engine.

It does not prove:

```text
cross-filesystem copy relocation
modified owned-leaf preservation
unowned sentinel preservation
addon lifecycle
uninstall
upgrade or downgrade
```
