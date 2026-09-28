# Dispatch boundary fixtures

These nine fixtures freeze type-level local bindings and values in otherwise
monomorphic programs, the same forms under generic dispatch, and two malformed
type applications. Existing generics, supplemental and boundary corpora remain
unchanged.

**Provenance.** This corpus was committed in `f39ba7e`, together with the
boundary repairs it exercises. An earlier version of this README said that
the expectations were written before those repairs, that four controls were
added after the first four cases, and that the inferred alias was frozen
before the inferred-binding guard. Git history cannot show any of these
orderings, because every case appears first in that one commit.
`regen.py` reproduces the seed side. The Knot pins await the coordinator's
literal review ([BOUNDARY-PINS.md](../BOUNDARY-PINS.md)).

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
enum entry calls. The Knot phase/code pins are boundary requirements that the
implementer chose; their review is pending. Values and tags come only from the
pinned seed interpreter and constructor declaration order. The regeneration adapter reuses the original seed-only script unchanged.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/dispatch-boundaries/regen.py
```

This directory is separate from the earlier boundary corpus. Its seed
observations come only from the pinned seed. Its Knot phase/code pins were
chosen by the implementer in the same commit as the checker that emits them.
They are therefore not independent of Knot output until they are reviewed.
