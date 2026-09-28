# Modules and pinned Base

Milestone 4 adds an explicit imported-book path to the Bend compiler. The loader
produces one ordered, qualified book; the existing checker, evaluator and enum
Wasm emitter then operate on ordinary names. Every user definition is checked.
Only the hash-verified Base receives the reachable-slice exemption.

Run commands from the repository root, with `BEND_NO_TELEMETRY=1`:

```text
check-cli --bundle tests/compiler-modules/bundle/lib source.bend
check-cli --audit-bundle tests/compiler-modules/bundle/lib source.bend
eval-cli --bundle tests/compiler-modules/bundle/lib source.bend main 65536
compile-cli --bundle tests/compiler-modules/bundle/lib source.bend output.wasm
```

The optional module mode preserves the original single-file arguments,
diagnostics and exit codes. Parent-relative imports in that original parser
now correctly report `Unsupported parse import`. No existing assertion was
changed, apart from the required registered-gate count increasing from 14 to 15.

## Mechanism and trust boundary

`imports.bend` reads headers and canonicalizes lexical paths. `qualify.bend`
applies per-file aliases and distinct term/constructor namespaces, respecting
lexical binders and declaration order. `load.bend` keeps pending headers, active
paths and completed paths in one explicit machine. A back edge is a cycle;
a completed dependency is reused in a diamond. No user definition is sliced.

`base-pin.bend` checks the unmodified pinned Base's SHA-256 before
`base-load.bend` inventories all 466 declarations. That inventory registers
book-global names at the Base import event. The transitive dependency closure
of every user definition selects Base source to parse and check. A needed form
outside the current language reports a specific `Unsupported` reason.

The audit runs only after combined checking. It emits `BasePin`, each loaded
`Module`, and disjoint `BaseChecked` / `BaseUnchecked` lists whose union, when Base was loaded, is the
seed's complete ordered inventory. Both lists are empty when Base was not loaded. Unchecked declarations remain a recorded
trust boundary. The seed compiler, arithmetic lowering and existing file/IO
primitives remain trusted. No new foreign capability was added.

## Independent expectations and gate

The original 40 entries, their observations and the frozen bundle remain
unchanged. These commits establish additional expectations:

| Commit | Independent expectation |
| --- | --- |
| `05473f7` | Seed-accepted parent-relative import; committed before implementation. |
| `cc0e1c4` | Seed rejection of an unused ill-typed imported definition; committed before implementation. |
| `b9a6c31` | User type named like a Base constructor, and user constructor named like a Base type; frozen before the category repair. |
| `778e62b` | Seven Python-hashlib vectors and the complete pinned Base digest; frozen before SHA implementation. |
| `722fc1d` | Local/hash identity, absolute import and mixed-root boundaries; frozen before their repairs. The raw-source cap was specified in prior literal review, then recorded in this freeze after the guard was implemented. |
| `71d20dd` | Seed-accepted 50 KB comment and 50,000 blank-line entries; frozen before replacing recursive header splitting/reassembly. |

`expectations.json` now contains the requested 42 seed fixtures.
`regressions.json` adds two namespace and two large-header cases; `probes.json` adds five boundary
cases. `regen.py` verifies the main seed oracle without rewriting it. The gate
also reruns every supplemental seed observation and compares frozen hashes.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-modules/regen.py
BEND_NO_TELEMETRY=1 python3 tests/compiler-modules/check.py
BEND_NO_TELEMETRY=1 npm run -s gates
npm run -s gates:verify
```

The [module receipt](receipts/modules.json) records 51 cases and 59 seed calls:
102 checks, 118 evaluations, 102 compilations, 54 Wasm observations, 21 identical
native/Bun Wasm pairs, 60 preserved outputs and 42 Base trust audits. Per lane,
the checker outcomes are 21 accepted, 19 Invalid, 10 Unsupported and 1 Exhausted.
The pin observer adds 22 observations; six real-loader checks reject a corrupted
Base as `HostFailure load base-pin`. Complete source and seed hashes are retained.

The five required mutants are independently seed-typechecked and built before
their frozen witnesses run:

| Mutant | Incorrect observation caught by the gate |
| --- | --- |
| Load a completed diamond dependency again | Invalid duplicate global instead of acceptance. |
| Re-export a file-local alias | Incorrect acceptance. |
| Resolve relative imports against the entry | Missing-module rejection of a valid nested import. |
| Accept a missing hash bundle entry | Incorrect acceptance. |
| Suppress active-path cycle detection | Incorrect acceptance. |

The proof entries print `All terms check.`: loader/path laws 16, qualification
17, Base selection 20 and pin helpers 15, for 68 filled laws. These are bounded
helper and transition laws, not a general order-independence, SHA refinement,
checker-soundness or compiler-correctness theorem.

## Full deterministic verification

The final scratch run passed all 15 registered gates with exit 0. The runner
snapshot and all 147 module-gate input hashes matched the worktree before copying
the new normalized module receipt. The [verification receipt](receipts/verification.json)
retains every gate count, completion record, drift classification and the earlier
integration failures. `gates:verify` passed 18 tests. Existing shared receipts are
left for the coordinator's post-merge refresh.

| Gate | Exact passing counts |
| --- | --- |
| Frontend | 14 reference fixtures, 28 lane observations, 24 boundaries, 4 boundary laws, 6 classification laws, 4 core mutants; 12 classification fixtures in two lanes, 7 classification mutants, 72 downstream rejections. |
| Checker | 49 fixtures, 98 checked observations, 10 depth probes, 16 catalog-bound observations, 7 mutants. |
| Structural | 16 fixtures, 64 lane observations, 4 boundary pairs, 7 mutants. |
| Fields | 40 fixtures, 240 phase observations, 36 budget probes, 6 host probes, 12 level/inspection observations, 9 mutants. |
| Wasm | 25 programs, 90 seed calls, two execution lanes, 64 rejection pairs, 44 boundaries, 7 mutants. |
| Wasm trust | 3 entries, 0 proof holes. |
| Fields trust | 4 entries, 0 proof holes. |
| Structural trust | 2 entries, 0 proof holes. |
| Owned store | 3,532 cases in each of two lanes, 15 literal witnesses, 6 mutants. |
| Flat store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 9 mutants. |
| Recursion | 19 fixtures, 114 phase observations, 4 fuel probes, 3 mutants. |
| Fields Wasm | 8 fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 frozen enum-byte checks, 30 boundaries, 4 mutants in both lanes, 5 laws. |
| Modules | 51 fixtures, 59 seed calls, 102 checks, 118 evaluations, 102 compilations, 54 Wasm observations, 21 byte pairs, 60 output-preservation probes, 42 trust audits, 22 pin observations, 6 corrupted-Base observations, 5 mutants, 68 laws. |
| Census | 43 source files, 785 declaration events, 40 feature classes. |
| Lint verification | 127 tests, 8 law-rule wiring checks. |

The runner classified 63 receipt artifacts identical, 7 volatile-only and 11
semantic. Shared semantic drift is confined to source/build/dependency hashes
and parser-mutant hashes; the new modules receipt has no tracked baseline.
No existing outcome assertion was relaxed.

## Offline preflight

All new Bend code and materially changed existing files received offline
preflight. No environment file or provider was accessed. The final closed
manifest groups include their local dependencies, so declaration counts overlap.

| Final receipt | Declarations | Truncated / role-limited | Composition bytes / 48,000 |
| --- | ---: | ---: | ---: |
| [Import paths](receipts/preflight-module-import-paths-handoff.json) | 56 | 2 / 2 | 12,541 — available |
| [Qualification](receipts/preflight-module-qualification-handoff.json) | 96 | 4 / 4 | 22,873 — available |
| [Base selection](receipts/preflight-module-base-slice-handoff.json) | 140 | 19 / 19 | 44,975 — available |
| [Base pin](receipts/preflight-module-base-pin-handoff.json) | 81 | 2 / 2 | 12,272 — available |
| [Loader](receipts/preflight-module-loading-handoff.json) | 287 | 33 / 33 | 83,512 — unavailable |
| [Driver/parser](receipts/preflight-driver-parser-handoff.json) | 81 | 47 / 47 | 136,895 — unavailable, unresolved context |
| [New fixture/observer files](receipts/preflight-new-fixtures-handoff.json) | 34 | 1 / 2 | 196,405 — unavailable, unresolved context |

All final invocations return attention status 3. Receipts without
`-handoff` are retained as historical preflight evidence. They do not describe
the final source/context selection.

Design deviation: the three loader-specific files total 16,282 bytes, but their
full parsing, qualification and Base-selection closure is 83,512 bytes, exceeding
the requested 48 KB composition limit. The loader is the composition point for
these mechanisms; its manifest retains the complete dependency set and blocker.
Four bounded submechanisms fit the composition limit; no aggregate style pass is
claimed. Compression, Delight, memetic identity, Anticipation, Payoff and potential
profundity have no live ratings. The coordinator owns that review.

## Limits and next increment

Module identity is lexical; symlink and case aliases are excluded. Absolute
import spellings and mixed absolute/relative entry/bundle roots report
`Unsupported`. Named packages remain unsupported; local and hash paths are read
only from existing files. The Base location is repository-relative. User files
are capped before header removal, loading has 1,024 transitions, and dependency
traversal is bounded. These limits do not prove larger programs invalid.

Primitive/literal and generic Base slices remain unsupported where the language
lacks them. The default emitter remains the enum profile; this increment does
not add fielded or recursive Wasm, whole-Base checking or self-hosting. The next
language increment needs primitives/literals and their fixed independent gates.
The coordinator should refresh shared receipts after merging and resolve the
remaining Perch context limits before claiming style qualification.
