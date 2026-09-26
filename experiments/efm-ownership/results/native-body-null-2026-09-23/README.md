# Native body member is null

DCS PID 4992, 2026-09-23 local time. All 94 samples from object time 0 through 9.5 seconds report `fm_null`. The runtime type, Registered displacement, primary vtable RVA 0x1146200, both instruction signatures, and the member read passed. The member at complete woAIPlane +0x2f98 was zero. No body dereference or native state write occurred.

This narrows the previous generic rejection: the probe does reach the intended class/member, but this aircraft/configuration does not expose an AIAerodyneFM instance there during the observed interval. It does not establish that all aircraft use this path, that no other physical state exists, or that the member can safely be populated manually.

The position-comparison gate remains unmet. Next work is offline tracing of the member's initialization and the alternative update path used when it is null. Repeating this same mission unchanged will not resolve that question.
