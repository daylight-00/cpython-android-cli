# Stage 3-D Gate 4 Consumer Integration Target Validation Result

> **Status:** TARGET EVIDENCE ACCEPTED — GATE 5 INDEPENDENT FREEZE

```text
work ID                  20260715-stage3d-gate4-consumer-integration-target-validation-v3
archive sha256           13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c
archive size             58525
safe archive members     757
self-index               697/697 exact
scenario results         48/48 expectation match
harness completion       48/48
independent verification 27/27 PASS
process records          150
uv                        0.11.28 (aarch64-linux-android)
```

## Accepted surface

```text
explicit find + venv reconfirmation  8/8
uv run exact-product execution       8/8
uv sync exact-product execution      8/8
bounded system discovery             8/8
whole-product transition continuity  4/4
precedence/negative/invariant        12/12
```

The accepted surface uses the exact absolute installed interpreter path and reprobes selected identity. Python downloads, network access, and managed-Python fallback are disabled. The result proves both CPython 3.14.5 and 3.14.6 across runtime-only, runtime+development, runtime+test, and full topologies. Transition continuity covers `uv python find`, `uv venv`, `uv run`, and `uv sync` before and after both frozen product directions.

Repository identity, authority inputs, global paths, uv managed-install state, and all seed products are byte-identical before and after execution. No transient workspace remains in the evidence archive.

## Correction lineage

The v1 archive is preserved with a 35/48 result. It exposed missing bounded `uv run` working directories and an independent-verifier failure path that could not serialize missing outcomes. The v2 archive is preserved with a 47/48 result. X05 legitimately selected the authoritative user-home `.venv` through physical working-directory ancestry because `--no-project` does not disable virtual-environment discovery.

The accepted v3 package retains all frozen repository, authority, product, evidence, contract, and matrix inputs. It changes only X05 isolation by adding uv's documented `--system` control while retaining `--no-managed-python`, `--no-project`, offline mode, an isolated HOME and managed directory, and a `/system/bin` PATH. X05 then fails with no eligible interpreter as expected.

## Frozen claim boundary

Gate 5 accepts the system-Python consumer-integration surface for the exact two-product, four-topology authority. It does not accept global interpreter links, shell integration, uv-managed Python registration, Python downloads, uv patching, registry or journal migration, third-product compatibility, or a general upstream uv Android-support claim.
