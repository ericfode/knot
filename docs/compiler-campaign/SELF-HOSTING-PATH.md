# Self-hosting path

This document lists what Knot still needs in order to host itself, which increment owns each requirement, the order in which the remaining work lands, and the risks that remain. It is the output of the self-hosting gap analysis (workflow `wf_35f2e149-542`). That workflow ran five survey lenses (features, Base, scale, host, fixpoint), an adversarial verifier for each blocking or major claim, and a completeness critic.

**Snapshot.** Statuses are evaluated at these commits:

| Branch | Commit |
|---|---|
| `main` | `f5afd84` (D14 recorded at `ec43747`) |
| `campaign/nest` | `eb15da8` |
| `campaign/descent-2` | `75e1ac6` |
| `campaign/modules` | `0111f13` |
| `campaign/literals` | `2ea222e` |
| `campaign/generics` | `f39ba7e` |
| `campaign/closures` | `a1d6891` |
| `campaign/io-host` | `f42ae39` |
| `campaign/wasm-owned` | `37baabe` |

Most verifier verdicts were written before the last five of these. Where a newer commit changed a verdict, the table says so.

**Route.** D14 is in force: self-hosting is VM-first.
1. The seed builds C1 on its native lane.
2. C1 compiles the bundle S into image I2.
3. The VM runs I2 as A2, and A2 compiles S into image I3.
4. The fixpoint is I2 = I3, and both generations must pass the conformance corpus.

Native Wasm codegen (`knot-enum-1`, `knot-fields-wasm-1`, closures' defunctionalization, owned storage) is now the speed track. The VM increments themselves are defined by the in-flight vm-design synthesis (`wf_68968469-dba`). This plan records the obligations those increments must meet, but it does not define them.

**S.** S is the import closure of `src/compile-cli.bend`, plus the hash-pinned ByteOutput package and the reachable Base slice. On main the closure has 13 source files (15 bundle files with Base and ByteOutput); on `campaign/literals` it has 32 source files. The closure contains the checker, the core and the emitter. The standalone CLIs outside S use no feature class that S does not also use, except `calls.partial`, and parse-cli exercises that in `e2e2.compile`. `*-LAWS` and `*-PROOF` files are outside S, as `docs/BEND-SUBSET-STAGES.md` requires (FX-19).

## Why the JS-lane fault matters

The fault is this: the seed's Bun (JS) lane overflows its stack when Base's `List.length` recurses past about 32,000 elements. The seed's native lane handles 16,000,000.

- **It does not block C1.** C1 is built only on the native lane. The harness never compiles with the Bun lane.
- **Knot's own code triggered it.** `src/compile-cli.bend:25` counted the emitted bytes with the non-tail `List.length` after writing them. It is the only call in `src/` over an output-sized list.
  - Reproduction: the Bun-built compiler wrote all 53,216 bytes of a 250-function module, then exited 1 with `bend: memory fault (machine stack overflow?)`. The native lane printed `Built 53216`. The two outputs are byte-identical.
  - Replacing the count with `0` removed the fault at that size: Bun then exited 0 with byte-identical output. So the count was the only call that faulted at 53 KB.
  - `campaign/literals` `2ea222e` replaces the count with the tail-recursive `A.length` (`src/machine-code.bend` `length_from`). The literals amendment adds a Bun-lane regression that emits at least 53 KB, and that regression is what pins the fix.
  - Above 53 KB, other recursions over output-sized data are still unmeasured on the Bun lane: ByteOutput's `B.finish`/`emit` with `List.append`, and `W.concat`.
  - Once literals merges with that regression, the `state.json` note "must be diagnosed" can be closed.
- **The only Bun run on the self-hosting path fails closed.** That run is `e2e2.reference` (`bun parse-cli.js` on each corpus file).
  - parse-cli reads at most 65,537 bytes, and 28 worst-case inputs agree across lanes. The receipt shows 623/623 files agreeing.
  - `check.py` counts a Bun fault there as a disagreement, not as Exhausted. That turns the gate red with the RangeError visible; it never produces a false pass.
  - Keeping `disagree + exhausted` folded is correct, because it forces both oracle lanes to agree. The charter's C1-lane bullet, which says the fault "is recorded as Exhausted", is what is wrong, and integrate-1 corrects that wording. The harness does not change.
- **Two consequences last.**
  - **The JS lane is the oracle for every frozen suite.** Every suite records seed expectations through `bun main.ts`: the JS interpreter for pure mains, and the JS lane for IO mains.
    - Nothing can be frozen at compiler scale. The io suite already had to make `write-bytes` report the requested count instead.
    - The lanes also disagree on some semantics: `String.length` on non-scalar Chars, Nat width, and `String.append` as a JS-only intrinsic.
    - The lanes increment measures these divergences (LANE-01).
  - **The same failure class threatens A2, sooner.** Node's default Wasm stack holds 13,781 minimal non-tail frames. Bun holds 637,763.
    - Guest recursion on the host stack would fault earlier than the seed's Bun lane does, and at points 46 times apart on the two hosts that DoD item 2 requires.
    - So D14's VM must keep guest frames in linear memory. This plan records that as a vm-design obligation (D14-04).

## Decisions required

Each decision has one owner. Work that depends on a decision does not start until it is recorded in `docs/COMPILER-CAMPAIGN.md`.

| Id | Decision | Owner | Deadline | Recommendation |
|---|---|---|---|---|
| DEC-1 | How the loader's path-identity foreign `path-host.inspect` is served in A2. It is in S (`compile-cli` → `driver` → `load` → `path-host`), and Knot's checker rejects it with `Unsupported check foreign-definition`. | Coordinator | Before io-host merges (the knot_io ABI freezes at that merge) | Add a knot_io `inspect` op with frozen encodings and a C host / JS host / VM differential. The checker then admits exactly the hash-pinned foreign identities. The alternative, a pure sandbox rule, cannot detect symlinks. |
| DEC-2 | Replace the classification laws `destructuring_binding` and `template_binder` (`src/LAWS.bend`, proved in `PROOF.bend`) and the two classification cases. The sugar FIXTURES.md requires this decision before implementation. | Coordinator | Before products starts | Replace each with a law over the supported form and a law that the remaining seed-valid variants are Unsupported. |
| DEC-3 | Reconcile the frontend gate pin that requires generic headers to stay Unsupported. It blocks the generics merge (`f39ba7e` message). | Coordinator (integrate-1) | At the generics merge | Replace the pin with the generics suite's frozen outcomes, as a reviewed amendment. |
| DEC-4 | One pattern matrix. Literal, Nat-offset, Char and String columns go through nest's `src/matrix.bend`, and `literal-matrix.bend` is folded into it or retired. | literals executor (amendment) | Before literals merges | As stated. The literals prompt already requires lowering through the pattern matrix. |
| DEC-5 | The Nat representation and bound on the image route. Options: a machine word with the seed's 2^48-1 bound, or unary cells with a 1,048,576 Exhausted bound. | vm-design synthesis | Before the image format freezes | A word with an explicit bound. The compiler's own maximum output budget, 1,048,576, sits exactly at literals' unary cap, and every unary Nat operation is O(n). |
| DEC-6 | Whether literals' Wasm instruction machine (`machine-vm.bend` and related files) is the VM's starting point, or stays a literals-only profile. | vm-design synthesis | Before any VM increment starts | Record the decision in the D14 notes. Freeze the machine at literals scope until then. |
| DEC-7 | The conformance oracle lane. | Coordinator, on the lanes report | Before the harness route adds conformance stages | Base semantics as run by the seed's native lane and interpreter. The JS lane is a cross-check whose stack fault is inconclusive. |
| DEC-8 | Amend D12 (`Unsupported compile host-effect`) for the image target. | Coordinator | Before core-io starts | The image target compiles exactly the hash-pinned foreign identities. The native Wasm targets keep D12 until they gain an IO lowering. |

## Increment plan

### Order

1. **Now, in parallel with the in-flight branches:**
   - harness-2, joint and lanes. They touch only `tests/compiler-bootstrap/`, a new `tests/compiler-selfhost/`, and a new lanes receipt.
   - integrate-1's charter step, and its first merges (nest, descent-2, modules).
   - DEC-1 and DEC-2.
   - The vm-design synthesis (in flight).
2. **After modules and literals merge:** census-3. Modules edits `tools/census`.
3. **After nest, literals, closures and generics merge:** selfsource and products. Every one of those branches edits `parse.bend` and `check.bend`, and most edit `catalog.bend`.
4. **After products:** sugar and baseslice.
5. **After products and the vm-design synthesis:** core-io.
6. **VM increments defined by vm-design:** image and C1 image emitter, VM runtime with model and laws, harness route. They can run in parallel with steps 2 to 5 where their files allow. The image serializer needs integrate-1's unified core schema. The IO part of the image needs core-io.
7. **Milestone 9, a frontend image on the VM** (as redefined by integrate-1). It needs selfsource, products, baseslice's frontend slice, the VM image and runtime, and the harness route.
8. **Milestone 10, the image fixpoint.** It needs everything above, plus sugar, core-io and the VM IO layer.

The critical path is: integrate-1 merges → products → core-io and baseslice → the VM IO layer and harness route → the fixpoint.

### Increments

| Id | Goal | Closes | Depends on | Start now | Executor | Size |
|---|---|---|---|---|---|---|
| harness-2 | Generate every compiler generation from one frozen bundle and one argv, and record a generation contract, whichever route is used. | SCALE-02, SCALE-12, FX-02, FX-03, FX-04, FX-05, FX-08, FX-09, FX-10, FX-11, FX-18, FX-20, FX-21, FX-22, FX-25, FX-27, A2H-06, A2H-07, A2H-08 (staging), A2H-12, A2H-14, THIN-02 | none | yes | codex | 1-2 days |
| joint | Freeze seed-derived fixtures for the combinations and scales that S uses and that no suite pins. | SF-01, SF-02 (fixtures), SF-04, SF-05, SF-06, SF-08, SF-09, SF-10, SF-13, SF-14, SF-16, SF-17, SF-18, SF-21, SF-22, INT-02, SCALE-01, SCALE-05, BS-05 (fixtures) | none | yes | codex | 2-3 days |
| lanes | Name the oracle lane, and measure where the seed's lanes disagree on the frozen agree fixtures. | LANE-01, FX-14 (oracle part) | none | yes | codex | 1 day |
| integrate-1 | Merge the on-path branches in a fixed order on `campaign/integrate`, re-key the charter to D14, and record the first blocker on S after each merge. | INT-01, D14-02 (core schema), D14-05 (ladder), D14-06, FX-01, FX-19, A2H-02 | none (merges each branch once it passes review) | yes | claude | 2-3 days, spread over merges |
| census-3 | Make the self-hosting meter measure the route actually used. | LANE-02, A2H-19, BS-11 | integrate-1 (modules, literals merged) | no | codex | 1-2 days |
| selfsource | Make the frontend and checker accept the layout and the size of S. | SF-01, SF-02, SCALE-01 | integrate-1 (nest, literals, closures, generics merged), joint | no | codex | 1-2 days |
| products | Type-level definitions (Pair, IO, Sigma) and product syntax (`A & B`, tuples, destructuring lets, tuple patterns). | SF-15, SF-20, BS-03 (items 3-6) | integrate-1 (closures, generics merged), DEC-2 | no | codex | 2-3 days |
| sugar | List literals, `do` blocks and templates, including their use in imported modules. | SF-14, SF-16, SF-17, SF-22 | products, joint, DEC-2 | no | codex | 2-3 days |
| baseslice | Lower the reachable Base slice from the post-modules closure, gated against census drift. | BS-02, BS-03 (items 1-2), BS-06, BS-09 (audit), BS-16, SF-11 | products, integrate-1 (literals, descent-2, modules merged) | no | codex | 2-3 days |
| core-io | Represent IO and the pinned foreign effects in checked core and the evaluator, so the image carries IO and the VM only dispatches it. | D14-02 (effect term), SF-12, SF-13, BS-12, SCALE-08, A2H-03, A2H-05, A2H-11, A2H-15, IO-07 (checker and core) | products, integrate-1, vm-design synthesis (IR), DEC-1, DEC-8 | no | codex | 2-3 days |

#### harness-2

- **Scope.** `tests/compiler-bootstrap/` only. No in-flight branch touches it.
- **One argv.** A single builder produces `[--bundle ROOT] <S entry> <out> <CONTRACT maximum_overrides>`. `--bundle` is used once the compiler's CONTRACT advertises module loading.
  - The same argv goes to both generation steps.
  - Today they differ. `check.py:242` gives C1 the maxima (65536 4096 4096 4096 1048576). `check.py:277` gives A2 only `[source, output]`, so A2 falls back to parser depth 512 and a 65,536-byte output cap.
  - The receipt records the argv, and the judge asserts that the two steps' argv are equal.
- **Staged sandbox.** `.local/compiler-bootstrap/bundle/` holds copied regular files: the S closure, Base at `.toolchain/bend-2.0.29-574b6d3/bend2/base.bend`, and `0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend` under a relative ROOT.
  - C1 runs with that tree as its working directory. The A2 sandbox is a fresh copy of the same tree.
  - Every file's sha256 is recorded. The hash of each 0x package file is pinned in the harness manifest, and a mismatch fails the run before the seed step.
  - The sandbox inputs are cross-checked against C1's `--audit-bundle` Module lines. The D2 Base trust inventory is stored with the receipt.
- **Generation contract.** `progress.json` gains a `generation_contract` object with:
  - the S entry and closure order, the argv, and the target;
  - the Node version (22.22.3, asserted), the V8 flags and stack policy, and the memory maximum;
  - `clang --version`;
  - the qualified host (Darwin, whose errno table io-host freezes);
  - the seed-reserved flags, which the harness rejects in argv;
  - the list of excluded metadata.

  The judge requires identical contracts for both generation steps.
- **Judge.**
  - Every blocker gets a source tag: knot-budget, host-stack, host-memory or host-time.
  - At `e2e3.a3`, a host-resource Exhausted after C1 has built S at `e2e3.a2` becomes the non-passing status `divergent-exhausted`.
  - `e2e2.reference` keeps its `disagree + exhausted` fold.
- **Diagnostics.** The receipt records C1's full `(exit, stdout, stderr)` for every conformance case. Later generations must match it byte for byte.
- **Timing and sizes.**
  - Timeouts scale by `KNOT_GATE_TIMEOUT_SCALE`.
  - Once `e2e3.a2` is reached, the receipt records C1's wall time and peak RSS on S.
  - It also records artifact sizes and their headroom under `output_bytes`.
- **Acceptance.**
  - The bootstrap gate passes on main with the current blockers.
  - New mutants are killed: differing argv, a symlinked sandbox input, host-Exhausted A3 after a reached A2, and a change confined to a diagnostic tail.
  - On a scratch merge of main and `campaign/modules`, both steps use `--bundle`, and the receipt records the new first blocker.

#### joint

- **Scope.** A new suite `tests/compiler-selfhost/` with `regen.py`, `expectations.json`, a runner that is aware of blocked cases, and a registered gate.
  - Every seed call is observed on both the seed JS interpreter and the native lane. A disagreement between lanes is a reviewed decision (DEC-7).
  - Every case names its owning increment and its needs. The runner reports blocked cases separately and never passes them.
- **Layout (owner selfsource):**
  - newlines after `(` and `,` in call arguments;
  - multi-line def parameter lists in Knot's exact shape: trailing comma, continuation indented to the body column;
  - newlines inside `{..}` in constructors and patterns, and inside `[..]`;
  - a dedented `name)` continuation line, in the shape of `driver.bend:33-37`, and a bare dedented `)`;
  - blank lines and `#` comment lines inside open delimiters;
  - the dedented `S.choose` ladder after `=>` (SF-04).
- **Fuel dispatch (owner literals, via DEC-4):**
  - `match fuel mode:` with the rows `case 0n _`, `case 1n+ +n K{..}` and a wildcard-fuel row first;
  - Nat columns beside `SNil`/`SCon` columns;
  - predecessor self-calls inside continuation lambdas;
  - a four-column variant.
- **Qualified shapes (owners modules and generics):**
  - qualified and package constructors nested in Base generic patterns, and as multi-scrutinee columns (`Fail{B.Limit{}}`, `C.Checked{C.Sequence{..},..}`);
  - fields typed by imported local and package types, including `List<&2,F.Flag>`;
  - an imported module that calls its own generic def while the entry defines the same bare name with another signature (INT-02);
  - cross-module calls to generic and higher-order functions with explicit type arguments and lambdas (SF-21).
- **Representation (owner generics):**
  - a rose tree through `List<&2,Self>`;
  - mutual Term/Bind through `Maybe` and `List`;
  - both built, matched and traversed with fuel.
- **IO shapes (owners core-io and sugar):**
  - a user `load(path, next: X -> IO(Unit))` threaded through `IO.bind` lambdas;
  - a fuel-recursive IO loader in the shape of `load.bend:215-225`;
  - a statement-only `do IO<Unit>:` in an imported module whose continuation calls a module-local def;
  - list literals in an imported module.
- **Sugar contexts (owner sugar):**
  - a list in a generic constructor field, a list as a lambda body, and a list of generic `Result` elements;
  - the cross-module template argument `~C.Term`.
- **Recursion (owner descent-2):** `emit(left,emit(right,suffix))`.
- **Scale (owners selfsource and literals):**
  - a bundle of at least 700 functions across 20 modules plus Base;
  - `65536n`, and `U32.from_nat(U32.to_nat(1048576))` within budget;
  - `U32.or`, `U32.xor`, `U32.not` and `U32.shln` on the edge words 0, 1, 2^31 and 2^32-1.
- **Acceptance.**
  - Every case has seed observations on both lanes.
  - Every positive has a seed-rejected twin where one exists.
  - Every Knot requirement is pinned: agree, or an exact Unsupported or Invalid code.
  - `regen.py verify` reproduces the suite, and the gate is registered.

#### lanes

- **Scope.** Rerun every frozen agree fixture's seed calls on the seed's native build and on the interpreter. The suites are nest, modules, literals, generics, closures, baseslice, io, sugar and the landed suites. Compare each run against the frozen records, which the JS lane produced.
- No frozen expectation is edited (D7).
- The output is a receipt and report under `tests/compiler-lanes/`.
- Every divergence names a DEC-7 outcome. The known candidates are: `String.length` on non-scalar Chars, Nat width 2^48-1, and the JS-only `String.append` intrinsic.
- **Acceptance.** The receipt has three-lane observations for every call. No divergence is left unexplained. A verify script reproduces the receipt.

#### integrate-1

- **Where.** The work happens on `campaign/integrate` (currently at `f5afd84`). The executor never merges or pushes to main. The coordinator fast-forwards main after each merge passes its gates, as the campaign protocol requires.
- **Charter step.**
  - Redefine milestone 9 as a frontend image on the VM, byte-identical in behaviour to the seed-built parse-cli.
  - Redefine milestone 10 as the image fixpoint plus conformance.
  - Correct the C1-lane bullet (see "Why the JS-lane fault matters").
  - Close the `state.json` memory-fault note once literals merges with its 53 KB Bun-lane regression.
  - Amend each on-path prompt: checker, core and evaluator deliverables gate self-hosting, and native Wasm lanes are speed-track evidence.
  - Record the S definition and DEC-1 to DEC-8.
- **Merge order.**
  1. nest.
  2. descent-2, re-merged onto nest `eb15da8`.
  3. modules.
  4. literals, after its amendment.
  5. closures, rebased onto descent-2's `Scope{...,aliases}`, with the `partial-self-same` pin migrated to Invalid.
  6. generics, after its amendment and DEC-3.
  7. io-host, after DEC-1.

  wasm-owned is speed track. It merges after closures once its review is clean, and it does not gate self-hosting.
- **Each merge.**
  - Run all registered gates and the joint suite.
  - Handle every `S.Node` variant explicitly in `qualify.walk`. A nest plus modules tree does not build until `Matrix` and `Alias` cases exist.
  - Unify `src/core.bend` into one schema holding Closure/Invoke (closures) and Literal/Intrinsic/Default (literals).
  - Regenerate the receipts.
  - Run the literal-aware bundle check (`check-cli --bundle`) over every file of S, and record the first blocker per file in the bootstrap receipt.
- **Acceptance.**
  - Every merge commit passes all gates.
  - The first-blocker table is current.
  - No file of S reports Invalid. An Invalid on S is a D4 violation. An example on literals `2ea222e`: `src/primitive.bend:88` `def all() -> List<&2,O.Op>` gives `Invalid parse function-result`, and generics fixes it.

#### census-3

- **Closure.** Compute the closure with Knot's own loader (base-load slice) and Knot's intrinsic registry (`src/primitive.bend`, 39 ops), per profile, next to the seed's JS and native cuts.
- **Stages and classes.**
  - Add a core/image evidence stage beside check and wasm.
  - Add a layout class covering multi-line headers and continuations inside delimiters.
- **Suites.** Add reviewed adapters for `tests/compiler-io`, `tests/compiler-sugar` and `tests/compiler-selfhost`. selfhost.json lists the first two as `unrecognized-suite`.
- The JS-cut meter stays as a secondary view.
- **Acceptance.**
  - The meter reports check, core and image evidence per declaration.
  - It counts the layout sites (eight multi-line headers on main).
  - It lists Knot's intrinsic cut next to the seed's.
  - The census tests pass, and the approval summary is printed.

#### selfsource

- **Layout.** In `parse.bend`, skip newline tokens and comment-only lines at continuation points in these lists: Arguments, Parameters, ListTail, constructor fields, pattern fields and list literals. The continuation points are after `(`, `{`, `[` and `,`, and before the closing delimiter.
  - Do not suppress newlines in the lexer. Closures' `LambdaStatements` needs newline tokens to separate the statements of a lambda body inside an argument list (the `choose(c, u =>` shape in `choose-thunks`).
- **Catalog limits.** In `catalog.bend`, `CONTRACT.json` and `SPEC.md`, raise the catalog limits to 4,096 functions and 1,024 types, as U32 counters that keep Exhausted.
  - Today one book allows 256 functions; 257 gives `Exhausted check budget`.
  - S already has at least 288 functions on main (217 user, 13 ByteOutput, 58 Base) and about 650 after the in-flight merges.
- **Optional.** Make the declaration spine iterative, so that parser depth measures nesting only (SCALE-12).
- **Acceptance.**
  - The joint layout and catalog cases agree.
  - Today's Invalid on these seed-accepted forms becomes a parse or agree result.
  - Every file of S parses.
  - Laws are checked.
  - Mutants are killed: a newline skipped inside a lambda body, and an off-by-one limit.

#### products

- **Scope.** Checker, core and evaluator only; this work is route-independent.
- **Type-level definitions.**
  - Expand `Pair` over `Sigma`, including the dependent field `snd: B(fst)`.
  - Expand `IO(-A) = @-R: Type -> (A -> IO.OP<R>) -> IO.OP<R>`, including its erased higher-rank binder and dependent arrow.
  - Support `A & B` in types (`U32 & String`, `File & Result<..>`).
- **Terms.**
  - Tuple construction.
  - Destructuring lets `(file,result) = pair` and `((a,b),c) = r`.
  - Tuple patterns `Fail{(code,message)}`.
- **Precondition.** DEC-2 must be recorded first.
- **Acceptance.**
  - Evaluator agreement on the frozen `tuple-*` and `destructure-*` sugar fixtures.
  - The baseslice `io-pure-bind` and `bind-missing-types` fixtures match.
  - Closures' `dependent-arrow` pins for this form move to agree through a reviewed amendment.
  - Laws for type-level expansion and destructuring.
  - No unchecked path in checked core.

#### sugar

- **Scope.** Parser, checker and core desugaring for:
  - `[..]` to Base `Con`/`Nil`, with the quantity taken from context;
  - statement-only `do IO<Unit>:` to `IO.bind(Unit,Unit,s1,_ => s2)`;
  - templates: `~A: Data`, `~value: ..`, `~(a => ..)`, recursive template self-calls, and qualified type arguments.
- **Imported modules.** Desugared `Con`, `Nil` and `IO.bind` must resolve to Base in non-entry modules, and qualification must not rewrite them.
- **Fixture amendment.** Add `do` fixtures to the sugar suite; it omits `do` today. The io suite already pins `do` as agree. Amend the pins these forms supersede, each with review:
  - the template and destructure cases in `tests/subsets/classification-cases.json`;
  - generics `template-twice`;
  - closures `template-map`.
- **Acceptance.**
  - The sugar gate passes.
  - The io `do` fixtures check.
  - The joint cases for SF-14, SF-16, SF-17 and SF-22 agree.

#### baseslice

- **Law-declared untyped defs.** `String.cmp`, `String.starts_with`, `U32.read.go` and `U32.show.go`, plus the two new cycles `String.contains`/`.if` and `String.trim_start`/`.if`.
- **Descent.** Support descent across these six helper cycles. The frozen suite pins four of them.
- **Refreeze.** Refreeze the slice from the post-modules census, from 72 to 95 entries, as a reviewed amendment. Add agree fixtures for the 16 entries that lack one.
- **Gates.**
  - Register baseslice as a gate that also runs `regen.py --census` and fails on drift.
  - Gate `--audit-bundle` on the compile-cli bundle. It must list no lowered `Word.*` helper, and it must record every `BaseIntrinsic` and `BaseUnchecked` entry.
- **Frontend slice.** Deliver the frontend slice that milestone 9 needs.
- **Acceptance.** The baseslice gate is registered and green. Census drift is zero. The compile-cli audit lists no lowered Word helper.

#### core-io

- **Effect term.** Add a checked core effect term (pure, bind, die and the pinned effect operations). Its shape must match the IR that the vm-design synthesis fixes.
- **Checker.** The checker admits exactly the hash-pinned foreign identities: the six Base effects, plus the DEC-1 outcome for `path-host.inspect`. Every other foreign definition stays `Unsupported check foreign-definition`. Under DEC-8, D12's `Unsupported compile host-effect` is lifted only for the image target.
- **Evaluator.** The evaluator runs IO mains against a model host written in Bend. That model is the reference for the VM IO layer.
  - Halt is a terminal die.
  - Higher-order user functions with IO continuations must work.
- **Acceptance.**
  - All 40 io fixtures check with their frozen outcomes.
  - Model-host runs match the frozen seed records on every agree run, with Exhausted only where the records have it.
  - The joint SF-13 cases agree.
  - The compile-cli closure checks with no `foreign-definition` Unsupported.
  - Mutants are killed: reordered effects, a die that resumes, and a lost `write_bytes` invalid flag.

## Amendments to in-flight increments

- **io-host, before merge.**
  - Implement DEC-1: add the `inspect` path-identity op, with frozen encodings and a C / JS / VM differential over symlink, case-alias and missing-path fixtures.
  - Let `runIO` take injectable stdout and stderr sinks, or ship an invoke helper. The bootstrap adapter must run the guest in a child process, because a Worker cannot capture `fs.writeSync(1)` (measured).
  - Share one trap classifier with `scripts/run-wasm.mjs`.
  - Add a control that separates a guest `IO.die(4, ..)` from host stack exhaustion.
- **literals, before merge.**
  - Add `WOr` and `WXor` to the registry, with seed-frozen fixtures on edge words. `base-pin` (SHA-256) and `machine-code` (LEB128) call `U32.or` and `U32.xor`, and the 39-op registry has neither.
  - Rebase onto main after nest, descent-2 and modules, and implement DEC-4. The joint fuel-dispatch cases are the acceptance test.
  - Add a Bun-lane regression that emits a module of at least 53 KB, so the `A.length` fix stays pinned.
  - Record the unary Nat bound (1,048,576) as a Knot Exhausted limit, pending DEC-5.
  - Freeze the instruction machine at literals scope, pending DEC-6.
  - Report the instruction count of S against the 32,768-instruction module cap.
- **modules, at its merge after nest.** Give `qualify.walk` explicit cases for nest's `Matrix` and `Alias`. Replace the silent wildcards in `following`, `names_in`, `terms_in`, `ctors_in` and `base-load.pattern_scope` with an explicit Internal.
- **generics, at its merge after modules.**
  - Extend qualify's declaration introduction to `S.TypedFunction` and `S.Generic`, and handle all nine new node variants.
  - Pass the joint collision case. Without this, `eval.bend`'s internal `select` call binds to `eval-cli`'s `select`.
  - Qualify type arguments in fields and signatures (`List<&2,C.Term>`).
  - Accept DEC-3.
- **closures, at its merge.**
  - Rebase onto `Scope{...,aliases}` and migrate the `partial-self-same` pin (already recorded in `state.json`).
  - Self-hosting acceptance is the checker, core and evaluator Closure/Invoke. The `return_call` and defunctionalization Wasm lanes are speed-track evidence.
- **vm-design, obligations on the increments its synthesis defines.**
  - **Image.** A versioned, canonical encoding of checked core and the reachable Base slice, with a law that decoding an encoding gives back the book. No paths, timestamps or host metadata. Two C1 runs must give identical bytes (D14-01).
  - **Authoring.** Choose an authoring route and pin its toolchain in the generation contract. `wat2wasm` is currently an unpinned Homebrew binary (D14-03).
  - **Stack.**
    - Guest frames and continuations live in linear memory, with no host recursion that grows with guest depth.
    - Fixtures recurse deeper than 700,000 frames and run at least 100,000 continuation steps. They give the same result, or the same Exhausted bound, under Node and under Bun.
    - Covers D14-04, A2H-01, SCALE-06, SCALE-07, FX-15, FX-16 and the residual of BS-14.
  - **Heap.**
    - One exported memory with a declared maximum of at most 2,048 pages, and `knot_alloc`.
    - Growth before reporting Exhausted.
    - Reclamation of continuation cells.
    - Peak pages recorded on S.
    - Covers SCALE-04, A2H-13, FX-06, THIN-01 and BS-15.
  - **IO layer.**
    - Implements knot_io exactly: the six effects plus the DEC-1 op.
    - Both bind directions trampolined over 100,000 binds.
    - Iterative `write_bytes` packing with the invalid flag; the output list is dropped after packing.
    - Halt maps to `die`, with no resumption.
    - Covers SF-12, BS-12, SCALE-08, SCALE-09, A2H-03 and A2H-11.
  - **Primitives.**
    - Semantics equal to literals' evaluator and the seed: div and mod by 0 give 0 and x; shifts of 32 or more give 0; comparisons are unsigned; `from_nat` truncates mod 2^32; `nat_sub` saturates.
    - DEC-5 applies.
    - Covers FX-14, SCALE-05 and BS-08.
  - **Size.**
    - String literals are pooled in the image.
    - The size of I2 is measured against the 1,048,576-byte output cap. Raising the cap is a reviewed contract change.
    - Covers SCALE-03, FX-28 and A2H-12.
  - **Harness route.**
    - Image stages: C1 → I2, then VM(I2) → I3, then I2 == I3.
    - A VM entry ABI for conformance calls.
    - A child-process knot_io adapter that copies inputs into a fresh sandbox (A2H-08, A2H-09, A2H-10).
    - A VM-versus-C1 differential over the full corpus, comparing exit, stdout, stderr and artifact bytes (ORACLE-01).
    - The conformance corpus grows with each merged suite (FX-17).
    - A Bun host lane (FX-23).
    - The seed made unavailable after the seed step (FX-24).
    - A time budget and a VM timing row in `bench/` (SCALE-16, A2H-18).
    - Covers D14-05 (harness part).
  - Record DEC-5 and DEC-6.
- **wasm-owned.** No amendment. Heap capacity and growth have moved to the VM. This branch stays speed track.
- **nest and descent-2.** No amendment beyond the merge steps in integrate-1.

## Requirement table

Status gives the corrected verdict where an adversarial verifier ran (v), the surveyed verdict otherwise (s), and the completeness critic's verdict (c). "Updated" marks a row that a commit after the verdict has changed. `SCALE-NN` abbreviates the survey identifiers `SCALE-NN-<NAME>`; for example, SCALE-01 is `SCALE-01-CATALOG-256`.

### Features

| ID | Requirement | Evidence | Covered by | Status |
|---|---|---|---|---|
| SF-01 | Continuation lines inside open `()`, `{}`, `[]` after `(` or `,` | The seed accepts; Knot on main and every branch gives `Invalid parse expected-term` (D4). Sites: syntax:56-58, driver:33-37, lex:62, patterns:57, scope:81-82, wasm:136, 241-242. No fixture has a newline inside `{}` or `[]`. | selfsource, joint | partially covered, blocker (v) |
| SF-02 | Multi-line def parameter list | 8 sites on main, 22 on modules. Knot gives `Invalid parse parameter`; the literals HEAD gives the same. Blocks parse-cli's own closure. | selfsource, joint | gap, blocker (v) |
| SF-03 | `#` comment line inside an open delimiter | The comment lexes to a newline, so the failure is SF-01's. Closures parses the only site (parse:202). | SF-01 fix; one joint case | covered, minor (v, refuted) |
| SF-04 | Dedented `S.choose` ladder after `=>` | Parses on closures; no frozen fixture | closures; joint | partially covered, minor (s) |
| SF-05 | Nat literal, successor or wildcard as one column of a multi-scrutinee match (fuel dispatch) | 9 matches with 105 rows on main. Every Nat pattern in every suite is single-column. Literals HEAD gives `Unsupported parse match-scrutinees`, and literals is not based on nest. | literals amendment (DEC-4), joint | gap, blocker (v) |
| SF-06 | `1n+ +n` reusable predecessor | 84 sites on main, all multi-column. Single-column checks on literals `2ea222e`. | literals; literals amendment and joint for multi-column | partially covered, major (v, updated) |
| SF-07 | `1n+n` in expression position | The seed folds `<k>n+term` in its numeric-literal parser, not as an operator. Pinned by literals `literal-views` and by `conversions` through `Nat.show.fin`. | literals | covered, minor (v, refuted) |
| SF-08 | Qualified constructors nested in patterns and as columns | On a nest+modules scratch merge all 24 observations agree, once `qualify.walk` has `Matrix`/`Alias` cases. No frozen fixture. | modules amendment, joint | partially covered, minor (v) |
| SF-09 | Datatype field typed by an imported qualified type | Works on modules (12 runs agree, 3 negatives rejected). `List<&2,F.Flag>` fields are Unsupported until generics and modules meet. | generics amendment, joint | partially covered, minor (v) |
| SF-10 | Rose tree through `List<&2,Self>` (AST, core IR) | Works on the generics and wasm-owned work in progress; no fixture | joint | partially covered, minor (v) |
| SF-11 | Base functions outside the frozen 72-entry slice | `regen.py --census` on modules lists 23 extra entries; 16 have no positive fixture. Two new law-declared helper cycles. | baseslice | gap, major (v) |
| SF-12 | IO: `main() -> IO(Unit)`, the type-level `IO`, `IO.bind`/`IO.die`, six effects, function-value continuation | No checker/core owner. io-host adds no compiler capability. S also reaches `path-host.inspect`. | products, core-io, vm-design | partially covered, blocker (v) |
| SF-13 | User higher-order functions with `X -> IO(Unit)` continuations and capturing lambdas | `die-after-write` covers a user higher-order function at `IO(Unit)`. Nothing threads a continuation through several user functions (driver:15-55, load:215-225). | core-io, joint | partially covered, minor (v) |
| SF-14 | Statement-only `do IO<Unit>:` in an imported module | The io suite pins `do` in the entry as agree. No imported-module fixture. The sugar suite omits `do`. | sugar, joint | partially covered, major (v) |
| SF-15 | Tuples: destructuring let, tuple pattern, `A & B` | Every branch reports `Unsupported parse destructuring-binding`. The frontend closure needs it (Char.cmp, String.cmp, String.eq.fin). DEC-2 comes first. | products | partially covered, blocker (v) |
| SF-16 | List literals in Knot's contexts | Covered except: a list in a generic constructor field, a list as a lambda body, a list of generic `Result` | sugar, joint | partially covered, minor (v) |
| SF-17 | Templates, including `~C.Term` | `template-set-known` mirrors scope:77-86. No cross-module case. Closures reports `template-binder` Unsupported. | sugar, joint | partially covered, major (v) |
| SF-18 | Self-call nested in another self-call's argument | bytes.bend:80-81. The recursion suite covers an adjacent shape only. | joint | partially covered, minor (s) |
| SF-19 | Base generic families with quantity arguments | generics `f39ba7e` implements generic checking and boxed erasure (unreviewed) | generics | partially covered, blocker (v, updated) |
| SF-20 | Erased and dependent type parameters with explicit arguments, including `IO(Unit)` and products | Erased parameters are in generics; `IO(Unit)` and `A & B` arguments need type-level definitions | generics, products | partially covered, major (v) |
| SF-21 | Cross-module calls to user generic and higher-order functions | The modules fixtures call only monomorphic functions across modules | joint; integrate-1 runs it | gap, major (v) |
| SF-22 | Sugar inside imported modules | Every sugar fixture is a single file | sugar, joint | partially covered, minor (v) |
| SF-23 | Non-tail recursion over output-sized data | compile-cli:25 `List.length`; literals `2ea222e` uses `A.length` | literals amendment | risk, major (v); replaced on literals, pinned by the 53 KB regression |
| C-01 | `import Base`, `./x.bend as A`, `0x<hash>/bytes.bend as B` | modules fixtures | modules | covered (s) |
| C-02 | Top-level qualified references; same bare names in several modules | modules fixtures | modules | covered (s) |
| C-03 | Multi-scrutinee constructor matches, wildcard columns, first match, depth 8 | nest fixtures | nest | covered (s) |
| C-04 | `+` binders in nested patterns; nested match on a field binder | fields and nest fixtures | landed, nest | covered (s) |
| C-05 | Record, nullary and multi-constructor types; parameter and let forms | merged suites | landed | covered (s) |
| C-06 | Lambdas, captures, curried parameters, thunks, function values | closures fixtures | closures | covered (s) |
| C-07 | U32 and large Nat literals; Nat arguments | literals fixtures; implemented on `2ea222e` | literals | covered (s) |
| C-08 | String and Char literals, escapes, `SNil`/`SCon` | literals fixtures | literals | covered (s) |
| C-09 | The 72-entry Base slice on main | baseslice coverage table | baseslice | covered (s) |
| C-10 | Forms absent from S's code | Detector hits come only from strings, comments and paths | boundary pins | covered (s) |

### Base

| ID | Requirement | Evidence | Covered by | Status |
|---|---|---|---|---|
| Q-JS-1 | The JS lane is not the oracle for deep recursion, and C1 does not depend on it | C1 is native only (charter, harness) | charter | covered (s) |
| Q-JS-2 | Harness classifies a Bun stack fault as Exhausted | `check.py` counts it as a disagreement. The only Bun use is `parse-cli.js`, capped at 65,536 characters (623/623 agree). The fold fails closed. | charter wording (integrate-1) | covered, minor (v, refuted) |
| BS-01 | Base slice inventory for compile-cli | base-closure.json: 72 Base entries on main | census | covered (s) |
| BS-02 | Plain-Bend Base entries | Frozen baseslice suite with no gate and no implementer | baseslice | partially covered, major (v) |
| BS-03 | Six Base-only demands: law-declared untyped defs, cross-helper descent, `((a,b),c) = r`, Pair/IO type-level defs, Sigma's dependent field, higher-rank IO | Knot reports `destructuring-binding` Unsupported; no branch claims the cycles | products (3-6), baseslice (1-2) | gap, major (v) |
| BS-04a | U32.add/sub/mul/and intrinsics | In literals' 39-op registry at `2ea222e` (unreviewed) | literals | partially covered, major (v, updated) |
| BS-04b | U32.div/mod with zero semantics | literals `u32-division`; `WDiv`/`WRem` | literals | covered, minor (v, refuted) |
| BS-04c | Unsigned U32 comparisons | literals `u32-unsigned-order` | literals | covered, minor (v, refuted) |
| BS-04d | U32.shrn: 32 or more gives 0 | `WShr`; `u32-shifts` | literals | partially covered, minor (v) |
| BS-04e | U32.to_nat, U32.from_nat, Nat.cmp | `ToNat`/`FromNat`/`NCmp` over unary cells capped at 2^20 | literals; DEC-5 | partially covered, major (v) |
| BS-04f | Bool.or and U32.is_zero lowered from source | baseslice fixtures | baseslice | covered (s) |
| BS-04g | String.append order and semantics | `SAppend` | literals | partially covered, minor (s) |
| BS-05 | U32.or and U32.xor | Reached by `base-pin` (SHA-256) and `machine-code` (LEB128) on literals HEAD. No `WOr`/`WXor`. No fixture. | literals amendment, joint | gap, blocker (v) |
| BS-06 | The frozen slice tracks the post-modules closure | 72 to 95 entries; 12 uncovered by any suite | baseslice | gap, major (v) |
| BS-07 | String.length divergence between lanes | The JS lane counts code points and faults on non-scalar Chars | literals `string-unicode`; lanes | covered (s) |
| BS-08 | Nat representation and bound | Base Peano; seed compiled lanes W64 up to 2^48-1; literals unary up to 1,048,576 with O(n) operations | literals amendment; DEC-5 | risk, major (v) |
| BS-09 | Word-bodied U32 defs are intrinsics; Word helpers stay unlowered | Fails closed (`--audit-bundle` lists BaseUnchecked). The remaining gap is BS-05. | literals amendment; baseslice audit | partially covered, blocker (v) |
| BS-10 | Char/String representation | literals fixtures | literals | covered (s) |
| BS-11 | Inventory of Knot's own intrinsic cut | literals intrinsifies WShow, NShow, SEq, SReverse, SLength, SEmpty, CSpace; hosts.json records none of them | census-3 | gap, minor (s) |
| BS-12 | The foreign effects need a Knot path to host imports | io-host provides the host only | core-io, vm-design | gap, blocker (v) |
| BS-13 | Higher-rank `IO.bind`/`IO.die` | Erased at runtime; the type-level work belongs to products | products | covered, minor (v, refuted) |
| BS-14 | Base non-tail recursion at compiler scale | Under D14 the VM owns the stack. Literals' machine keeps about 349K return records in linear memory. | vm-design | partially covered, minor (v, refuted) |
| BS-15 | One runtime profile for literals, heap, closures and knot-io | Under D14 the single VM module is that profile | vm-design | partially covered, major (v) |
| BS-16 | Frontend Base slice (39 entries) | Literals registry; the frontend also needs tuples in 5 declarations | literals, products, baseslice | partially covered, major (v) |
| BS-17 | F32 and Array are unreached | census | none needed | covered (s) |

### Scale

| ID | Requirement | Evidence | Covered by | Status |
|---|---|---|---|---|
| SCALE-00 | The driver does not count output with non-tail recursion | Bun exits 1 after writing 53,216 bytes; native prints `Built 53216`; replacing the count with `0` removes the fault. Replaced by `A.length` on literals. | literals amendment | risk, minor (v); replaced on literals, pinned by the 53 KB regression |
| SCALE-01 | The catalog admits the whole book | 256 functions per book; 257 gives `Exhausted check budget`; about 650 projected | selfsource, joint | gap, blocker (v) |
| SCALE-02 | Identical options and bundle mode for A2 and A3 | `check.py:242` vs `:277`; defaults 512 and 65,536. Silent, because the judge allows the blocker. | harness-2 | gap, blocker (v) |
| SCALE-03 | Output budget and string-literal lowering | 4,193 string characters in S | vm-design (pooling); harness-2 (size) | risk, minor (s) |
| SCALE-04 | Heap sized for the bundle, with growth and reclamation | The native profiles have 1 to 2 fixed pages; the requirement moves to the VM heap | vm-design | gap, blocker (v) |
| SCALE-05 | Nat as a word with a chosen bound | Nothing pins a word; literals is unary | DEC-5, literals amendment, joint | gap, major (v) |
| SCALE-06 | Remaining non-tail recursion fits the host stack; the policy is pinned | Node default: 13,776 frames | vm-design; harness-2 (records policy) | partially covered, minor (v) |
| SCALE-07 | Per-character CPS loops in constant stack | closures `return_call`; the VM under D14 | vm-design | covered, major (s) |
| SCALE-08 | IO with guest-heap bind frames and a growable `knot_alloc` | No owner | core-io, vm-design | gap, blocker (v) |
| SCALE-09 | The output byte list fits memory without deep flattening | Folded into SCALE-00 and SCALE-08 | literals, vm-design | partially covered, minor (v) |
| SCALE-10 | Every file of S fits 65,536 characters | Largest projected file 23,793 bytes | modules | covered (s) |
| SCALE-11 | Base (67,190 bytes) loads through its own bounded path | `load.bend` reads with cap 131,073 | modules | covered (s) |
| SCALE-12 | Parser depth covers each file's declaration spine | 512 by default; `Exhausted parse budget` at 256 declarations | harness-2 (maxima); selfsource (optional) | risk, minor (s) |
| SCALE-13 | Per-body checker and emitter depth | Per function; well under V8 limits | existing profile | covered (s) |
| SCALE-14 | Loader fuel covers the import graph | About 265 of 1,024 transitions | modules | covered (s) |
| SCALE-15 | C1 compiles S within time and memory | Native lane; unmeasured on S (THIN-02) | charter, harness-2 | covered (s) |
| SCALE-16 | A2 finishes within 600 s | Unmeasured | vm-design (timing) | risk, minor (s) |

### Host

| ID | Requirement | Evidence | Covered by | Status |
|---|---|---|---|---|
| A2H-01 | Deep non-tail recursion survives in A2 | Node default: 13,728 frames. The VM owns the stack under D14. | vm-design | gap, major (v) |
| A2H-02 | Diagnose the Bun-lane memory fault note | Diagnosed as compile-cli's `List.length`; `state.json` note still open | integrate-1 | covered (s) |
| A2H-03 | IO path from Knot to knot_io | io-host defers it | core-io, vm-design | gap, blocker (v) |
| A2H-04 | Host ABI for the effects | io-host `6051e37` and `f42ae39`, unmerged | io-host | covered, major (s) |
| A2H-05 | The loader's file IO in A2 | Short reads refuted (0 in 9,000 reads). The loader now calls `path-host.inspect` (`0111f13`), which Knot's checker rejects. | DEC-1, io-host amendment, core-io | gap, blocker (v) |
| A2H-06 | Bundle command form and identical budgets | Same as SCALE-02 | harness-2 | gap, blocker (v) |
| A2H-07 | A relative bundle ROOT for hash packages | `mixed-path-roots` is Unsupported; io-host refuses absolute paths; `BEND_LIB` is absolute | harness-2 | gap, blocker (v) |
| A2H-08 | Base as a regular single-link file at its pinned relative path | Gate scratch symlinks `.toolchain`; io-host refuses symlinks | harness-2; vm-design harness | gap, major (v) |
| A2H-09 | `io-abi` bootstrap adapter | Absent. A Worker cannot capture fd writes; needs a child process. | vm-design harness; io-host amendment | gap, blocker (v) |
| A2H-10 | Knot statuses distinguishable from host statuses | `host` flag from the runtime status | io-host amendment; vm-design harness | partially covered, minor (v) |
| A2H-11 | `IO.die` semantics | Host side in io-host | core-io; vm-design IO layer | partially covered, minor (v) |
| A2H-12 | A3 fits the budgets and one `write_bytes` | | harness-2; vm-design | partially covered, minor (v) |
| A2H-13 | Memory for A2 compiling S | wasm-owned is speed track | vm-design | gap, major (v) |
| A2H-14 | Deterministic host; environment recorded | | harness-2 | partially covered, minor (v) |
| A2H-15 | Module identity kept identical in C1 and A2 | C1 side: the `path-host` foreign (`0111f13`). A2 side: Knot rejects it and knot_io has no op. | DEC-1, io-host amendment, core-io | gap, blocker (v, updated) |
| A2H-16 | Parent-relative escapes | S uses none | none | risk, minor (s) |
| A2H-17 | argv reaches A2 exactly | io-host | io-host | covered (s) |
| A2H-18 | Time budget for A2 and A3 | Unmeasured | vm-design harness | risk, minor (s) |
| A2H-19 | The census counts IO requirements | tests/compiler-io is `unrecognized-suite` | census-3 | gap, minor (s) |

### Fixpoint

| ID | Requirement | Evidence | Covered by | Status |
|---|---|---|---|---|
| FX-01 | The charter's handling of the JS-lane fault matches the code | The charter says "recorded as Exhausted"; the code counts a disagreement, fail-closed | integrate-1 (charter wording) | partially covered, minor (v) |
| FX-02 | Identical argv for C1→A2 and A2→A3 | 248 match-defs build under both argv; 249 to 256 give `Exhausted parse budget` under the bare argv | harness-2 | gap, major (v) |
| FX-03 | Bundle mode once modules merges | Single-file mode keeps import rejection | harness-2 | gap, major (v) |
| FX-04 | A frozen bundle sandbox, identical for C1 and A2 | | harness-2 | gap, major (v) |
| FX-05 | Hash-package content pinned on every host | | harness-2 | risk, minor (s) |
| FX-06 | A2 has enough memory wherever C1 does | | vm-design | partially covered, major (v) |
| FX-07 | Hosts classify traps the same way | | io-host amendment; vm-design harness | gap, minor (s) |
| FX-08 | Wall-clock guards scale with load | | harness-2 | gap, minor (s) |
| FX-09 | Runtime identity (Node, V8 flags, stack policy) pinned | | harness-2; vm-design | risk, minor (s) |
| FX-10 | Same argv semantics in C1 and A2 | | harness-2 | risk, minor (s) |
| FX-11 | C1 reproducible, build environment recorded | | harness-2 | partially covered, minor (s) |
| FX-12 | No volatile metadata in artifacts or receipts | | harness | covered (s) |
| FX-13 | Deterministic ordering | | by construction | covered (s) |
| FX-14 | Knot's U32/Nat semantics equal the seed's intrinsics | Frozen literals fixtures | literals; lanes; vm-design | partially covered, minor (v) |
| FX-15 | A2's Base helpers run in O(1) host stack at compiler scale | | vm-design; literals (`A.length`) | partially covered, major (v) |
| FX-16 | Tail calls through continuations run in constant stack | | vm-design | gap, major (v) |
| FX-17 | An independent, broad conformance corpus | enum suites only | vm-design harness; each suite as it merges | partially covered, major (v) |
| FX-18 | Diagnostics compared across generations | | harness-2 | gap, minor (s) |
| FX-19 | S is the complete compiler | The compile-cli closure includes the checker and emitter; the CLIs outside it add only `calls.partial` | integrate-1 (records S) | partially covered, minor (v) |
| FX-20 | D2 Base trust inventory recorded with the fixpoint | | harness-2 | gap, minor (s) |
| FX-21 | The harness closure equals the loader closure | | harness-2 | risk, minor (s) |
| FX-22 | A recorded deterministic generation contract | | harness-2 | gap, minor (s) |
| FX-23 | Programs run under Node and Bun | | vm-design | gap, minor (s) |
| FX-24 | The seed is used only in the seed step | | vm-design harness | partially covered, minor (s) |
| FX-25 | Knot-budget and host-resource exhaustion distinguished | Mutated receipts pass the judge with a host-Exhausted A3 | harness-2 | partially covered, major (v) |
| FX-26 | Char/String encoding of S identical across hosts | S is ASCII (0 non-ASCII bytes, 0 tabs) | io suite; lexer | covered (s) |
| FX-27 | IO error codes match between C1 and A2 | io-host's errno table is Darwin's | harness-2 (Darwin qualified) | risk, minor (s) |
| FX-28 | Size ceilings admit the self-compile | | vm-design; harness-2 | unknown, minor (s) |

### Completeness

| ID | Requirement | Evidence | Covered by | Status |
|---|---|---|---|---|
| D14-01 | Image format and C1 image emitter, deterministic | No code on any branch; vm-design is design only | vm-design | gap, blocker (c) |
| D14-02 | Checked core represents every feature of S, including IO and foreign effects; one core schema | Closures and literals extend core separately; no effect term exists | integrate-1 (schema), core-io (effect term) | gap, blocker (c) |
| D14-03 | The VM, with a Bend model, laws, differential tests and mutants; pinned toolchain | No branch; `wat2wasm` unpinned | vm-design | gap, blocker (c) |
| D14-04 | Guest frames in linear memory; identical Exhausted under Node and Bun | Node 13,781 frames, Bun 637,763 | vm-design | gap, blocker (c) |
| D14-05 | Harness and ladder on the image route | `check.py` builds `a2.wasm`/`a3.wasm`; milestones 9 and 10 describe native Wasm | integrate-1 (ladder), vm-design (harness) | gap, major (c) |
| D14-06 | In-flight increments re-scoped to D14 | Only `io-host-fix` mentions D14 | integrate-1 | risk, major (c) |
| D14-07 | Reconcile literals' instruction machine with the VM | 32,768-instruction module cap; 64 MiB with no reclamation | DEC-6, literals amendment | risk, major (c) |
| LANE-01 | Name the oracle lane; re-observe agree fixtures on the native lane | Every `regen.py` records through `bun main.ts` | lanes | gap, major (c) |
| LANE-02 | The meter measures the route actually used | The meter uses the seed's JS cut and has only check and wasm stages | census-3 | gap, major (c) |
| INT-01 | Merge order and owner; one pattern matrix | Every pair among nest, literals, closures and generics conflicts in check.bend or parse.bend | integrate-1, DEC-4 | gap, blocker (c) |
| INT-02 | Every consumer of `S.Node` handles the new variants; no silent name fall-through | qualify's `following` ends in `case _ _: names`; generics parses 187 of main's 275 defs as `TypedFunction` | modules and generics amendments, joint | risk, major (c) |
| IO-07 | knot_io serves `path-host.inspect`, or the foreign is removed | The ABI has no path op and is freezing now | DEC-1, io-host amendment, core-io | gap, blocker (c) |
| THIN-01 | Whole-file CPS loops in bounded heap | Every step allocates a continuation cell | vm-design | partially covered, major (c) |
| ORACLE-01 | VM-versus-C1 differential at compiler scale | The evaluator is capped at 1,048,576 transitions | vm-design harness | risk, minor (c) |
| THIN-02 | C1 time and memory on S measured | `e2e3.a2` is blocked at `lex literal` | harness-2 | unknown, minor (c) |

## No action

These rows need no increment. The reasons are:

- **Refuted by verification:** SF-03, SF-07, BS-04b, BS-04c, BS-13, BS-14, Q-JS-2. Their residual obligations are listed in the row that owns them.
- **Owned by an in-flight increment with no amendment needed:**
  - SF-19 (generics);
  - BS-04a, BS-04d, BS-04e, BS-04g (literals; DEC-5 covers the Nat bound);
  - A2H-04 and A2H-17 (io-host).
- **Covered:**
  - C-01 to C-10, BS-01, BS-04f, BS-07, BS-10, BS-17;
  - SCALE-07, SCALE-10, SCALE-11, SCALE-13, SCALE-14, SCALE-15;
  - FX-12, FX-13, FX-26, Q-JS-1.
- **Accepted risk:** A2H-16. S has no parent-relative import; io-host refuses escapes.

## Probe on literals `2ea222e`

These results were taken with native builds of parse-cli and check-cli from `campaign/literals` `2ea222e`. The scratch tree is `scratchpad/gap-plan/lit`.

- **Single-file parse-cli.** It still reports `Unsupported lex literal` on every file of S. Literal lexing is wired only into the bundle loader (`load.bend` imports `literal-lex.bend`), so the harness reaches it only through `--bundle` (harness-2).
- **Bundle check.** `check-cli --bundle` on each of the 32 files of S stops first at a generic parameter type (`Unsupported parse parameter-type`), which is generics' work. The exceptions are:
  - `primitive-op.bend`, which checks;
  - `src/primitive.bend`, which gives `Invalid parse function-result` at line 88 (`def all() -> List<&2,O.Op>`), a D4 violation on Knot's own source. The same form parses on generics `f39ba7e`.
- **Next blockers.** After generics, the expected first blockers on S are:
  - layout (SF-01, SF-02);
  - tuples (SF-15);
  - multi-column Nat patterns (SF-05);
  - `U32.or`/`U32.xor` (BS-05);
  - the catalog limit (SCALE-01);
  - the path-host foreign, once literals includes `0111f13`.

  integrate-1 records the actual sequence after each merge.

## Risks

1. **VM speed.** A2, the VM running I2, may take longer than the 600 s host budget to compile S. The bend-hosted design critique found the transition estimate one to two orders of magnitude low. Nothing can be measured until an image of S exists.
2. **Size caps.**
   - The size of I2 is unknown against the 1,048,576-byte output cap.
   - If literals' machine is kept, S is also unmeasured against its 32,768-instruction module cap.
3. **Merge volume.**
   - Six branches edit `check.bend` and `parse.bend`.
   - There are two pattern-matrix implementations.
   - descent-2 carries a stale copy of the nest matrix.
   - Each merge can reintroduce an Invalid on S that stays hidden behind an earlier Unsupported.
4. **Pending decisions.** DEC-1 blocks the io-host merge and core-io. DEC-2 blocks products and sugar. DEC-3 blocks generics. DEC-8 blocks core-io. Unrecorded decisions stall the critical path.
5. **Unary Nat.** The compiler's maximum output budget, 1,048,576, equals literals' unary cap, and every Nat operation is O(n) in time and cells. A word representation (DEC-5) removes both problems but must match the seed's 2^48-1 behaviour.
6. **Oracle lane.**
   - The frozen records come from the seed's JS interpreter and JS lane. They cannot witness compiler-scale runs.
   - They differ from C1's native lane on known Base semantics.
   - Until the lanes increment reports, a conformance mismatch may be an oracle artefact.
7. **Masked blockers.** Each fix exposes the next first blocker, and the census cannot see layout. The per-merge first-blocker table is the only early signal.
8. **Host parity.** Node's and Bun's stack depths differ by 46 times, and their memory-growth behaviour is not yet compared. A VM that is correct under Node may still diverge under Bun (DoD item 2).
9. **Trusted-runtime toolchain.**
   - The VM is trusted.
   - Its assembler (`wat2wasm`) is unpinned.
   - Emitting the VM from Bend would put speed-track profiles back on the critical path.
10. **Qualified host.** io-host freezes Darwin's errno table, and C1 uses OS errno. Other hosts are unqualified.
11. **Source growth.**
    - `check.bend` reaches about 24K characters on closures, against the 65,536-character per-file cap.
    - S's function count is projected at about 650 of a raised 4,096 limit.
    - Further growth needs recurring measurement.
12. **C1 cost.** C1's wall time and peak memory on S have never been measured.
13. **Review coverage.** Live Perch semantic and style review of the VM and image code depends on provider availability. A missing key is recorded as unavailable evidence, not as a pass.

## Evidence

- **Survey and verification outputs.** Workflow `wf_35f2e149-542` journal. Its probes are in `scratchpad/gap-*`:
  - features: `gap-features-*`, `gap-sf08`;
  - Base: `gap-base*`, `gap-baseslice`;
  - scale: `gap-scale*`;
  - host: `gap-host*`, `gap-a2host`;
  - fixpoint: `gap-fixpoint*`;
  - critic: `gap-critic`.
- **Plan probes.** `scratchpad/gap-plan/`.
- **Key files on main:**
  - `tests/compiler-bootstrap/check.py` (lines 39, 199-212, 242, 277, 523);
  - `tests/compiler-bootstrap/receipts/progress.json`: `e2e2.reference` reached; `e2e2.compile` and `e2e3.a2` blocked at `Unsupported lex literal`;
  - `src/compile-cli.bend:25` and `:57`;
  - `src/catalog.bend:79` and `:127`;
  - `docs/compiler-campaign/state.json:180`.
