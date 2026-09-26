# Style comparison specimens

Three implementations of one contract: map each U32 `x` to `3*x+1` modulo
2^32, preserving list length and order. All expose
`solve(xs: List<&2,U32>) -> List<&2,U32>` and import only Base.

- `a.bend`: direct structural recursion.
- `b.bend`: a reusable mapping combinator with a specialized function argument.
- `c.bend`: accumulate in reverse order, then reverse once.

Neutral filenames avoid telling the model which implementation should win.
None is labeled a style defect or a correct aesthetic answer. The existing
frozen performance evaluator supplies independent compile, output and scaling
checks; it is not modified for this pilot.

```sh
python3 tests/perch-performance/evaluate.py --case growing-prefix-copy \
  --candidate tests/perch-style/a.bend --output .local/style/a.json
# Repeat for b.bend and c.bend with distinct output paths.

npm run lint:rank -- --live \
  --cohort='Map each U32 x to 3*x+1 modulo 2^32 over a reusable list, preserving length and order.' \
  tests/perch-style/a.bend::solve \
  tests/perch-style/b.bend::solve \
  tests/perch-style/c.bend::solve
```

The [pilot report](../../docs/perch-style.md) records results and limits.
