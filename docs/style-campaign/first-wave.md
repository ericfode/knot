# First style campaign results

Two implementation changes were accepted on 2026-09-26, both as unreleased
working revisions. Neither meets every style target. The campaign continues.

## IntMap — `2a74af4`

`branch` expressed one pruning exception through five constructor outcomes.
It now states the exception and passes every other pair through:

```bend
def branch(-V: Data, lo: IntMap<V>, hi: IntMap<V>) -> IntMap<V>:
  match lo hi:
    case Tip{} Tip{}: Tip{}
    case a b: Branch{a,b}
```

The get/set/remove path symmetry, public API, pruning semantics, persistence,
32-bit coverage and traversal order remain unchanged. The conceptual payoff is
the visible smart-constructor law; no new vocabulary or abstraction was added.

The first candidate passed complete proof checking, native and JavaScript
conformance, all 11 semantic mutants and the existing performance gates.
No compiler retry was used. Semantic Perch supplied 29 checks with no findings.

| `branch`: mass at level 3+ | Before | After |
| --- | ---: | ---: |
| Conceptual compression | 0.61 | 0.92 |
| Reading delight | 0.81 | 0.77 |
| Memetic identity | 0.07 | 0.09 |

All four reviewed path-family declarations meet compression and delight; all
four remain below the memetic target. These single model judgments are not
statistical estimates of improvement or measured human response. The code was
accepted for its direct expression and preserved behavior, with style debt open.

[Owner report, before/after and evidence](../../packages/int_map/STYLE_CAMPAIGN.md).

## OutputBuilder — `17473cd`

Append admitted a checked count while composition admitted a Boolean; each
rebuilt the same counted tree. One `join` now receives the admitted count and
centralizes length advancement and ordered construction:

```bend
def join(admitted: Result<Error,U32>, builder: Builder, suffix: Tree) -> Result<Error,Builder>:
  match admitted builder:
    case Fail{err} Buffer{cap,n,prefix}:
      Fail{err}
    case Done{k} Buffer{cap,n,prefix}:
      Done{Buffer{cap,U32.add(n,k),Join{prefix,suffix}}}
```

The existing `attach` and `combine` entry points become adapters. Byte scanning,
invalid-byte-before-capacity ordering and suffix emission remain unchanged.
The first candidate passed with zero proof holes, 14 native checks, 13 JavaScript
checks, nine semantic mutants and scaling through 8,000 chunks. No compiler
retry was used. Semantic Perch supplied 79 checks with no findings.

Of 17 reviewed definitions/datatypes, 16 meet compression, 12 meet delight and
none meet the memetic target. `combine`'s memetic mass rose from 0.04 to 0.32,
still below target. `attach`'s delight fell from 0.83 to 0.67. This is a visible
tradeoff, not an across-the-board win. Two datatype contexts hit the cap of four direct users;
definition contexts were untruncated. The common operation was retained for
its shared mechanism, with remaining reading deficits recorded.

One mutation's text locator moved with the implementation. It still discards
the right byte tree during composition, and the original witness/assertion
kills it. Assertion bodies and accepted laws were unchanged.

[Owner report, distributions and evidence](../../packages/output_builder/STYLE_CAMPAIGN.md).

## Coordinator verification and next work

The coordinator inspected the diffs and receipts, matched reviewed source and
helper hashes, checked fixed contract/assertion hashes, and verified every
recorded proof/build/runtime success and all 20 intended semantic mutant kills.
The owners performed execution; the coordinator did not rerun their tests.
Published content identities and release-time evidence remain unchanged.

The [verification receipt](first-wave-verification.json) retains checked input
and evidence hashes. Root campaign tooling separately passed all 28 tests and
law-rule wiring. The campaign setup is committed as `65f3bb1`.

The initial improvements did not solve memetic identity. Keep that deficit
visible, including the possibility of role/context sensitivity in the judge.
No rubric or threshold was changed to manufacture a pass. The next batches
cover Vec, Source, Symbols and TermStore; the compiler owner has preregistered scope.refine/replace at structural
checkpoint `6413a1a` while continuing its owning-runtime work. Other units and all historical
dispositions remain in the complete queue.
