# Current Project Context

> **Current epoch:** Epoch 2
> **Current phase:** E2-P0 — documentation and component-boundary foundation
> **Frozen predecessor:** Epoch 1 through Stage 3-F
> **Predecessor commit:** `e1de252740a96c40f3d587269136235a2c84ea16`
> **Primary target:** Android/Bionic arm64, `aarch64-linux-android`, initially API 24+
> **Primary execution profile:** `termux-cli`

## Active objective

Define the standalone product, installer-consumer boundary, repository topology, terminology, and migration sequence before moving implementation files.

This phase is additive documentation and directory-boundary work. It does not change the launcher, CPython build, native closure, archives, installation lifecycle, uv behavior, publication artifacts, target evidence, or any frozen Epoch 1 authority.

## Product direction

```text
upstream CPython Android source and release model
        -> Android/Bionic standalone CPython product
        -> canonical archives, metadata, checksums, and qualification
        -> installer and lifecycle manager
        -> Termux CLI users
        -> pip, venv, uv run, uv tool, and Python CLI packages
```

The product is Termux-first because Termux is the practical mainstream Bionic-native interactive shell environment. The standalone core must not require Termux application-private absolute paths or Termux package libraries as binary identity.

## Immediate reading path

1. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
2. [`roadmap/EPOCH2_ROADMAP.md`](roadmap/EPOCH2_ROADMAP.md)
3. [`architecture/COMPONENT_OWNERSHIP.md`](architecture/COMPONENT_OWNERSHIP.md)
4. [`decisions/`](decisions/)
5. [`references/`](references/)
6. [`epochs/EPOCH1_CLOSURE.md`](epochs/EPOCH1_CLOSURE.md)
7. [`PROJECT_CONTEXT_STAGE3F.md`](PROJECT_CONTEXT_STAGE3F.md) when exact predecessor authority is required

## Next bounded phase

E2-P1 defines the canonical standalone archive and metadata contract. No producer or installer code moves until that contract has explicit inputs, outputs, non-goals, and acceptance checks.
