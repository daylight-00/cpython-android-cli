# Epoch 2 Research Conclusions

> **Status:** verified research set  
> **Date:** 2026-07-18  
> **Authority:** research guidance only; these documents do not redesign Epoch 3 or authorize publication

This directory records three independently verified conclusions produced from the Epoch 2 project review.

## Reading order

1. [CPython 3.14/3.15 across Android API levels 24 and 29–36](E2_CPYTHON_ANDROID_API_LEVEL_MATRIX.md)
   - separates compile-time API floor, runtime Android release, and runtime kernel;
   - identifies API 29, 31, and 34 as the most relevant CPython thresholds;
   - defines the bounded API-36 experiment.

2. [Upstream provenance and standalone distribution models](E2_UPSTREAM_PROVENANCE_AND_STANDALONE_MODELS.md)
   - separates CPython/Python.org, BeeWare, this project, Astral, and uv responsibilities;
   - confirms that the main future product should consume the official CPython Android package;
   - treats Astral as the standalone product-form reference rather than the Android binary upstream.

3. [Epoch 2 research scope review and direction](E2_RESEARCH_SCOPE_AND_DIRECTION.md)
   - evaluates the current repository as an experiment and evidence incubator;
   - incorporates the accepted real-Termux E2-P3 result;
   - identifies completed questions, work to pause, and fundamental experiments still required;
   - keeps Epoch 2 focused on Android adaptation evidence without designing Epoch 3.

## Shared conclusion

The future main distribution should be an upstream-derived, Astral-like standalone adaptation. The current repository should finish the unresolved Android-specific research needed to support that later product while preserving source reconstruction and API-36 work as bounded experiments.

The current priority is the remaining `termux-emulator` qualification and combined E2-P3 closure, followed by direct upstream-artifact adaptation, update portability, Python 3.15 preview work, API-36 comparison, minimum-floor and 16 KB compatibility, native-extension capability, host-profile separation, license provenance, and uv consumer requirements.
