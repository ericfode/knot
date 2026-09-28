# Compiler campaign census

Generated offline by `npm run census`; verified by `npm run census:check` and
`npm run census:test`. See the [tool contract](../../../tools/census/SPEC.md) and
[operation notes](../../../tools/census/README.md).

| Manifest | Evidence |
|---|---|
| [implementation.json](implementation.json) | Per-file imports, hashes, per-declaration feature classes, references and captures; class definitions and package pins |
| [base-closure.json](base-closure.json) | Frontend and compiler roots; JS/native cuts, value-reference slice, complete static dependency closure and dependency edges |
| [accepted.json](accepted.json) | Discovered suites, fixed fixtures and gate hashes; stage-specific positive evidence, failures and unknown-format reports |
| [hosts.json](hosts.json) | Reachable foreign effects, intrinsic/representation requirements, full Base trust inventory and emitted Wasm capabilities |
| [selfhost.json](selfhost.json) | Compiler/frontend closure counts, ranked missing classes and each declaration's check/Wasm gaps |

No timestamp, checkout path or unverified model rating enters a generated
manifest. Census parses source; the executed gates below supply separate evidence.

## Current census-2 meter

Run `npm run census:meter` for a read-only summary. The generated manifest uses
the JS runtime/type closure, including package/Base dependencies, excluding
law/proof files. Filled laws in ordinary files remain counted when they implement
runtime functions. A declaration needs its own feature classes plus its file's
import classes. Each stage counts only declarations with no missing classes.

| Closure | Declarations | Compiler / package / Base | All classes evidenced at check | All classes evidenced at Wasm |
|---|---:|---|---:|---:|
| `src/compile-cli.main` | 328 | 242 / 14 / 72 | 0 | 0 |
| `src/lex.tokenize`, `src/parse.parse` | 87 | 48 / 0 / 39 | 0 | 0 |

The largest compiler blockers are `types.base` (320 declarations), `imports.base`
(256), `generics` (236), `imports.local` (224) and `quantities.arguments` (222).
The frontend's largest blocker is `types.base` (86). These are overlapping
counts, not additive work estimates. Full rankings and per-declaration gaps are
in `selfhost.json`. Even complete class coverage would not qualify combinations,
host capabilities or a bootstrap.

The accepted inventory now discovers all 14 registered gates and reads **171
fixtures across seven suites**, covering 140 distinct files. It has 13 classes
with check/evaluator evidence and 12 with Wasm evidence. Recursion has check/eval
witnesses; fields have executed Wasm witnesses. `deep-call` evaluator exhaustion
and `arena-overflow` Wasm exhaustion are retained and excluded from positive
evidence. No unknown suite format is present in this checkout.

Thirteen explicit suite adapters also cover the six upcoming branch formats.
Their 242 frozen fixtures were loaded and inventoried from pinned Git objects;
they do not contribute until those files land here. Unknown future formats are
reported rather than inferred. See the [census-2 verification](census-2.md) for
exact gate counts, source pins, controls, mutants and the remaining boundary.

## Original census checkpoint (historical)

The following counts and receipts describe the first census increment before
the reviewed compiler wave. They are retained as historical evidence; the
generated manifests and census-2 report above describe the current checkout.

| Scope | Files | Declaration events | Unique declarations | Definitions | Used classes |
|---|---:|---:|---:|---:|---:|
| Compiler, including laws/proofs | 28 | 359 | 325 | 254 | 40 |
| Frontend: lex, parse, syntax | 3 | 45 | 45 | 37 | 30 |
| Candidate package runtime sources | 8 | 225 | 225 | 201 | 34 |
| Published imports, separately identified | 2 | 53 | 53 | 48 | 26 |
| Pinned Base | 1 | 495 | 466 | 321 | 45 |

The coordinator's **37 frontend definitions** and **37-entry Base runtime
closure** are confirmed. The latter includes 9 JS or 8 native intrinsic cuts and
has no foreign effects. The 16-class estimate is replaced by 30 explicitly defined
classes: this taxonomy separates quantity modes, literal kinds, captures, variable
calls and pattern forms. These class counts are not interchangeable with an
unspecified coarser taxonomy.

The frontend roots reach 36 of its 37 definitions (`syntax.line` is unused) and all eight frontend types;
the runtime/type closure has 81 entries overall. Its value-reference slice has
25 Base entries. The complete compiler driver (`src/compile-cli.main`) has 70 Base
runtime/type entries, including 20 JS or 19 native intrinsics and six foreign
operations: `IO.args`, `IO.print`, `File.open`, `File.read`, `File.close` and
`File.write_bytes`. The full Base trust inventory has 42 foreign definitions and
two unsafe definitions (`Array.fork`, `Array.join`); neither unsafe definition is
reachable from the selected roots. These are static upper bounds, not optimizer
output or a self-hosting claim.

Accepted fixture evidence covers 12 classes at checking/evaluation and 11 at
executed Wasm. Constructor fields have catalog/check/evaluator witnesses and no
positive Wasm fixture evidence. The records preserve Unsupported, Invalid and
Exhausted separately; the outcome adapter also preserves host/internal failures.

## Executed increment gates

Existing assertions and all `src/` and package source files were unchanged.

| Gate | Passed observations |
|---|---|
| `python3 tests/subsets/check_frontend.py` | 14 reference fixtures, 2 parser lanes, 24 boundaries, 4 laws, 4 semantic mutants |
| `python3 tests/compiler-checker/check.py` | 49 fixtures, 98 checked observations, 10 depth + 16 catalog-bound observations, 7 mutants |
| `python3 tests/compiler-structural/check.py` | 16 fixtures, 4 boundary pairs, 7 mutants |
| `python3 tests/compiler-fields/check.py` | 40 fixtures, 240 phase observations, 36 budget + 6 host + 12 level/inspection observations, 9 mutants |
| `python3 tests/compiler-wasm/check.py` | 25 programs, 90 reference calls in each of 2 lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| `bun tests/compiler-wasm/trust.ts` | 3 closure entries; zero holes; runtime foreign sets of 6, 5 and 0 |
| `bun tests/compiler-fields/trust.ts` | 4 closure entries; zero holes; runtime foreign sets of 0, 5, 5 and 6 |
| `bun tests/compiler-structural/trust.ts` | 2 closure entries; zero holes; 5 runtime foreign operations |
| `python3 research/owned-store/check.py` | 3,532 traces per CPU backend, 15 literal witnesses, 6 mutants |
| `python3 research/flat-store/check.py` | 3,534 instances and 13,621 step observations per backend, 24 literal probes and 7 lifecycle checks per backend, 9 mutants; 1,050-byte Wasm module |
| `npm run -s lint:verify` | 103 tests and eight-rule law wiring; zero provider requests |
| `npm run census:test` | 33 tests, including 3 complete seed checks and 4 semantic census mutants |
| `npm run census:check` | All four generated manifests current; repeated regeneration byte-identical |

Every proof entry used by the compiler gates printed `All terms check.`:
`src/PROOF.bend`, `src/check-PROOF.bend`, `src/catalog-PROOF.bend`,
`src/fields-PROOF.bend` and `src/runtime-PROOF.bend`. The stores' proof gates also
passed. The census fixture's reflexive law is only a parser/proof-syntax control.

The first `lint:verify` attempt could not lock the read-only platform tree-sitter
cache (88 passed, 11 failed before all files could run). The unchanged gate passed
after copying the existing manifest, bundles and parser libraries into ignored
`.local/census-parser-cache` and setting `TREE_SITTER_LANGUAGE_PACK_CACHE_DIR`
to that directory. No download or test change was needed.

Regenerated legacy receipts were inspected and restored: paths, dates, timings,
gzip headers and pre-existing stale compiler input hashes were outside this
increment. Decompressed store observations were byte-identical. Fresh command
logs remain in ignored `.local/census-gates/`; the counts above record this run.
The sandbox denied the worktree Git index lock during `git checkout --`.
Exact HEAD blob contents were restored inside the writable working tree instead;
the Git index and other worktrees were not changed.

## Perch and next increment

Offline preflight with `--task=tools/census/SPEC.md` covers 16 declarations in
three new Bend fixture files: zero truncated contexts, zero incomplete role
contexts and an available 821-byte composition with no unresolved references.
The initial taskless preflight reported `missing_task_context`; supplying the
fixed contract removes that blocker. Both runs made zero provider requests.
There are no live compression, delight, memetic, anticipation or payoff ratings;
preflight is not a style pass. Live review belongs to the coordinator.

Next: merge/reconcile this snapshot, preserve the explicit approval policy, and
extend accepted-profile evidence as capabilities land. Use the named closure
entries to plan Base lowering. Actual seed-emitted reachability, instance-specific
templates and higher-order flow remain separate work; this inventory does not
certify a complete executable bootstrap.
