# Stage 2-B Starter

Stage 2-B refines the Stage 2-A winning strategy: self-location plus re-exec.

## R2 policy

The R2 launcher uses a condition instead of a recursion guard:

```text
discover /proc/self/exe
        |
derive prefix/lib
        |
is prefix/lib already an LD_LIBRARY_PATH component?
        |
        +-- no
        |    normalize environment
        |    configure CA
        |    execv(self, original argv)
        |
        +-- yes
             normalize duplicate required entries
             repair/discover CA if needed
             run B0 PyConfig directly
```

This gives a fixed point:

- top-level clean launch: one re-exec,
- inherited subprocess with correct loader environment: zero re-execs,
- wrong or missing loader environment: repaired and one re-exec,
- wrong/nonexistent CA path: repaired without re-exec when the loader path is already ready.

## Build

```sh
source ~/tmp/260704/env.sh

cd ~/tmp/260704/stage2b

DEV_PREFIX="$HOME/tmp/260703/android-python-work/prefix" \
./build-stage2b.sh
```

## Termux preparation

Place `python-s2-r2` beside the scripts, then:

```sh
./prepare-stage2b-pristine.sh

source \
  ~/tmp/260704/stage2b/pristine-test/STAGE2B_TEST_PREFIX.env
```

## Validation

```sh
./stage2b-validate.sh
```

Profiles:

- `clean`
- `ready`
- `wrong-ld`
- `wrong-ca`
- `duplicate`

Additional tests:

- unrelated working directory,
- invocation through an external symlink,
- subprocess re-entry,
- uv venv,
- clean launch through the venv interpreter,
- uv run.

## Relocation

After the main validator passes:

```sh
./stage2b-relocation.sh
```

This validates the same whole prefix at location A, then moves it to location B and repeats:

- native imports,
- HTTPS,
- subprocess re-entry,
- uv venv,
- clean venv launch,
- uv run.

## Decision rule

Stage 2-B is successful only if R2:

1. passes from a clean external environment,
2. does not grow duplicate required library-path entries across subprocesses,
3. repairs wrong inherited loader and CA settings,
4. preserves venv identity,
5. survives whole-prefix relocation,
6. preserves uv workflows after relocation.
