# Stage 3-C Phase 5 Gate 4D Bidirectional Termux Validation Result

Gate 4D preserves both the complete v1 execution and the v2 corrective focused retest.

```text
v1  ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c  493427 bytes  1223/1223 index
v2  98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2  720554 bytes  529/529 index
```

The v1 run produced 55 unaffected PASS scenarios. H01-H08 failed only the original timezone/development probe assumptions; C11-C12 failed an invalid source-only collision expectation; A04 was derived. The v2 archive verifies v1, reruns H01-H08, replays C11-C12, derives A04, and independently verifies 66/66. Repository HEAD, tree, remote, and cleanliness remain unchanged throughout target validation.
