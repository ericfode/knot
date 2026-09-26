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

Receipts distinguish universal boundary proofs, finite observations and runtime
checks. None proves general parser correctness or checker soundness. The host
harness orchestrates commands and compares observations; all lexing, parsing
and tree rendering lives in Bend.
