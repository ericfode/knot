# Enum-profile resolver and checker gate

Run `python3 tests/compiler-checker/check.py` from the repository root. The gate
builds `src/check-cli.bend` for Bun and native, checks the complete frontend plus
checker proof entry, and writes `receipts/checker.json` with source/tool/generated
hashes and commands. Build products and mutant copies remain ignored under
`.local/compiler-checker/gate/`.

The 49 cases combine the earlier 14 parser fixtures with 35 semantic controls.
They have literal reference outcomes and exact resolved-term expectations in
`cases.json`; `make-manifest.py` only serializes those reviewed literals. It does
not learn expected output from Knot. Seventeen cases check successfully, thirty
are Invalid and two are Unsupported. Duplicate arms are accepted by the seed but
excluded from this profile; repeated parameter names are supported shadowing.

Two execution lanes give 98 semantic observations. Ten CLI depth observations
include Flag's failing depth 3 and successful depth 4. Eight catalog-bound
observations per lane exercise 256/257 entries for each bounded collection.
Seven deliberately wrong, type-correct implementations fail unchanged semantic
expectations. The harness contains no parser, resolver, checker, evaluator or
emitter implementation.

The CLI is an inspection checkpoint. `Checked` means all function bodies passed
this profile's checker. No Wasm is emitted and no source value is evaluated by
Knot yet. See `src/SPEC.md` and `research/compiler-checker/LAW_REVIEW.md` for bounds,
semantics, evidence distinctions and remaining limits.
