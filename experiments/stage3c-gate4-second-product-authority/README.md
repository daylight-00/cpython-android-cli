# Gate 4 Second-Product Authority

This directory contains the authority-acquisition work that must finish before any cross-version transition design.

## Current state

```text
A1 selection and design          DESIGN FROZEN — input capture pending
A2 input capture                pending
A3 upstream replay              pending
A4 three-artifact materialize   pending
A5 standalone Termux validate   pending
A6 independent freeze           pending
```

Selected second product:

```text
CPython 3.14.5
v3.14.5
5607950ef232dad16d75c0cf53101d9649d89115
aarch64-linux-android / API 24 / NDK 27.3.13750724
```

Run the repository design verifier:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-second-product-authority-design.sh
```

A design PASS is not a second-product or Gate 4 target PASS. The next operation is exact source/producer/dependency/toolchain input capture.
