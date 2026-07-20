# E2-R1/UT-5 — Feature capability and product-surface qualification

This experiment classifies subprocess, venv, base-pip, uv-coexistence, console-script, and multiprocessing behavior on the selected official Android runtime. Every matrix entry has an evidence-backed disposition: `pass`, `android-mandatory-adaptation`, `missing-bionic-primitive`, `upstream-build-decision`, or `inadequate-environment`.

Passing probes are technical support candidates only. They do not select Epoch 3 inclusion. In particular, base pip, pip command wrappers, external uv, pre-existing venv relocation, `preexec_fn`, and multiprocessing primitives remain individually bounded. Default `/bin/sh` is not assumed; explicit Android shell behavior is recorded separately.

This authority enables feature-surface selection and platform qualification. It does not qualify broad devices, select an Epoch 3 product, make the product selectable, or publish artifacts.
