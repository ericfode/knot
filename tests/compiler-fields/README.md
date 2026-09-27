# Structural term gate

Run from the repository root:

```sh
python3 tests/compiler-fields/check.py
bun tests/compiler-fields/trust.ts
```

`cases.json` freezes seed outcomes, checker diagnostics/core slices, live-field
value observations and compiler capability failures. The harness builds native
and Bun variants; it never implements source semantics. `bounds.bend` observes
4095/4096 lexical capacity and exact inspection work/character limits. Ordinary
checker/evaluator budget pairs reach the first successful budget and its neighbor.
The shared-tree seed control is check-only and tests explicit inspection exhaustion.

Nine isolated mutants must parse and typecheck, then differ from unchanged
observations for their intended semantic reason. Harness timeouts/build errors
do not count. All inputs, commands, generated hashes and outcomes are recorded
in `receipts/fields.json`. The trusted seed closure is separately inventoried
under `research/compiler-fields/receipts/trust.json`.

See the [contract](../../research/compiler-fields/SPEC.md) and
[law packet](../../research/compiler-fields/LAW_REVIEW.md) for proof boundaries,
projection differences, unsupported capabilities and the owning-runtime gap.
