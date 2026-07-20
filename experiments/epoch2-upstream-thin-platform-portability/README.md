# E2-R1/UT-6 — Platform portability

This authority separates directly tested platform behavior, static 16 KiB ELF compatibility, related historical evidence, and explicitly withheld claims. The current assembled product is directly qualified only in the recorded Termux/aarch64 Android target context.

The official package's API-24 identity is not treated as runtime proof. The minimum release API remains withheld because no direct current-assembly lower-API target was available. Static 16 KiB-compatible PT_LOAD layout is accepted; runtime operation on a 16 KiB device is accepted only when directly observed. Non-Termux app namespaces, ADB, root, emulator, other ABIs, and broad device/version claims remain withheld.

This evidence enables Epoch 3 platform decisions. It does not select a minimum API, make a broad device claim, select an Epoch 3 product, make the product selectable, or authorize publication.
