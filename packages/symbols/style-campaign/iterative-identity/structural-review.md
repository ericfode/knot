# Independent balanced-trie validation

Both frozen candidates pass the independent structural checks on native and JS.
All 17 deliberately broken implementations compile and then fail those checks
semantically. No defect was found in the reviewed rotation or prefix-root logic.
This is finite controlled evidence, not a universal invariant theorem or a timing
benchmark. The public model/laws/assertions were not changed.

| Candidate | Main SHA-256 | Independent assertion SHA-256 |
| --- | --- | --- |
| 05 balanced Letter payload | `babfe9205dd805928984307cd59fdb7fe764fe111854a33b94d977ecb387a491` | `3390667ba666553ba1b933d8c9b084071f73285ce6b0f5771be52ba238fbb820` |
| 06 separate prefix terminal | `8e44e7b0b147ad90cee9c049d62d44d8ba14bcbf0b7b07bc45044c24d2eacbeb` | `bb2d5771f76d276aec64cb928b0123f1add71a7440645a532e2ac5fb3ede5222` |

The source copies are in `05-baseline/` and `06-baseline/`. Their
`invariant-gates.json` files retain compile, native and JS command results. Each
layout's identical assertion file is used unchanged against its implementation
mutants. `controls.json` identifies those mutations and their hashes;
`control-runs.json` and each mutant's `invariant-gates.json` retain the outcomes.

## Checked invariants

The consuming Bend audit computes subtree bounds, sibling black height, color,
maximum sibling depth and a violation mask. It checks all sibling subtrees and
every nested `same` subtree; it does not inspect only the outer root.

| Bit | Violation |
| --- | --- |
| 1 | Nonblack top or nested prefix root |
| 2 | Red node with a red less/more child |
| 4 | Unequal less/more black height |
| 8 | Nonstrict sibling order |
| 16 | 06 only: Here in less/more, or a second Here wrapper |

For 05 the independent ordering is `End < Code(c)` for every U32 c, including
zero. For 06 terminal Here is outside the character tree. Here.more must be a
black Fork/Vacant tree and every Fork.same starts another valid prefix root.
The audit handles that wrapper explicitly; returning a superficially black
wrapper cannot conceal a red underlying sibling root.

Handwritten checker controls require exact masks for a valid tree, a red root,
a red/red edge, unequal black height and reversed order. The 06 controls also
check a terminal inside a sibling tree and a terminal wrapper hiding a red root.
These all return 1 on both native and JS, validating each assertion category
independently of the implementation mutation set.

## Implementation controls

| Mutation | 05 mask | 06 mask |
| --- | ---: | ---: |
| Omit left-left rotation | 2 | 2 |
| Omit left-right rotation | 2 | 2 |
| Omit right-left rotation | 2 | 2 |
| Omit right-right rotation | 2 | 2 |
| Omit blackening of a fresh same root | 1 | 1 |
| Omit blackening after equal-character descent | 3 | 3 |
| Omit top-root blackening | 3 | 3 |
| Reverse LT/GT character insertion directions | 8 | 8 |
| Omit blackening through Here.more | N/A | 3 |

Every control compiles, executes and returns the same nonzero mask on both
backends. No control is counted as detected merely because typing failed.

The witnesses include every prefix of all four three-key rotation orders,
the same orders beneath a common character prefix, empty/NUL ordering,
terminal-plus-character trees, repeated names, composed/decomposed Unicode,
emoji and U+10FFFF. Additional whole-tree checks cover ascending/descending
scalar names and ascending/descending names following a common prefix.

## Measured sibling depths

Both layouts and both backends gave the same values for ascending distinct
single-scalar names:

| Names | 1 | 2 | 3 | 16 | 64 | 256 | 1,024 | 4,096 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Maximum sibling depth | 1 | 2 | 2 | 5 | 7 | 9 | 11 | 13 |

At every listed size, all four ordering/prefix workloads have zero structural
violations on native and JS. `diagnostics.json` contains these results, the
checker-control executions, source hashes and complete command records. These
depths support the intended balancing behavior on this corpus; elapsed command
times are not package performance results.

## Code review

All four rotations preserve the inorder character sequence and carry each
same-subtrie with its original character. For 05 that payload is a Letter; for
06 it is the char/same pair in each Fork. Rotations affect less/more links only.

In 06, recursive less/more insertion always carries a nonempty String, so it
cannot create a Here terminal in a sibling tree. Only a top or same descent can
finish the String and create/wrap Here. Top insertion and equal-character descent
blacken that prefix root, and Trie.black traverses its optional Here wrapper.
Fresh tails are also blackened. Those cases account for the otherwise easy-to-miss
independence between sibling trees and same-subtries.

Lookup compares complete U32 character values and treats the terminal separately
from NUL. Public intern probes before append and commits the trie only after
Vec.push succeeds. The original public model and laws remain the evidence for
payload/ID behavior; this additive audit checks structure rather than replacing
those gates.

Two diagnostic-driver failures are preserved separately: a rejected import path
and an attempt to compile a parameterized pure main directly. The repaired driver
uses local copies and a zero-argument entrypoint. Neither required changing the
candidate or any invariant assertion.
