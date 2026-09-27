# Compiler pipeline trial contract

The driver turns source text into one checked compiler book. The public
`load`, `source`, `parsed`, and `checked` entry points retain their signatures
and observations. Lexing, parsing, checking, evaluation and emission semantics
are fixed dependencies, not design variables in this trial.

The text path has three ordered stages: tokenize with the character budget,
parse with the parser budget, and check the parsed root with the checker budget.
The budgets are independent. A stage's first failure propagates unchanged;
later stages and the success continuation do not run after that failure.
Exhaustion remains inconclusive and is never converted into a checked book.

`parsed` forwards an incoming failure before checking anything; on success it
checks the supplied root and ignores the parser's residual tokens, as before.
It does not spend the character or parser budgets. `checked` sends a successful
book to the continuation exactly once. Each public success continuation runs
at the same IO position as before. Error category, code, location, output stream
and process status remain unchanged.

`load` still opens, reads at most 65,537 bytes, and closes the input file before
source processing. Read/open failures retain their status and diagnostic. The
emitter's independent rule that failed compilation preserves prior output also
remains fixed. This trial does not change the accepted language, theorem claims,
runtime representation, package releases or paused compiler milestones.

## Reading hypothesis, recorded before generation

Author's hypothesis: seeing the text → tokens → parsed root → checked book path
and its first-error rule together reduces the reader's need to reconstruct the
pipeline from separate IO adapters. A new helper is justified only if the
complete mechanism becomes easier to follow. Consistent type and budget order,
compact composition and an explicit effect boundary are desired. This is a
reading hypothesis, not a human preference measurement or a promised score.

## Frozen experiment

One substantive candidate by GPT-6 Astra at max reasoning; preserve its first
source and first compiler result. At most one separate compiler-diagnostic
retry. Do not alter independent assertions to accept a candidate. A failed
candidate may be rejected; a verified readability improvement may be kept with
explicit style debt. Automatic style success requires all applicable current
declaration and complete-mechanism targets.

Freeze source, contracts, test programs/manifests, tool/rubric identities and
direct public-API witnesses before generation. Existing frontend/checker gates
exercise the unchanged stage implementations; the Wasm/fields/structural gates
exercise the shared driver through native and Bun compiler/evaluator programs.
The additional fixed witnesses cover public `checked` and `parsed` entry points
and continuation ordering. They are finite observations, not universal proofs.
Run the five complete existing suites and their proof entries on the candidate.
Keep all historical receipts and generated examples unchanged; redirect only
build/output destinations through the local gate launcher.

Perch reviews changed declarations semantically, rates every changed/introduced
declaration with fixed task evidence, and assesses the bounded complete pipeline.
Retain distributions and missing/truncated context. No repository-wide scan or
unchanged-score retry belongs to this trial.
