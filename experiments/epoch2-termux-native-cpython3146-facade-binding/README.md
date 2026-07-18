# E2-P2 Termux-native CPython 3.14.6 façade binding

> **Status:** FROZEN producer binding; real façade execution not yet accepted

This experiment binds the stable standalone façade to the exact Termux-native CPython 3.14.6 producer authority frozen at `d1f19039af727344c77f2d0fac0806553da86bcc`.

The binding replaces the Stage 3-B workstation routing with exact private-authority acquisition and reconstruction of:

```text
runtime-base + development-addon
```

The `test-addon` is preserved in authority storage and build outputs but is not part of the E2-P1 package input.

The historical Gate 1 verifier and custom-NDK provenance audit remain unchanged. The current verifier adjudicates only their exact expected failure sets after the explicit binding transition.

This gate does not execute the real stable `build` or `package` operations and does not claim a real E2-P1 envelope, qualification, selectability, publication, or transition behavior.
