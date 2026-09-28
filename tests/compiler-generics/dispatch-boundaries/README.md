# Dispatch boundary fixtures

These nine fixtures freeze type-level local bindings and values in otherwise
monomorphic programs, the same forms under generic dispatch, and two malformed
type applications. The seed-derived expectations were written before the
corresponding boundary repair. Existing generics, supplemental and boundary
corpora remain unchanged. The first four dispatch cases and their observations
are preserved exactly when adding the four controls. A final inferred alias of
a rigid type parameter was frozen before adding the inferred-binding guard;
all eight preceding cases and seed observations stayed unchanged.

The checker must report Unsupported for all seven seed-valid fixtures, including
an erased local type alias nested in a match arm. It must preserve this outcome
when no top-level declaration carries generic syntax. An unannotated type-valued
name still denotes its declared datatype and must not become an invalid free
name. The same lexical-name fallback is required under generic dispatch.

The empty `Flag<>` field annotation is pinned Invalid at parse/type-arguments.
The nonempty `Flag<Flag>` annotation in a monomorphic field is pinned Unsupported
at check/type-expression. Both are seed-invalid and must never cause an internal
failure or produce an artifact.

`expectations.json` contains seven valid seed checks, two seed rejections and nine
enum entry calls. Knot phase/code pins are reviewed boundary requirements; values
and tags come only from the pinned seed interpreter and constructor declaration
order. The regeneration adapter reuses the original seed-only script unchanged.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/dispatch-boundaries/regen.py
```

This directory is separate from the earlier boundary corpus. None of its
expectations comes from Knot output.
