# Stage 3-A Final: Runtime Closure Census and Boundary Freeze

> **Status:** FROZEN
> **Stage:** 3-A
> **Input:** Frozen Stage 2 R2 + B0 runtime
> **Target tested:** Termux on Android arm64
> **Runtime baseline:** CPython 3.14.6

## 1. Stage 3-A question

Stage 3-A asked:

> What exactly is the runtime closure of the frozen Stage 2 interpreter, and which dependencies are internal, Android-provided, Termux-provided, metadata-only, or otherwise external?

The stage began with the rule:

```text
observe first
modify nothing
```

The runtime prefix was treated as data before any packaging or dependency-rewriting work.

## 2. Frozen result

Stage 3-A is complete and frozen.

The tested runtime closure model is:

```text
runtime product core
  runtime prefix
    interpreter launcher
    libpython and internal native libraries
    stdlib
    lib-dynload extension modules

native external boundary
  Android system SONAME providers
    5 unique tested system SONAMEs
    5/5 fresh-process dlopen probes PASS

host/data integration boundary
  CA trust
    Termux CA bundle integration confirmed

  timezone data
    absent in base runtime
    first-party Python tzdata fallback confirmed PASS

  temporary storage
    Termux $PREFIX/tmp observed

  device/process environment
    /dev/null

optional workload helpers
  file
  uname
  observed only through platform() information path
```

This is not a claim of universal portability across Android versions, devices, vendor images, API levels, or linker namespace configurations.

## 3. Complete runtime inventory

Observed inventory summary:

```text
file entries             3280
symlinks                    5
ELF objects                 81
DT_NEEDED edges            329
inspection errors            0
mutation check            PASS
```

The inventory tooling recorded:

```text
files.tsv
symlinks.tsv
elf-objects.tsv
elf-needed.tsv
python-runtime.json
closure-classification.tsv
unresolved.tsv
errors.tsv
summary.json
mutation-check.txt
```

The runtime tree fingerprint was unchanged before and after inventory.

Frozen claim:

> Stage 3-A inventory tooling observed the tested runtime without mutating the runtime prefix.

## 4. Native closure result

The 329 DT_NEEDED edges reduced to:

```text
9 unique needed SONAMEs
  4 RUNTIME_INTERNAL
  5 ANDROID_SYSTEM
```

Observed edge classification:

```text
RUNTIME_INTERNAL   80 edges
ANDROID_SYSTEM    249 edges
TERMUX native       0 edges
UNRESOLVED           0 edges
```

Each of the 5 unique Android-system SONAMEs passed a fresh-process SONAME `dlopen` probe.

Frozen claim:

> On the tested target, the native ELF closure is resolved by the runtime prefix plus the five tested Android-system SONAMEs, with no observed Termux native-library provider edge and no unresolved DT_NEEDED edge.

Caution:

```text
249 ANDROID_SYSTEM edges
    !=
249 unique libraries
```

and:

```text
5/5 tested SONAME loadability
    !=
universal Android portability guarantee
```

## 5. Extension-module execution result

The active extension directory was discovered from the relocated runtime path rather than stale `DESTSHARED` metadata.

Observed:

```text
extension candidates    67
isolated import PASS    67
isolated import FAIL     0
```

Frozen claim:

> All 67 immediate extension-module candidates in the selected active `lib-dynload` directory imported successfully in isolated fresh-process probes on the tested target.

This evidence concerns the enumerated extension files. It does not prove arbitrary third-party wheel compatibility.

## 6. Runtime paths versus build metadata

The extension probe exposed a critical distinction:

```text
active runtime paths
  sys.prefix
  sys.base_prefix
  sys.path
  active sysconfig.get_paths()
    -> relocation-aware

build/development metadata
  DESTSHARED and other config vars
    -> partially stale
```

Concrete example:

```text
DESTSHARED=/usr/local/lib/python3.14/lib-dynload
```

while the active extension directory was rooted under the relocated runtime prefix.

Frozen architectural distinction:

```text
runtime execution correctness
    !=
development metadata relocation correctness
```

## 7. Sysconfig path census

Extractor v2 passed regression self-checks and reported:

```text
absolute path records                 179
ANDROID_SYSTEM                          1
BUILD_PREFIX_RESIDUE                   25
OTHER_ABSOLUTE                         97
RUNTIME_PREFIX                         56
```

Build-prefix residue:

```text
25 records
12 unique /usr/local paths
21 metadata keys
all missing on tested device
```

The remaining missing `OTHER_ABSOLUTE` set was classified completely:

```text
BUILD_WORKSPACE_RESIDUE          58 records / 10 unique paths
TOOLCHAIN_RESIDUE                 8 records /  3 unique paths
USER_SCHEME_DESTINATION          16 records /  9 unique paths
HOST_BUILD_TOOL_RESIDUE           5 records /  1 unique path
TZDATA_SEARCH_PATH_METADATA       4 records /  4 unique paths

UNKNOWN                           0 records /  0 unique paths
```

Frozen claim:

> The tested sysconfig metadata surface contains real build/development residue, but the missing absolute-path set was fully classified and did not reveal an unknown live base-runtime dependency.

## 8. Timezone-data boundary

Base runtime scenarios:

```text
default configured TZPATH       FAIL
tzdata-only fallback            FAIL: package absent
explicit Termux zoneinfo path   FAIL: path absent
```

Representative keys:

```text
UTC
Asia/Seoul
America/New_York
```

all failed in the base-runtime data-source scenarios.

A non-mutating uv ephemeral environment then supplied only the first-party `tzdata` package while:

```text
PYTHONTZPATH=""
```

Observed:

```text
tzdata package found
zoneinfo.TZPATH=[]
UTC                  PASS
Asia/Seoul           PASS
America/New_York     PASS
all_keys_pass=true
```

Frozen claim:

> The base runtime has a timezone-data source gap, but CPython's first-party `tzdata` package fallback works on the tested target without modifying the frozen base runtime prefix.

Stage 3-A does not decide whether Stage 3-C should bundle `tzdata`, declare it as a dependency, or integrate a host TZif tree.

## 9. CA trust boundary

Observed matrix:

```text
clean launcher environment    PASS  HTTPS 200
explicit Termux CA            PASS  HTTPS 200
missing SSL_CERT_FILE path    PASS  repaired to Termux CA
existing empty regular file   FAIL  certificate verification error
```

Frozen launcher CA contract:

```text
existing SSL_CERT_FILE points to regular file
    -> preserve caller choice

missing or unset SSL_CERT_FILE
    -> discover Termux CA candidate

existing but unusable regular file
    -> preserve caller choice
    -> HTTPS may fail
```

Frozen claim:

> The launcher performs CA path-level discovery and repair, not semantic validation of CA bundle contents.

This clarifies earlier shorthand that said the launcher preserved a "valid" CA file.

## 10. Representative runtime audit

A Python audit-hook workload observed:

```text
path events      26
special events    5
```

Unique observed path classes:

```text
DEVFS            1
HOME_STATE       1
RESULT_OUTPUT    8
RUNTIME_PREFIX  13
TERMUX_TEMP      1
```

Exact-row review classified the external observations as:

```text
/dev/null
    normal device boundary

project experiment directory under $HOME
    probe-code location, not generic home-state dependency

$PREFIX/tmp/<temporary path>
    host temporary-storage integration

libc.so
    already-characterized Android native boundary

network :443
    deliberate HTTPS workload

file / uname
    optional platform-information helper commands
```

Frozen claim:

> Every exact path and special event observed in the representative Python-level audit workload was classified, and no new unknown broad host dependency boundary remained in that observed set.

Limitation:

> Python audit hooks are not a complete syscall trace and do not prove the absence of all possible native-library filesystem accesses or workload-specific dependencies.

## 11. Final production smoke reconfirmation

The canonical production-shape smoke passed after Stage 3-A tooling and analysis:

```text
base runtime             PASS
native imports           PASS
HTTPS                    200
subprocess re-entry      PASS
uv venv                  PASS
venv identity            PASS
uv run                   PASS

STAGE2C_SMOKE=PASS
```

The tested uv venv preserved:

```text
sys.prefix      = venv path
sys.base_prefix = frozen runtime prefix
```

and uv run preserved the frozen runtime prefix as the base of the ephemeral environment.

## 12. Final production relocation reconfirmation

The canonical runtime was:

```text
copied to A
validated at A
moved as a whole from A to B
validated at B
```

At both A and B the harness validated:

```text
sys.executable
sys.prefix
sys.base_prefix
sys.path
active sysconfig.get_paths()
HTTPS
subprocess child identity
fresh uv venv
fresh venv base_prefix
uv run
uv run base_prefix
```

Observed final markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

Frozen relocation claim:

> The tested production-shape runtime prefix can be relocated as a unit. After an A-to-B move, active runtime identity, active sysconfig paths, subprocess identity, fresh venv base identity, and uv run base identity all re-rooted at B, with the tested stale-A runtime assertions passing.

Not tested:

> Survival of an already-created external venv across movement of its base runtime remains outside the frozen Stage 3-A claim.

## 13. Acceptance checklist

Stage 3-A acceptance conditions:

```text
[x] every runtime-prefix path inventoried
[x] every ELF object inventoried
[x] every DT_NEEDED edge represented
[x] internal dependency resolution explicit
[x] Android-system dependencies explicitly classified
[x] Android-system SONAME loadability probed
[x] Termux host integration dependencies explicitly classified
[x] unresolved native edges = 0
[x] Python runtime identity captured
[x] extension-module import surface probed
[x] sysconfig metadata residue classified
[x] timezone-data boundary characterized
[x] CA trust boundary characterized
[x] representative audit rows classified
[x] Stage 2-C smoke reconfirmed
[x] whole-prefix production relocation reconfirmed
```

Result:

```text
STAGE3A=FROZEN
```

## 14. What Stage 3-A does not decide

Stage 3-A does not define:

```text
final archive layout
installer semantics
runtime versus development archive split
license bundle layout
manifest schema for release consumers
CA bundle packaging policy
whether tzdata is bundled or declared
multi-ABI release matrix
multi-API-level release matrix
uv-managed Python distribution metadata
release signing
SBOM generation
```

Those belong to later Stage 3 work.

## 15. Stage 3-B handoff

The next active stage is Stage 3-B: reproducible build-input promotion.

Stage 3-A found that the runtime execution closure is strong, while the current build/development metadata still remembers:

```text
upstream build workspace paths
macOS NDK toolchain paths
/usr/local build-prefix paths
host build tools
```

Stage 3-B must now answer:

> Can the current launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths?

The runtime closure is now a frozen constraint on that work, not a reason to redesign the launcher.
