# Frontend semantic review

2026-09-26: Perch 0.3.5 with `jev-1.13.0` answered all **282 checks in 47
requests**. No above-floor findings were reported. Raw probabilities, rule
selection, source hashes and bounded context metadata are retained in
[`receipts/perch.json`](receipts/perch.json).

The lexer, syntax helpers, inspection renderer, parser CLI, laws and proofs were
checked with the six shared Bend rules. The parser dispatcher `run` was checked
with fuel completeness, machine arithmetic, checker trust and pattern sharing.
Its helpers were supplied as bounded working-copy context. The self-contained
law packet received all eight law rules. All source/context file hashes matched
the current files when the receipt was assembled.

There are no findings to classify as confirmed, duplicate or false-positive.
Below-floor uncertainty remains in the recorded probabilities; this report does
not convert it into proof. Parser analysis does not resolve Base, constructor
arities or every dynamic callback. The complete pinned-seed checks and actual
native/Bun observations in `tests/subsets/receipts/frontend.json` are the
deterministic evidence for this checkpoint.

This review covers a parser increment. Semantic rejection, independent value
evaluation and Wasm generation remain unimplemented, and are not covered by
this report. The four checked laws are the boundary laws stated in
`LAW_REVIEW.md`; they do not establish general parser correctness.
