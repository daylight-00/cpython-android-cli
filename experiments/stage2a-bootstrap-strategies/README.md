# Stage 2 Starter

Stage 2 begins from the frozen Stage 1-B B0 frontend.

The external Stage 1-B runtime contract is:

```text
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

This starter compares three strategies for reducing that external contract.

## Variants

### S2-E: setenv-only control

The launcher:

1. discovers its executable through `/proc/self/exe`,
2. derives `<prefix>` from `<prefix>/bin/<launcher>`,
3. sets `LD_LIBRARY_PATH`,
4. discovers and sets the Termux CA bundle,
5. enters the B0 PyConfig initialization path.

This is a control experiment. It measures whether changing the process environment alone is sufficient for extension-module dependency loading.

### S2-U: bionic linker update

The launcher:

1. self-locates,
2. dynamically resolves `android_update_LD_LIBRARY_PATH`,
3. updates the running process linker search path,
4. mirrors the resulting path into the environment,
5. configures the CA bundle,
6. enters B0.

This is an Android-specific experiment.

### S2-R: self re-exec

The launcher:

1. self-locates,
2. sets `LD_LIBRARY_PATH`,
3. sets `SSL_CERT_FILE`,
4. re-execs `/proc/self/exe` with the original `argv`,
5. removes the private recursion guard,
6. enters B0.

This uses process restart so the dynamic linker sees the environment at program start.

## Build

```sh
source ~/tmp/260704/env.sh

cd ~/tmp/260704/stage2

DEV_PREFIX="$HOME/tmp/260703/android-python-work/prefix" \
./build-stage2.sh
```

Copy these four launchers to Termux:

```text
python-pyconfig-auto
python-s2-setenv
python-s2-linker-update
python-s2-reexec
```

Prepare a pristine comparison prefix:

```sh
./prepare-stage2-pristine.sh
source ~/tmp/260704/stage2/pristine-test/STAGE2_TEST_PREFIX.env
./stage2-compare.sh
```

## Decision rule

Do not select a Stage 2 strategy only because the base interpreter imports `ssl`.

A candidate must preserve:

- native stdlib imports,
- HTTPS trust,
- subprocess re-entry,
- uv venv,
- venv identity and native imports,
- uv run.

The initial purpose is measurement, not premature final architecture selection.
