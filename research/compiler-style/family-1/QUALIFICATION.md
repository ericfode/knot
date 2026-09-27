# Compiler family 1: isolated qualification

Historical pre-integration report. The parent [acceptance](../STYLE_CAMPAIGN.md)
records the later full gates, review and reproducibility correction.

The immutable first candidate passes the bounded behavioral/backend gate. It is
not integrated or accepted. Perch and three-axis style review remain unrun.

## Candidate and reading judgment

`set_known` owns one binding-list traversal and one metadata reconstruction.
`refine` and `replace` supply closed term-constructor templates and explicit
payloads. Stable identity selection, retention of unrelated fields, and retention
of nonmatching known terms can be read once. The wrappers expose the actual
difference: construct a nullary value from the binding's token/type, or install
the supplied term unchanged. All matching IDs are updated, including duplicates.

The tradeoff is a generic template and a payload argument. A reader must follow
that extra call to understand either public operation. The source is slightly
longer and the wrapper signatures remain unchanged. This is a concrete reduction
of duplicated invariants, not an automatic style-target pass. Template
specialization avoids a reusable runtime closure; no performance advantage is
claimed.

- Baseline scope SHA-256: `1457a6c70081f3c31d7eda4277ceb662399c7e8f3c40be2312001ccf287bd51e`
- Candidate scope SHA-256: `9581c3922f9d027e67b6b0a054b99b6b7b4062f59c3a0c72f9e7e3f1ea522dfd`
- Candidate generation: first attempt passed; no diagnostic retry or later candidate edits.
- Exact source: `candidate-first.bend.snapshot`; exact diff: `candidate-first.diff`.

## Fixed independent observations

Run from the repository root:

```sh
python3 research/compiler-style/family-1/check-behavior.py
```

`behavior.bend` imports only isolated copies. It emits every binding's token text
and four position fields, identity, quantity, type ID, parameter flag, and known
term. Values, references, and a compound constructor with a parameter and a
reference argument are observed field by field. Unexpected term shapes produce
a sentinel which cannot match the oracle. Other arbitrary term shapes are not
covered by this fixture.

`behavior-oracle.py` defines expected rows independently by their position and
case, with literal token/term anchors. It does not inspect or call either scope
implementation. Input hashes are fixed in each receipt before execution. Exact
whole-output equality detects reordered, omitted, additional, or changed records.

The 28 successful runs cover baseline/candidate × native/Bun × sizes
`0, 1, 7, 16, 64, 256, 1024`. Each run contains both operations on empty, missing,
first, middle, last, and duplicate identities: 336 sections and 54,720 binding
records total. Metadata varies by position; quantities span 0/1/2, both parameter
flags occur, and prior knowledge spans absent, value, reference, and compound
terms. Missing identities preserve all records. Duplicate cases update every
matching identity while retaining the other records.

The runner independently seed-checks copied `fields-PROOF.bend`, checks the
fixture, and builds native and Bun artifacts for each implementation. Commands,
exit statuses, source/program/expected/output hashes, and elapsed wall times are
in `behavior-receipts/attempt-002.json`. Complete stdout is retained in the
corresponding compressed files. These single-run wall times include process
startup, formatting, and output. They establish completion at increasing sizes,
not a speedup, isolated traversal cost, or an asymptotic bound.

The first new observer had an unsupported forward call from its term serializer.
That fixture-only diagnostic is retained in `behavior-receipts/attempt-001.json`
and its source in `behavior-receipts/fixture-first.bend.snapshot`. Reordering the
observer around its supported atom shapes resolved it. The candidate was never
changed and this was not a candidate generation retry.

## Remaining acceptance gates

The existing `tests/compiler-checker/check.py`,
`tests/compiler-fields/check.py`, and `tests/compiler-wasm/check.py` derive their
repository root from `__file__`, read `ROOT/src`, and write their fixed build and
receipt paths. They expose no supported source/build overrides. Running them
unchanged in the live checkout would test the baseline and touch shared output;
this sidecar did neither. Their complete regression and mutation gates require
parent integration or a separately authorized isolated repository layout.

The frozen preregistered live source, proof, contract-observation files, and
independent assertions still match their original hashes. No live source,
shared state, existing tests, or owned-store files were edited. No commits were
created. Targeted semantic Perch, all three style ratings, full regressions, and
the final integration/disposition remain with Compiler Planning.
