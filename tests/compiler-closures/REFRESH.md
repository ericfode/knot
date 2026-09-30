# Closure refresh, 2026-09-29

The refresh starts from `a1d68911` on `campaign/closures`. Its 32 new edge
programs have independent expectations in `refresh.json`; the original 42
fixtures, 292 calls, probes, regressions, laws and mutants are unchanged.

`refresh_seed.py --write` froze 32 checks, 64 native/Bun build observations and
40 executed seed calls: 20 accepted programs and 12 source rejections. The
accepted programs have literal Flag results in both seed lanes. An IO wrapper
prints the observed Flag in native builds without changing the tested source.
The rejected programs fail checking and both build lanes with the same exact
diagnostic. Host/build faults do not count as source rejections.

The edges cover reversed capture references, captured functions and higher-order
arguments, lexical shadowing, lambda lets, staged partial calls, discarded
function arguments, empty application, function fields, nested returned
closures, erased captures, promoted captures and distinct arrow domains.
Negative controls cover reusable/erased function values, affine reuse, arrow
result mismatches, overapplication, match eligibility and unresolved names in
erased or discarded lambda bodies.

Replay the frozen observations with:

```sh
export BEND_NO_TELEMETRY=1
python3 -B tests/compiler-closures/refresh_seed.py
```

Use a task-local TMPDIR for direct native seed builds. On this macOS host the
seed's clang probe intermittently failed through `/usr/bin/clang`. Resolving the
actual Xcode compiler and SDK, with a local cached version response, completed
the freeze. A missing SDK was a host/build fault, not a source verdict.

The closure differential gate now includes every refresh source in both Knot
lanes and replays both seed lanes first. It preserves the original assertions.
The decision audit and complete gate results are recorded in
[`closures-refresh.md`](../../docs/compiler-campaign/closures-refresh.md).
Live Perch, integrating main and refreshing shared receipts belong to the
coordinator under this executor's explicit restrictions.
