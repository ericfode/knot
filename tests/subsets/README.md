# First compiler corpus

These are no-Base Bend 2 programs, including intentional semantic negatives.
`s1/` names the stage they exercise; it does not claim all of S1 is implemented.
The pinned reference interpreter checks each program independently. Negative
diagnostics must reach the stated type, quantity or completeness rule.

The first frontend checkpoint parses all these files, including the semantic
negatives, into an explicit syntax tree. `Parsed` does **not** mean type checked,
accepted for execution or compiled. Resolution, quantity checking, evaluation
and Wasm emission are subsequent parts of the active compiler milestone.

Run `python3 tests/subsets/check_frontend.py`. It checks the complete Bend proof
entry, builds the parser written in Bend to native and JavaScript, compares both
against literal tree observations, checks reference outcomes and resource/error
boundaries, and kills type-correct semantic mutants. JavaScript bootstrap file
IO uses Bun 1.3.14 because the pinned Base uses `bun:ffi`; the eventual Wasm host
is Node 22.22.3. Generated seed artifacts stay under ignored `.local/`.

`classification-cases.json` fixes six seed-accepted out-of-profile programs and
six nearby malformed controls under `classification/`. The gate requires exact
exit status and phase/code/location in both parser lanes, alongside the original
14 tree fixtures and 24 boundary observations. The six prefix laws in
`src/LAWS.bend` preserve classification across arbitrary suffixes and source
locations; they do not validate those suffixes. Seven additional type-correct
mutants reverse a required classification and must produce that exact wrong
outcome to count as semantic kills. The hash-import reference uses the frozen
`module.bend` fixture staged into an isolated `BEND_LIB`; no hub is contacted.
The same fixed rejection diagnostics must also propagate through the checker,
evaluator and compiler in both lanes (72 observations); all 24 compiler failures
must preserve an existing output file. This checks rejection, not execution of
the unsupported forms.

Receipts distinguish universal boundary proofs, finite observations and runtime
checks. None proves general parser correctness or checker soundness. The host
harness orchestrates commands and compares observations; all lexing, parsing
and tree rendering lives in Bend.
