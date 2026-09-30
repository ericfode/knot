# Closures review round one

The compiler repairs reject split `->`/`=>`, refuse lexical type shadows as
`Unsupported check dependent-type`, accept the seed's lambda continuations and
newlines before `=>`, intern arrows by resolved domain/result IDs, and lower
wide tail calls compatibly with Node 22.22.3 arm64. The two split-operator majors
are duplicates with one repair. The previously unverified wide-call finding is
confirmed: fresh native/Bun compilers at `c0cc612a` emitted modules that abort
default Node with SIGTRAP at widths 39 and 64, while width 38, Bun and Node
`--no-liftoff` succeed. It is fixed by a conservative 32-live-parameter bound at
both ends of `return_call`; wider callees use `call; return`, and wider callers
use ordinary body lowering. This keeps values but does not promise constant
stack usage for wide signatures. Narrow continuation acceptance remains required.

Expectation-first commit `662c88bb` adds 42 sources: 29 accepted controls and
13 seed rejections, independently observed with 42 checks, 84 native/Bun builds
and 58 seed executions. Existing expectations, fixtures, laws and mutants remain
unchanged. No seed-derived amendment to an existing expectation was needed.
The [new manifest](../../tests/compiler-closures/review-r1.json) and
[archived pre-repair receipt](../../tests/compiler-closures/receipts/history/review-r1-before.json)
retain complete sources, commands, outputs, hashes and measured timings.

Both repaired compiler lanes pass all 42 controls: 84 check, 84 evaluator and
84 compile observations, 58 default-Node calls, 29 byte comparisons, and 18
additional wide-host controls (forced Liftoff, no Liftoff and Bun). All eleven
lambda layout programs execute their seed-fixed result. Seven lexical shadow
programs refuse without creating an artifact, and their renamed controls agree.
Five new local laws check operator spans and exact arrow keys; all ten complete
root proof entries check without holes. The open general preservation obligation
remains required under D21.

The first repaired observation measured native medians over three samples:

| Unused signature | Before | After | Module bytes |
| --- | ---: | ---: | --- |
| 128 parameters | 1.849915 s | 0.005539 s | Identical, 186 bytes |
| 192 parameters | 9.834378 s | 0.008107 s | Identical, 250 bytes |

These are paired, bounded observations from seed-native `-O1` compiler builds,
with the SDK path explicit, and a 30-second external guard. They are not a
complexity theorem or a default-`-O3` performance claim. Recursive name printing
is removed from nominal/arrow lookup; explicit arrow IDs retain their existing
ordering and synthetic suffixes retain the existing inventory contract.

Four additional type-correct mutants exercise wrong split-operator acceptance,
ignored lexical type scope and false Invalid semicolon layouts. A fifth restores
wide `return_call` and is killed by decoded unsafe lowering before invocation;
host aborts are never semantic kills. Full registered-gate and mutation counts
will be recorded after the complete suite finishes. The three minor archived
receipt links in `docs/perch-review-log.md` now resolve through `receipts/history/`.

## Style and integration remainder

The offline style finding is confirmed and remains an integration dependency.
The current branch intentionally retains the shared context tooling; the
coordinator assigns fitting to `perch-cap`, and merging or borrowing another
worktree's implementation is outside this executor's authorization. Nonlocal
ByteOutput context and manifest-wide composition partitioning also belong to
the coordinator's Perch integration. This is not a disputed finding or a style
pass. No code is reshaped solely to fit the judge, and no cap, coverage or
quality threshold is weakened.

| Offline whole-manifest preflight | Before | After |
| --- | ---: | ---: |
| Groups | 21 | 21 |
| Structural blockers | 605 | 626 |
| Truncated contexts | 594 | 615 |
| Unavailable compositions | 11 | 11 |
| Supporting-role exemptions unavailable | 705 | 724 |
| Provider requests | 0 | 0 |

Counts repeat shared declarations across groups. Both commands exit 3 and report
current source freshness. Closure-types has 14 truncated contexts,
closure-checking has 31 plus its unavailable composition, closure-lowering has
15, and constructor visibility has one. Closure-checking is 72,730/48,000 bytes
after repair. Seven global compositions still contain unresolved nonlocal
imports. Compression/Maximally big brain, Delight, Memetic identity, Anticipation,
Payoff and composition have no live ratings or distributions; all remain
unqualified. Potential profundity/Galaxy brain remains unjudged.

The smallest honest composition repair requires a shared manifest/tool policy
for selecting bounded collaborating declaration families with explicit imported
interfaces. Splitting file lists alone loses the referenced checking/evaluation
law family; including its full closure recreates the over-limit composition.
The coordinator must preserve every declaration and composition obligation while
partitioning captures, partial application and closure evaluation, then rerun
offline preflight before any live qualification claim. `perch-cap`'s names-only
tier addresses fitting; it does not itself establish complete contexts or solve
the 48,000-byte composition limit. Current tasks and thresholds remain intact.

The existing coordinator remainder is unchanged: serial nest/modules/descent
integration, the D24 request Default, generics' nineteen blocked chooser calls,
shared receipt/census refresh, and live semantic/law/style qualification.
Under D26, function-field is Checked in the catalog with enum emission still
refused; closure-parameter remains Unsupported until lambda-match is modeled;
closure-apply is Checked with generic higher-order support and otherwise genuine
Unsupported. `suffix-cont-lambda-let` and `letop-lambda-dead2` become Checked when
matrix support is sound, otherwise Unsupported. Seed values never move.
No merge, rebase, push, provider call, `.env` access or other-worktree mutation
occurred. All new scratch/build products are under ignored `.local/`.
