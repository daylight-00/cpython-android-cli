# Stage 3-B Phase 1 Final: Current Producer Provenance Reconstruction

> **Status:** FROZEN
> **Stage:** 3-B Phase 1
> **Result:** PASS

## Question

> Is enough producer identity available to begin a controlled clean replay of the current Android CPython producer graph?

## Result

Observed lineage analysis:

```text
phase2_ready=true
remaining_gates=[]
```

Producer structure checks:

```text
CONFIG_ARGS structure   PASS
CFLAGS structure        PASS
LDFLAGS structure       PASS
```

Dependency declaration checks:

```text
bzip2   1.0.8-3   MATCH
libffi  3.4.4-3   MATCH
openssl 3.5.7-0   MATCH
sqlite  3.50.4-0  MATCH
xz      5.4.6-1   MATCH
zstd    1.5.7-2   MATCH
```

NDK identity:

```text
preserved snapshot       27.3.13750724
embedded prefix metadata 27.3.13750724
active Linux compiler    27.3.13750724

snapshot vs embedded     MATCH
snapshot vs active       MATCH
```

Source identity gate:

```text
exact_cpython_source_git_identity_available=true
```

Historical evidence inventory:

```text
historical_build_evidence_file_count=2
```

## Producer lineage model

The current consumed development prefix contains macOS producer metadata:

```text
BUILD_GNU_TYPE=aarch64-apple-darwin24.6.0
NDK prebuilt host=darwin-x86_64
workspace=/Users/runner/work/release-tools/...
```

The active replay workstation is Linux.

Stage 3-B therefore does not define success as reproducing producer-host absolute strings.

The replay acceptance model is:

```text
same exact CPython source identity
same preserved producer script model
same dependency release-tag model
same NDK release
same Android target/API intent
    -> clean Linux replay
    -> closure and behavior comparison against frozen Stage 3-A
```

## Frozen Phase 1 conclusion

The following gates are closed:

```text
[x] exact CPython source Git identity available
[x] six dependency release tags recovered and matched
[x] CONFIG_ARGS producer structure matched
[x] CFLAGS producer structure matched
[x] LDFLAGS producer structure matched
[x] preserved, embedded, and active NDK versions matched
[x] macOS producer lineage identified from embedded metadata
[x] exact unknowns separated from structural producer evidence
```

Result:

```text
STAGE3B_PHASE1=FROZEN
STAGE3B_PHASE2_READY=true
```

## Remaining historical unknowns

These do not block a controlled producer replay:

```text
exact historical workflow run ID
exact historical workflow job ID
exact release-tools repository commit
exact shell transcript
exact dependency archive hashes from the original run
exact original artifact transfer chain
```

They remain provenance questions, but the current source/toolchain/dependency/configuration gates are sufficient for a clean replay experiment.

## Handoff

Proceed to Stage 3-B Phase 2:

> Build the exact identified CPython source commit through the preserved Android producer model on Linux, using NDK 27.3.13750724 and the declared dependency release tags, without mutating the original source checkout or historical prefixes.
