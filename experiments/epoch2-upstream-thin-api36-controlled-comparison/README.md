# E2-R1/API36-1 — Controlled source-equivalent comparison

This authority compares three bounded aarch64 Android CPython 3.14.6 control classes: exact official API-24 bytes, an API-36 rebuild using the exact six dependency release assets pinned by the CPython 3.14.6 Android builder under hard URL, filename, SHA-256, and size binding, and an API-36 rebuild of the same pinned dependency source tags and recipes under an Android-sysroot-only host-isolation contract with artifact-aware shared-ELF and static-archive validation. The compile API is the intended variable; every additional producer, timestamp, source-dependency, prepopulation-path, and measurement-normalization delta is enumerated.

The comparison supplies Epoch 2 closure evidence. It does not select an Epoch 3 input, establish a minimum supported Android release, qualify 16 KiB runtime devices, authorize publication, or make the rebuilt controls selectable products.
