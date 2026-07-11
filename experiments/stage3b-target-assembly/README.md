# Stage 3-B Phase 4.3: Promoted Runtime Assembly

Run this phase on Termux after synchronizing the canonical Victor `out/` tree.

The candidate is isolated at:

```text
work/termux/stage3b-promoted-runtime/prefix
```

It does not overwrite the frozen Stage 2-C / Stage 3-A runtime tree.

Workflow:

```sh
git pull --ff-only
bash scripts/sync/pull-out.sh
bash experiments/stage3b-target-assembly/prepare-promoted-runtime.sh
```

The canonical assembler verifies the synchronized package against `SHA256SUMS`, extracts the upstream `prefix/`, creates `prefix/bin`, installs the promoted launcher, and creates the `python3` and `python` symlinks.

Expected marker:

```text
STAGE3B_PROMOTED_RUNTIME_ASSEMBLY=PASS
```

This marker proves assembly only. Runtime behavior and Stage 3-A closure equivalence remain later gates.
