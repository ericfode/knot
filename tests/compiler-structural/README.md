# Constructor field declaration gate

```sh
python3 tests/compiler-structural/check.py
bun tests/compiler-structural/trust.ts
```

The gate compiles the Bend catalog observer and actual compiler to native and
Bun. Sixteen fixed fixtures compare against the pinned seed and literal expected
catalog/error observations. Valid field declarations remain Unsupported by the
compiler, and all rejected compilations preserve a preexisting output artifact.
The native/Bun boundary pairs distinguish accepted 256-field metadata from
257-field catalog exhaustion, using parser depth 4096 to reach that boundary.

Seven semantic mutants remain parseable/type-correct before unchanged assertions
reject them. The proof entry checks five new laws plus the previous 18. Exact
commands, source hashes, observations and mutants are in
[receipts/catalog.json](receipts/catalog.json).

`observe.bend` renders the real catalog without checking bodies; its success
record is `Catalogued`. The Python driver only creates test inputs, invokes
tools and compares observations. It contains no Bend parser, checker or evaluator.
This gate establishes no field execution, recursive-function support, owned
heap, self-hosting or GPU result. See the
[contract](../../research/compiler-structural/SPEC.md) and
[review packet](../../research/compiler-structural/LAW_REVIEW.md).
