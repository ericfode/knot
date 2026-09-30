# Descent-2 executor precheck repair

Starting checkpoint: `3eb80a30263d257c9badd6a94d6c89938d305eac`.
Tested implementation: `716f7703b6fd8b7f6d9d1efe8e0122bf5f832934`.
Qualification result: **17/17 gates passed**, exit 0, in 957.714092 measured seconds. The invoking source snapshot matches before and after the run.

The reported compiler conditions are repaired without changing any prior frozen
expectation, law or semantic mutant. Commit `9b33f2cb` froze all nine exact source
hashes from the review and 14 neighboring controls before production edits. The
pinned seed independently observes all 23 programs through parse, book, native
and Bun lanes: 15 accepted and eight rejected. The freeze is immutable and is
replayed by the registered `descent-prechecks` gate.

The source repair is in `b8361221`; `7ba698ea` preserves the existing concrete
quantity-error precedence and closes the new style-manifest import groups.
`f5ca6c0d` uses the canonical scope quantity merge for residual occurrences;
its unchanged original and new affine mutants both remain effective in both lanes.
`716f7703` makes the admission-only guard return Unit; M.alias retains the scope
operation. All focused outcomes are unchanged, with default O3 and deadlines retained.
Every commit in this repair uses the directly requested GPT-6.1 Sol trailer. The historical
[refresh report](DESCENT-2-REFRESH.md) and its receipts remain evidence of the
previous checkpoint; they do not qualify these subsequent source changes.

## Compiler behavior

| Frozen source SHA prefix | Former defect | Repaired CLI result |
| --- | --- | --- |
| `208934010de44d63` | Forward pattern constructor was Parsed despite seed parse rejection | `Invalid parse unknown-constructor`; downstream `Invalid check unknown-constructor` |
| `3b743ec11a606800` | Empty first domain became missing-arm after a harmless lexical gap | `Unsupported check empty-datatype` |
| `6ca9fd5e0721b596` | Empty first domain became missing-arm | `Unsupported check empty-datatype` |
| `8583b8be9bce45eb` | Dotted local pattern accepted in parse and check | `Unsupported parse dotted-binder` in every lane, per standing coordinator stopgap |
| `994c5fe84c89f297` | Wildcard `_` was used as a value | `Invalid check free-name` |
| `a09a4050df3f2eab` | Seed-accepted residual rematch became already-matched | `Unsupported check residual-alias` |
| `a58c6be37af1985b` | Affine default alias duplication was Checked | `Unsupported check residual-alias` |
| `ec85f95d234d7639` | Deep exhaustion escaped without a source position | `Exhausted check budget 73:74:7:4` in check/eval/compile |
| `f97b34472f86e33b` | Detached constructor pattern was accepted | `Invalid parse detached-brace` in every lane |

The parse CLI now validates constructor declaration events and arities. Constructor
expressions may still refer forward. Dotted pattern names use the canonical
parser stopgap; detached pattern braces retain their seed rejection. The common
source lookup refuses `_` as a value, while internal level lookup continues to
support reconstruction. Empty variable columns use the standing D4-compliant
capability refusal; unused empty declarations and zero-row elimination remain
accepted by their independent controls.

The residual guard uses a bounded usage algebra: sequence adds up to two,
alternatives take the maximum, lexical shadowing removes a name, and inspection
marks the residual obligation. It considers the visible aliases of a live affine
identity refined by constructor expansion. Single use, shadowing, explicit
promotion and constructor-field quantity checking remain covered. A concrete
`Invalid check affine-reuse` result precedes the conservative refusal. Each occurrence represents the same level in `E.sequential`, so the existing
quantity primitive remains the single policy for consumption conflicts. The guard
does not implement the missing Default core representation and may refuse valid
programs. Such refusal is a capability limit, not acceptance or a completeness
claim.

Exhaustion carries an available expression or function source boundary. The
original location-free helper equations and explicit zero-budget checker law
are unchanged. The earlier evaluator, Wasm emitters and descent algebra are
otherwise unchanged.

## Independent gates and laws

| Gate | Result / measured seconds | Exact counts |
| --- | --- | --- |
| frontend | Passed / 54.869343 s | 14 parser fixtures in two lanes / 28 observations; 24 boundaries; four boundary laws and six classification laws; four parser mutants; 12 classification fixtures in two lanes, seven classification mutants, 72 downstream observations |
| checker | Passed / 35.047306 s | 49 fixtures, 98 checked observations, 10 depth probes, two boundary cases / 16 catalog observations, seven semantic mutants |
| structural | Passed / 40.323797 s | 16 fixtures, 64 lane observations, four boundary pairs, seven semantic mutants |
| fields | Passed / 38.632607 s | 40 fixtures, 240 phase observations, 36 budget probes, six host probes, two boundary cases / 12 level and inspection observations, nine semantic mutants |
| wasm | Passed / 78.052154 s | 25 programs, 90 independent seed calls in two lanes, 62 rejection pairs, 44 boundary observations, seven semantic mutants |
| wasm-trust | Passed / 0.846685 s | three entries, zero proof holes |
| fields-trust | Passed / 1.266193 s | four entries, zero proof holes |
| structural-trust | Passed / 0.641829 s | two entries, zero proof holes |
| owned-store | Passed / 15.959340 s | 3,532 cases in two lanes, 15 literal witnesses, six semantic mutants |
| flat-store | Passed / 32.042957 s | each lane: 13,621 observations, 3,534 instances, two installed boundary states, seven lifecycle checks; nine semantic mutants |
| recursion | Passed / 29.897478 s | 19 fixtures, 114 phase observations, four fuel probes, three semantic mutants |
| fields-wasm | Passed / 180.970420 s | eight fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 frozen enum-byte checks, 30 boundaries, four mutants / eight kills, five checked laws |
| census | Passed / 0.588553 s | compiler 40 files / 609 declarations / 40 classes; frontend 3 / 53 / 31; packages 8 / 225 / 34; published imports 2 / 53 / 26; Base 1 / 495 / 45 |
| lint:verify | Passed / 10.592229 s | 127 tests, eight law-rule wiring controls; mocked review only, zero provider requests |
| nest | Passed / 208.656908 s | 40 fixtures, 174 seed calls, 40 matched outcomes / zero UNMET; 386 evaluator and 386 Wasm values, 24 boundaries, 100 enum hashes, six mutants / 12 kills |
| descent | Passed / 126.342327 s | original 38 fixtures / 228 phases / 19 accepted books; two resource fixtures / 12 phases / one accepted book; 34 refresh fixtures / 204 phases / 15 accepted books; 12 boundary cases / 24 observations, two proofs, seven mutants / 14 kills |
| descent-prechecks | Passed / 99.304765 s | 23 fixtures / 184 phases; 11 accepted books, 22 evaluator and 22 Wasm values, 11 equal module pairs, 24 preserved refusal artifacts; one proof / eight laws; seven mutants / 14 kills |

`gates:verify` separately passed 18 tests and six semantic wrapper mutants. Its runner and verification inputs are unchanged since that check. The [verification receipt](../../tests/compiler-descent/receipts/precheck-verification.json) retains normalized results, full counts, completion lines, measured times, environment identity and earlier failures.

The descent aggregate retains 74 frozen books / 444 phase observations, 35
accepted books, 70 evaluator values, 68 direct Wasm values plus two independently
checked observer links, 35 equal module pairs and 78 preserved rejection artifacts.
Its 24 boundary observations comprise 14 Exhausted, two InternalFailure and eight
successes. The original 38 books, two resource books, 12 boundary cases and seven
mutants remain fixed. The earlier refresh contributes 28 new edge programs plus
six verbatim nest sources, meeting the required 20 new edge-program minimum.

The new precheck gate contributes 23 fixtures / 184 phase observations, 11 accepted
books / 22 evaluator values / 22 actual Wasm values, 11 equal module pairs and
24 preserved refusal artifacts. Seven type-correct semantic mutants retain their
frozen mistakes and witnesses and produce 14 semantic kills. They exercise the
wildcard, empty-domain, residual duplication, detached brace, dotted binder,
declaration-event and unlocated-exhaustion defects. Every refused compile keeps
an existing artifact unchanged.

`src/precheck-PROOF.bend` fills eight laws with zero holes. Wildcard lookup and
empty-variable refusal are general helper equations; the other six are ground
controls for saturation, alternatives, lexical shadowing, usage, pattern events
and source position. They do not establish a general parser/checker soundness,
termination, residual-region lowering or matrix theorem. The two D21 matrix
laws remain required and open in `src/SPEC.md` and `LAW_REVIEW.md`; nest's newer
proof evidence must be preserved together with those obligations at integration.

The protected-input receipt compares 126 prior law/proof/mutant/pin paths against
the starting checkpoint, with zero changes. It includes the explicit file list
and hashes. A separate audit confirms the 27 new seed-freeze files and four new fixed specification/law/proof/mutant files are byte-identical to their freezing commits (`9b33f2cb` and `b8361221`). New files are additive independent controls. Census was regenerated
by `census:approve` then `census` and checked; the three nonempty approval summaries are recorded verbatim in their source-repair
commit bodies; the admission-only revision records its empty summary. No inventory was hand-merged.

## Precheck dispositions

The committed-head C1/C3 replay has exit 3, zero tool errors, two checks with
unavailable rules, and 11 executor conditions. This is not a precheck pass. C1
reports no remaining unsound acceptance, D4 false Invalid, value disagreement,
crash or malformed diagnostic. It reports four premature-unsupported conditions
on dotted binders. C3's shared runner shape and five restored driver conditions
are gone. The [disposition receipt](../../tests/compiler-descent/receipts/precheck-dispositions.json)
retains every remaining condition, fingerprint, evidence, stated reason and
coordinator metadata condition. No ledger entry or coordinator authorization
has been fabricated.

The four dotted-binder flags (`45039564fcfeef32415b`, `3e7f002746acdd34676c`,
`e4af3e4a0fabc7da90b9`, `a33f42d5b48d15b4bc86`) are disputed against
main's `COORDINATOR-STATE.md:59-64`: modules' scope-aware checker is canonical;
until integration the parser stopgap is `Unsupported parse dotted-binder`.
The suite calls a refusal at the seed's error token premature. All four books
are refused and cannot be evaluated or emitted. Moving the diagnostic offset
or replacing the named stopgap merely to appease that heuristic would obscure
the standing ruling. Modules owns its removal and seed-derived amendments.

| C3 path / fingerprint | Concrete disposition |
| --- | --- |
| `tools/census/approved.json` / `36cca7c64f2debab284b` | Required generator output records new declarations, imports and feature widenings. All three source-repair commits contain its exact printed summary, and census checks current. The additive-entry heuristic cannot represent a widening of an existing source declaration. Coordinator reconciliation remains. |
| `docs/compiler-campaign/manifest.json` / `d789742f1f5540c40ea5` | Three new groups are additive; existing groups append the imported helpers needed by the unchanged import-closure assertion. No old group, member, task or note is removed relative to the starting checkpoint. Merely adding a group would leave old groups unclosed. The unchanged 127-test offline lint gate verifies the required closure. Coordinator reconciliation remains. |
| `tests/compiler-recursion/check.py` / `377c91d8f5f372de0a2e` | Inherited independently frozen verdict/mutant migration remains; only the unauthorized host timeout addition was removed this round. The original anchors reference the retired descent/frontier helpers. The migrated mutants preserve same-parameter, direct and even witnesses. Restoring the old script would require obsolete Unsupported outcomes or absent source anchors. Pending coordinator D26 reconciliation/authorization. |
| `tests/subsets/check_frontend.py` / `0e4cf4252a837aa62567` | Inherited acceptance observer and original-witness mutant migration remains; only its host timeout addition was removed. The old observer can only validate rejected output and cannot check the now-accepted multi-match or execute its unchanged seed value. Pending coordinator reconciliation/authorization. |
| `tests/compiler-checker/cases.json` / `1edc1d233d5f8396faf7` | Inherited rows 20 and 39 remain unchanged this round: duplicate-arm is Checked; recursive-call is Invalid recursive-call. Original seed observations remain On{} and decreasing-self-call rejection respectively. Reverting to Unsupported loses the verified precise verdict. Pending coordinator pin reconciliation. |
| `tests/compiler-fields/cases.json` / `5a5e0e99a8cad16b2cab` | Inherited rows 23 and 25 remain unchanged: nested-pattern and nested-single-pattern are Checked, evaluate to the original Off{} and On{}, and enum compile remains Unsupported constructor-fields. Seed observations and emitter capability are unchanged. Pending coordinator pin reconciliation. |
| `tests/subsets/classification-cases.json` / `c8797540d2c0063c7234` | Inherited row 2 remains unchanged: multi-match is Parsed/Checked and evaluates/emits the seed's unchanged On{} / tag 1. The former match-scrutinees refusal is obsolete. Pending coordinator pin reconciliation. |

The last five conditions compare this branch to `d14418b7`, not the starting
`3eb80a30` checkpoint. They are preserved prior work, with concrete unchanged
seed evidence; this round does not claim new approval for their earlier edits.
The raw suite also flags historical commit metadata and the requested executor
trailers under its old Claude default. The direct user trailer is authoritative.
Full census summaries are actually present in `b8361221`, `7ba698ea` and `f5ca6c0d` despite
the suite's older summary heuristic. These coordinator-only metadata issues do
not justify rewriting history. Unavailable helper-divergence, promised-D4-target,
generator and ownership rules remain unavailable evidence.

## Ownership, failed attempts and style

The shared runner differs from its effective base only by additive gate/count
rows; its required-name test only adds names. Five legacy drivers are byte-identical
to that base. Seven timeout changes were removed in total, including the two
inherited migrated drivers. The earlier checkpoint body says six restored drivers;
the precise corrected statement is five byte-identical drivers and seven timeout
removals. The ignored clang wrapper resolves the installed Xcode clang and SDK;
it caches the exact verified installed version response. Native cache misses use that unchanged compiler binary. The local Bun launcher uses the seed-supported absolute CC and directs seed temporary files into ignored .local scratch even when an independent driver filters TMPDIR. The compiler wrapper applies application scheduling policies only to its own compiler children; it never changes another process. Cached version output alone did not eliminate the intermittent discovery failure; the absolute selection remains subject to the seed's normal version validation. A separate bounded probe made 240 successful version queries without reproducing it. No operating-system cause or universal reliability is claimed. The version and compiler hash are recorded in the verification receipt. It changes no optimization flag, source pin, compiler budget or host deadline. The seed reported no usable clang during version detection in the prior nest build; no precise operating-system cause is claimed.

The final run uses an ignored CPU native build cache. Every native seed build still
typechecks the source and generates C; actual clang freshly preprocesses every
eligible call. The cache includes the preprocessed bytes, compiler/linker/library
hashes, release flags and command plan, and validates the executable hash before
reuse. It normalizes temporary object locations and inactive debug-directory
metadata only for the strict no-debug/no-coverage CPU command. Source-sensitive
builtins stay in preprocessed input; unsupported compiler modes bypass caching.
Changed C produces a miss; invalid C remains a failed compilation. The verification
receipt retains those controls, warm builds, cache implementation identity and
all keys/events used by the run. Runtime checks, Wasm construction/execution,
quantity/proof acceptance and semantic-mutant assertions are fresh. The run reused 17 matching native builds and compiled 73 new entries. A cache hit
reuses native LLVM/link output and is not a fresh backend build or a cold-build
performance qualification. Cold builds exceeded unchanged host guards under
concurrent load; that remains an explicit host limitation.

| Attempt | Outcome | Measured whole-run time |
| --- | --- | --- |
| `run-06fqujan` | 15/17 passed. Offline manifest closure and concrete affine-error precedence failed; repaired by 7ba698ea. | 1082.115420 s |
| `run-3nc_r4bd` | 11/17 passed. Frontend/fields/wasm exceeded unchanged host build guards and blocked two trust gates. Nest normal controls passed but its unchanged affine mutant was masked by duplicate quantity enforcement; repaired by f5ca6c0d. | 1137.197772 s |
| `run-meomdq__` | Partial evidence only: ten completed passes, frontend failure, remaining gates unrun. No whole-run elapsed time or pass inferred. | Not measured to completion |
| `run-bm7vv1bo` | 16/17 passed. Sixteen gates passed; nest stopped at clang version detection before checking any program. The subsequent run caches the exact verified installed version response and retains the same binary, SDK, flags and host/compiler limits. | 903.286144 s |
| `run-kcsl6t_n` | 16/17 passed. Sixteen gates passed, including all nest mutants and the new prechecks. Descent stopped at clang version detection during the strip-rebuilt-constructor mutant build, before its execution. Cached version output alone did not eliminate the failure. The next run supplies the seed-supported absolute CC through the local launcher, retaining version validation and default O3. | 1480.731544 s |
| `run-4d38m7_a` | Partial evidence only: checker and structural completed; frontend failed. Remaining gates unrun. No whole-run elapsed time or pass inferred. | Not measured to completion |
| `run-kwwnz9hg` | Partial evidence only: frontend and structural failed, checker passed; remaining gates unrun. No whole-run elapsed time or pass inferred. | Not measured to completion |


The failed attempts remain evidence. No assertion failure or host timeout counts
as a mutant kill, source rejection or semantic success. Only owned descent and
precheck receipts are copied back. Other gates' shared receipts remain coordinator
refresh work. The final documentation/receipt commit changes no tested source,
gate script, frozen input, census or rubric.

The bounded offline preflight covers all 54 changed/new declarations in nine files.
Its fixed task is available at 2208 bytes. Six declaration contexts truncate;
the composition is unavailable at 109673 / 48000 bytes, with one collaborator
outside the selected group. There are zero provider requests.

| Style axis | Applicable quality target | Current evidence |
| --- | --- | --- |
| Conceptual compression | Level 3 per actual obligation | Unrated; no distribution or pass |
| Delight / high dopamine | Level 3 per actual obligation | Unrated; no distribution or pass |
| Memetic identity | Level 3 for mechanism/leading roles; level 2 for supporting roles | Unrated; no distribution or pass |
| Anticipation | Same role-scaled target | Unrated; six contexts lack full evidence; no distribution or pass |
| Payoff | Same role-scaled target | Unrated; six contexts lack full evidence; no distribution or pass |

All retain the 60% probability bar. Potential profundity/Galaxy brain remains
unrated; the fixed task is supplied, but offline preflight makes no judgment.
The reading hypothesis is the saturated usage algebra and explicit refusal
boundary. The new tests/proofs verify behavior, not aesthetic quality. Live
semantic/style review is coordinator-only and has not run. No automatic style
pass is claimed, and no score-seeking rewrite was made.

## D26 audit and integration boundary

No merge, rebase or push was performed. The direct implementer boundary supersedes
the refresh prompt's main-merge step; the coordinator integrates nest then modules
then descent-2. The earlier audit at nest `9645422d` is retained unchanged. These
are all 16 audited items; later upstream suites still require coordinator review.

| Case | Earlier nest pin | D26 selection |
| --- | --- | --- |
| `recursion/same-parameter` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/other-parameter` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/rebuilt-parent` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/rebuilt-constructor` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/computed` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/shadow-let` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/second-descent` | `Unsupported check recursive-call` | `Checked` |
| `compiler-checker/recursive-call` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `compiler-nest/rec-swapped-args` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `compiler-nest/rec-alias` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-partial` | `Unsupported check recursive-call` | `Invalid check missing-arm` |
| `rebuilt-retyped-constant` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-root-source` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-root` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-swapped-fields` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-unrefined-constant` | `Unsupported check recursive-call` | `Invalid check recursive-call` |

The original recursion gate still uses the enum emitter, so the checked
second-descent book retains Unsupported constructor-fields at compilation.
The fields-profile descent gate checks/evaluates the original structured book
and executes the independently frozen observer. A checked source does not imply
an unsupported emitter can build it. The integrated checker chooses diagnostic
phase/code; rebuilt-partial's missing-arm is supported by the frozen control
that removes only the self-call and exposes the seed's missing Leaf cases.

Remaining coordinator/dependent work: merge main and nest/modules in order;
reconcile D26 losing pins and displaced mutants in separate seed-citing commits;
preserve the D21 open-law/proof union; integrate Default core and scope-aware
dotted binders/empty-domain support; retain D22-D25 VM effect/Default/atomic-stop
semantics; run independent review and live Perch; refresh shared receipts and
resolve the explicit precheck metadata/authorization disputes. This report
qualifies branch-local implementation only, not integrated-main self-hosting.
