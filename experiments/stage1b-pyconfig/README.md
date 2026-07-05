# Stage 1-B Starter

This directory starts the Stage 1-B PyConfig frontend experiment.

## Variants

- `stage1a`: frozen `Py_BytesMain` baseline.
- `b0-auto`: `PyConfig` initialization without overriding `config.home`.
- `b1-home`: `PyConfig` initialization with `config.home` from `CPYTHON_HOME`.

The Stage 1-A runtime integration remains unchanged:

```sh
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

Stage 1-B does not attempt to solve native linker lookup or CA trust through PyConfig.

## Host build

```sh
source ~/tmp/260704/env.sh
cd ~/tmp/260704/stage1b
./build-stage1b.sh
```

Copy the resulting launchers into the Termux test prefix:

```text
<prefix>/bin/python-pyconfig-auto
<prefix>/bin/python-pyconfig-home
```

## Termux comparison

```sh
./stage1b-compare.sh
```

The experiment is successful when B0 and B1 can be compared against the Stage 1-A baseline using the same runtime contract and uv workflows.

A B1 failure in venv identity is useful evidence: it would show that forcing `config.home` changes semantics that B0 preserves.
