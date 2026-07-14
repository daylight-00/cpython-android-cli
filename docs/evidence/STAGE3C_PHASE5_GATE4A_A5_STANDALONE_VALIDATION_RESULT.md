# Stage 3-C Phase 5 Gate 4A A5 Standalone Validation Result

> **Status:** A5 FROZEN PASS
> **Product:** CPython 3.14.5 / android24 / aarch64
> **Next boundary:** A6 independent archive audit and freeze

## Preserved v1 failure

The first A5 result remains immutable:

```text
archive sha256  783dbbbea38b338f2c337cda0bc8cac8ed9d042a5dbabd08db7a061d67b48072
archive size    100,956
candidate rc    61
verifier rc     71
```

Independent diagnosis passed 18/18 checks and isolated two harness defects:

1. A normal `sysconfig["data"] == prefix` value was rejected by a descendant-only assertion.
2. Inline `-c` was passed as a uv option instead of as an executed script command.

The original FAIL is retained as evidence and is not relabeled as a PASS.

## Accepted corrected result

```text
archive
  20260714-gate4a-a5-standalone-validation-v2-results-20260714T124248Z.tar.zst

size
  101,148 bytes

sha256
  851026d08d18dcef03b30d7ccf3f437a8712ba5cbdecde5e9d4478ba996ecc76

result index
  734/734 exact

candidate
  10/10 PASS

archived verifier
  41/41 PASS

A6 independent input audit
  34/34 PASS
```

The result contains 225 recorded commands: 218 expected rc 0 commands, four dependency-guard or lock-exclusion rc 44 commands, and one each of the accepted PREPARED rc 90, COMMITTED rc 92, and late APPLYING rc 93 crash boundaries.

## Accepted target behavior

A5 validated fresh standalone and composed installations for:

```text
runtime identity, CLI and PyConfig
67/67 native extension imports
ELF needed closure and external SONAME dlopen
HTTPS trust repair and regular-file preservation
first-party tzdata fallback
subprocess
stdlib venv, uv venv and uv run with an explicit interpreter
whole-prefix relocation
both addon installation orders
both addon removal orders
development C-extension compile/import
selected offline test_json and test_hashlib execution
runtime dependency guard
same-version noop and repair
preserve-and-report ownership
PREPARED/APPLYING/COMMITTED recovery
lock exclusion
complete teardown
```

No upgrade, downgrade, migration, or mixed-version command was executed.

## Claim boundary

A5 accepts standalone CPython 3.14.5 target behavior for the exact A4 artifact set. It does not freeze the complete second-product authority by itself and does not accept any transition behavior. A6 remains required.
