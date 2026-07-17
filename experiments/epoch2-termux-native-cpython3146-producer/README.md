# E2-P2 Termux-native CPython 3.14.6 producer

This experiment opens a producer authority for rebuilding the pinned CPython
3.14.6 Android product directly in Termux.

It is a new authority. It does not rename the frozen Stage 3-B Linux producer,
and it does not treat matching NDK release numbers as matching compiler bytes.

The first bounded operation is `preflight.py`. It verifies the reacquired
Stage 3-B source and product lock, the tracked dependency lock, the current
custom NDK identities, the ephemeral lld patch, the retained 3.14.5 shell
adapter, host API probe mappings, SDK availability, tools, and storage.

The 3.14.5 authority contributes only proven host-execution techniques:

- route only implicit `subprocess.run(shell=True)` calls through Termux bash;
- apply build-Python configure-cache negatives only from bounded evidence;
- patch lld only in an ephemeral overlay;
- use clean source, dependency, build, output, and result roots;
- verify the candidate on Android before freezing it.

The 3.14.5 source, OpenSSL 3.0.20 input, package hashes, runtime fingerprint,
and acceptance decisions are not inputs to the 3.14.6 product.

After a successful preflight, the next operation is a clean 3.14.6 replay
candidate. A façade producer-binding change remains a later, independently
reviewed transaction.

## Legacy cache exception

The initial profile distinguishes six source-mapped negative cache variables
from one historically proven inert entry, `ac_cv_func_setpwent=no`. The latter
is restricted to build-Python configuration and does not imply a
`HAVE_SETPWENT` source mapping. Dynamic additions remain mapping-gated.
