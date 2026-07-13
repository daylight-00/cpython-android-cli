# Stage 3-C Phase 5 Gate 3C Addon Lifecycle Acceptance Result

> **Status:** FROZEN PASS — independently inspected corrected Termux authority

## Authoritative result

```text
archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst

archive sha256
  43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a

archive size
  23,994,806 bytes

archive members
  801

regular / directories / symlinks / hardlinks / special / unsafe
  732 / 69 / 0 / 0 / 0 / 0

result-tree-safety sha256
  ab338579025da63dec1750e3a7649c9a5f260cd4556f60ab3b3ade6140187bb9

root result-index sha256
  fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c

root indexed files
  731/731 exact
```

The archive was downloaded from the exact user-to-agent Drive work folder and independently reopened. The external SHA-256 matched the uploaded sidecar. Every archive member was checked for absolute paths, parent traversal, links, and special types before extraction.

## Target acceptance

```text
design verification
  73/73 PASS

target scenarios
  50/50 PASS

independent repository verifier
  103/103 PASS

external acceptance audit
  27/27 PASS

workflow / wrapper
  rc 0 / rc 0
```

Scenario groups:

```text
preflight rejection       10/10
composition and repair    10/10
addon uninstall             9/9
crash recovery             12/12
lock exclusion               2/2
behavior and final audit     7/7
```

## Raw-process cross-check

```text
process JSON records       127
stdout / stderr files      129 / 129
output/result comparisons  108

return-code distribution
  rc 0    100
  rc 44    15
  rc 90     4
  rc 92     4
  rc 93     4
```

The external audit independently confirmed the ten preflight rc 44 rejections, two lock-contention rc 44 rejections, the preserved-residual collision rejection, and all twelve crash return codes from the matrix. It also checked every indexed regular file's path, size, mode, and SHA-256 against extracted bytes.

## Accepted product properties

Gate 3C now accepts the frozen addon lifecycle and dependency contract:

```text
development-addon prerequisite
  exact runtime-base only

test-addon prerequisite
  exact runtime-base only

inter-addon dependency
  none

install orders
  runtime -> development -> test
  runtime -> test -> development

addon-removal orders
  remove test first
  remove development first

runtime-base removal while any addon is installed
  rejected before mutation
```

The target evidence proves exact registry and ownership transitions, addon repair, collision rejection, preserve-and-report addon uninstall behavior, accepted rollback tombstone semantics, committed cleanup, `test.support`, selected offline CPython tests, and the complete frozen runtime regression after both addons are removed.

## Archive-integrity correction closure

The first target archive remains immutable non-accepting diagnostic evidence. The corrected archive contains no symlinks or special entries, excludes the transient B06 venv, passes the pre-archive safety report, and has exact root-index membership. The two first-run blockers are therefore closed without changing the transaction engine, artifact manifests, matrix, registry schema, or recovery policy.

## Repository identity

```text
applied correction commit on target
  6dd398961a89c2fc4a60a705087f398e3c2c9287

accepted repository tree
  581623d6622f4919d790b296ec89f53dc9b6385e
```

The applied commit SHA is target-session-specific because `git am` creates a new committer identity and timestamp. The tree identity is the content authority.

## Claim boundary

This result closes Gate 3C addon lifecycle and dependency enforcement only. It does not prove the final multi-artifact/runtime-base uninstall boundary, upgrade, or downgrade. Gate 3D must separately integrate the already frozen runtime-base preserve-and-report behavior with a complete composed-product teardown and final ownership/residual audit. Gate 4 remains deferred until a second complete frozen product identity exists.
