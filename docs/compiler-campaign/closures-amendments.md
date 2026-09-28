# Closures: expectation amendment before implementation

Pinned seed Bend 2.0.29 (`574b6d39a235b539eb19a5c532993a0abb3d11ad`):

```sh
BEND_NO_TELEMETRY=1 bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts tests/compiler-structural/fixtures/function-field.bend
```

Exit 0, stdout `On{}`. The fixture has an affine `Flag -> Flag` field
inside a `Type` datatype. This is accepted by the seed and required by
`closure-field` and `closure-list` in the frozen closure suite.

Amended pin: **structural/function-field** only. The catalog must accept the
field, retaining its literal span `58:59:5:6`, quantity 1, and the first
interned function type (id 2, after Flag and Box). The structural observer
continues to list source datatype declarations; interned arrows are type
identities, not extra source declarations. The default enum compiler still
reports `Unsupported check constructor-fields`, matching the suite's other
fielded cases. The explicit fields compiler and closure gate establish
execution with the seed result.

No fixture source or seed observation changes. This checkpoint precedes
implementation; the catalog assertion is expected to fail until function types
land. The scan of existing registered suites found no other closure-conflicting
pin. `compiler-nest/closure-parameter` and `compiler-generics/closure-apply`
belong to their owning suites and remain unchanged. Their function-type
Unsupported pins require coordinator reconciliation when those gates land.
