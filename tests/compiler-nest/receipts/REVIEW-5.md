# Nest review round 5

One finding was confirmed, and it is **partially fixed**. The
irrefutable-first-row law is now a general theorem with a checked proof. The
exhaustive-lowering law is neither fixed nor disputed. It stays unmet, and this
round asks the coordinator whether to accept that shortfall or require the
theorem.

No compiler behavior changed. `src/matrix.bend` and the checker are untouched.
All fixtures, expectations, gate assertions and mutant anchors are unchanged.

| Commit | Change |
|---|---|
| `7225d8e` | New `src/lowering-LAWS.bend` and `src/lowering-PROOF.bend`. `irrefutable_first_row_witness` added to `matrix-LAWS`. `matrix-PROOF` imports the lowering proof. New `lowering-laws` manifest group. Census approved; the summary is in the commit message |
| `6ef64e4` | CONTRACT.json, state.json, both SPECs, the LAW_REVIEW round-5 section, the falsification and preflight receipts |
| This commit | Gate receipts, campaign state and these dispositions |

Viewed alone, `7225d8e` records a `hosts.json` contract hash for the
CONTRACT.json that lands in `6ef64e4`, so `census --check` fails at that one
intermediate commit. HEAD is consistent.

## Finding

| Finding | Disposition and evidence |
|---|---|
| Two of the three required matrix laws exist only as ground witnesses | **Partially fixed.** `src/lowering-LAWS.bend::irrefutable_first_row_selected` holds for every fuel, catalog, scope, work budget, column list and trailing rows. Its hypotheses are one variable or promotion per column (`Irrefutable`, indexed by the columns) and a leaf body (`Leaf`). Its conclusion: every leaf of each successful `M.expand` tree is that body, and aliases are transparent. The proof is an induction on expansion fuel over an invariant that every lowering state preserves. It composes exactly the preservation facts that the one-step helpers state. No witness was renamed. `irrefutable_first_row_witness` inhabits the antecedent, and eight falsification mutants are each killed at a named proof term (`round5-falsification.txt`). The **exhaustive-lowering law remains unmet**. It is listed in CONTRACT.json and state.json, and LAW_REVIEW.md round 5 records the typing obstacle. A catch-all corollary is not claimed as the general theorem. |

## Requested decision

The coordinator should choose one:

1. Accept the documented shortfall for the exhaustive-lowering law.
2. Require it before merge. It needs typed value vectors and scope-typing laws for
   `P.branch`, generated `$matrix` lookups, `E.residual` and `M.alias`, plus
   Maranget matching lemmas for `specialize`, `without` and `default_rows`.
   That is a multi-hundred-line proof increment.

## Gates

On `6ef64e4`, `npm run -s gates` exited 0 with 24 of 24 gates passed
(`run-ijjqsn0v`, 425.9 s; the summary is `round5-all-gates.json.gz`).
`npm run -s gates:verify` passed its 18 tests. Every gate's counts equal round
4's except two. Census now counts 35 files and 641 declarations, up from 33
and 599, reflecting the two new modules. Bootstrap's corpus is 937, up from 935.

Only the nest-owned receipts (`nest.json`, `review.json`, `round3.json` and
`round4.json`) are refreshed, by direct gate runs. Semantic drift in shared
receipts, such as build hashes and loaded-file lists, is left to the
coordinator.
