# E2-R1/UT-3 — Sysconfig and native-extension SDK

This experiment converts the official binary-derived CPython 3.14.6 Android metadata from producer records into a relocation-aware consumer view and proves a real Android native-extension wheel build, venv installation, import, whole-prefix movement, fresh relocated venv installation, and import.

The active sysconfig module derives runtime paths from its own location. The installed Makefile derives `prefix` from `MAKEFILE_LIST`; pkg-config files derive it from `pcfiledir`; build-details and the auxiliary sysconfig JSON use explicit relative path semantics. Producer NDK, workspace, and `/usr/local` values are frozen in the baseline census and removed from active consumer metadata.

The accepted on-device SDK profile uses `clang`, `clang++`, and `llvm-ar` in the Android/Termux execution context. A separate runtime-only representation is required. A workstation cross-build SDK remains unavailable until an explicit relocatable NDK/sysroot authority exists.

The wheel artifact remains in the result receipt and is not committed. This authority does not select an Epoch 3 product, qualify broad devices, make the product selectable, or publish artifacts.
