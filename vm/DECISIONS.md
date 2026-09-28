# D15–D18: proposed exact wording, and points for the coordinator

D15–D18 were adopted at `454bf30` in `docs/COMPILER-CAMPAIGN.md`. The wording below
is what [SPEC.md](SPEC.md) implements; it refines the adopted rows without
changing their direction. This executor does not edit the campaign decision table,
except the D20 row, rewritten at the coordinator's round-4 direction.
D19, adopted on main after this branch's base (`b926a3c`), replaces the 2,048-page
(128 MiB) memory bound with a declared 65,536-page (4 GiB) maximum; the spec
follows it (§5, §10, §11) without a new image header word.

- **D15 (Nat).** Nat is the mathematical range 0..2^32-1, held in the VM's
  canonically boxed scalar word (immediate below 2^31, a Big cell from 2^31). Every
  Nat result is checked before narrowing; a result above 2^32-1 is `Exhausted`
  kind 2 with cause `NatRange` in the VM's own outcome, never U32 wraparound. U32
  still wraps. Pure Char keeps every u32 code, non-scalars included; scalar
  validation happens only at IO. Witnesses: `nat-big` and `u32-to-nat-big`
  (inside the bound; the VM owes the seed's `True{}` although eval-cli is
  exhausted at 2^20) and `nat-range`, `nat-mul-range` and `nat-succ-range` (the
  VM owes `Exhausted NatRange` although the seed's native lane succeeds).
- **D16 (fuel).** One unit per entry: the requested Book function or Program
  `main`, every Application, every Invoke including erased ones, both applications
  of an Action, and every continuation application including the terminal one.
  The debit happens after the operands are evaluated and before the entry. Prims,
  constructors, lets, cases, RC and rendering cost nothing. At fuel 0 the pending
  entry stays in the state and no effect happens. Exhausted kinds: 1 fuel,
  2 heap and representation (NatRange, RCOverflow, image size, display), 3 frame
  region. **Quantum:** when a debit makes the count reach 65,536, the entry step
  completes and dispatch returns to `knot_main`, which resets the count and
  re-enters. For an Action applied to its continuation, that step performs the one
  effect and leaves the continuation's entry pending; there is no separate
  "perform" state, so the effect still runs exactly once across the yield.
- **D17 (knot-io-2).** knot-io-1 plus `read_bytes` (raw bytes, no decoding),
  `path_identity` (modules' `path-host.bend` `inspect`, whose C and JS bodies at
  `0111f133` are hash-pinned in `vm/registry.json`), and `exhausted(3)`. io-abi-2
  owns the payload and precedence; VM IO acceptance waits for that contract. An
  image may already encode the foreign id; that is not IO conformance.
- **D18 (literals' machine).** `knot-literals-wasm-1` and its emitters stay frozen
  in S as a native profile whose modules must stay byte-identical inside the VM.
  knot-vm-1 is a separate runtime for knot-image-1, with uniform RC and immortal
  constants from the start; it is not a growth of that machine.

## Refinements of VM-DESIGN.md, for review

1. **Case tables.** VM-DESIGN says Case gets a dense tag table at encode time,
   and the earlier draft duplicated a catch-all's Default body once per missing
   tag. The spec keeps the dense table but writes `none` for a missing tag and
   stores one Default child, present exactly when some row is `none`. No node is
   shared or copied. U32 and Char cases use sorted sparse keys plus a required
   Default, which is the literals core's form.
2. **Header.** 32 words: the representation table has 12 entries (Nat, U32, Char,
   String, Bool, Cmp, Unit, List, Result, Sigma, IO.OP, File). Prim results,
   IO results and the terminal `Emit` need the pinned Bool, Cmp, Result, Sigma,
   List, Unit and IO.OP indices, and a name is never authority.
3. **U32 is opaque.** The literals loader models U32 as a datatype with one
   nullary constructor `#U32`; the image does not encode that constructor. U32
   and Char literals, which the literals core represents as `Value{type,n}`, are
   image Literals with U32 or Char constants.
4. **Compact frames.** `[values, node, aux, head]`, head on top, 3 words plus
   values. The earlier draft's 8-word frame header would have needed 24 MB for
   the required 250,000-deep non-tail recursion, above the 16 MiB region; the
   compact layout needs 12 MB. The release worklist lives in the frame region
   above the top frame, so its overflow is also kind 3.
5. **Tail entry releases first.** A tail entry drops the caller's Activation
   before allocating the callee's, so a tail loop reuses one cell. Every other
   substep order is fixed in SPEC §5–§7 because lockstep compares addresses.
6. **Program driver.** A Top frame sequences the Program: `main`, its erased `R`
   application, its application to the immortal terminal continuation, then
   Emit (exit 0) or Halt (`die`). Program images must carry the Unit, String and
   IO.OP representations; the reference validator enforces it.
7. **Seed lanes.** The seed's native lane is the reference, as for C1. Its Bun
   lane is a cross-check whose documented bounds now include unary Nat
   materialization: `nat-big` passed 60 GB of RSS in about 6 minutes on that
   lane and was stopped.
8. **Book results are statically describable or Unsupported.** Review round 2
   replaced round 1's `HostFailure invoke scalar-result` bound, and the run-time
   `function-result` and `abstract-result` outcomes, with one predicate on the
   requested function's result type (SPEC §8): algebraic with describable fields,
   recursively. A U32, Char or String anywhere in the type, an arrow or a `none`
   field makes the invocation `Unsupported invoke result-type` before any entry.
   A bound is a declared domain or budget limit and is always Exhausted; an
   Unsupported result is D4's refusal, never a bound. Of the 76 Book goldens only
   `result-u32` falls outside the domain, so no other expectation changed. Three
   goldens frozen in round 2 witness a U32 field, Char and String; a `none` field
   and an arrow are witnessed by describe controls, because neither pinned head
   produces a checked core for a generic result, and a closure result would add
   another main-line `Invalid parse function-result` row (finding 5).
9. **A Case may inspect an erased position.** Review round 2 relaxed §3's
   scrutinee rule from "the slot's type equals the concrete scrutinee type" to
   "the scrutinee type is concrete and the slot's type is it or `none`". Round 1's
   rule refused S's own shape: 79 nested patterns on generic fields across 14 of
   S's files, such as `catalog.bend`'s `case Con{+head,+tail}: match head: …` and
   `check-cli.bend`'s `case Done{P.Parsed{value,rest}}`. The Case still inspects
   the word against its scrutinee type (§6.1), so this admits no new unsoundness
   beyond what `none` instantiation already allows. Neither pinned head checks a
   `List<T>` parameter (literals: `Unsupported parse parameter-type`), so the
   shape is witnessed by the admitted control `list-head-match` until a golden can
   be frozen.
   Review round 5 found the arm rule refusing S the same way: "a Case and every
   arm body" agreed exactly, and List pins `Con{none, List}`, so a Case whose Nil
   arm is concrete and whose Con arm returns the head had no legal type. S has the
   shape three times: `literal.bend`'s `first_code` (`0` or the head),
   `imports.bend`'s `first` (`""` or the head) and `base-pin.bend`'s `nth` (`0` or
   the word). §3 now lets every arm body, Branch, key Branch or Default, fit its
   Case, with the `fits` of Application, Construct and Invoke, and keeps exact
   agreement for a Reference and its slot and a Let and its body. A value fitting
   into a Case is laundered no further than one passed to a call. A Case takes the
   type of the position it fills, the positional rule §3 already states for
   `none`; all 91 goldens already had that type. A Branch slot takes its
   constructor's pinned field type, as `validate` did, never the core binder's
   instantiated type, and `check-spec.from_display` now agrees: it types Branch
   slots by the pinned field (cross-checked against a concrete binder), Let slots
   by the value's node and Cases by position, while a nested Case still names the
   core's type as its scrutinee. The admitted plan control `first-code` (seed
   `True{}` for the same source) is also the lowering of its hand-written display,
   which neither the old last-arm Case type nor a core-typed binder reproduces.
   Positional typing makes plans canonical; validation checks only fit, so
   `first-code-none-case` (the same Case typed `none`) is admitted too, and
   `key-arms-none` answers a `none` parameter from a key Branch and a Default. A
   refused control `branch-body-type` (a Bool arm in the U32 Case) and three codec
   mutants (`validator-exact-arm-type`, killed by `first-code`,
   `validator-exact-key-and-default-type`, killed by `key-arms-none`, and
   `validator-ignores-branch-body-type`) pin both directions.
10. **Non-scalar output is a divergence by contract (D20).** Review round 3 found
   §11's reference lane and §10's IO contract in conflict: the seed's native lane
   writes a non-scalar Char as generalized UTF-8 (`print-non-scalar`, ASCII source
   `IO.print(SCon{Chr{55296}, SNil{}})`, bytes `ED A0 80 0A`), while `knot-io`
   refuses it. Under D20 the VM refuses the whole String as `HostFailure io abi`
   before the host call (§10); the golden keeps the native bytes as hex, is marked
   `divergent-by-contract (non-scalar output)` and is never counted as agreement
   (§11). The seed's Bun lane refuses the same output and is recorded beside it.
   `print-non-scalar-mid` (`"a\u{D800}b"`) pins that no part of the String is
   written. The next review found the native bytes unfit to classify: the lane
   truncates the lead byte of a code at or above 2^21, so `Chr{67237376}`
   (0x401F600) prints `F0 9F 98 80`, the valid UTF-8 of U+1F600, and a rule that
   decoded those bytes owed the emoji (`print-non-scalar-wide`). Round 3 then made
   the Bun lane the witness, but review round 4 showed that it refuses a
   non-scalar Char where `char_new` constructs it, printed or not: it refused
   `non-scalar-code` (native `55296\n`) and `non-scalar-unprinted` (native
   `a\nnonempty\n`, Bun `a\n`), which print only scalars, and wrote nothing for
   `print-non-scalar-second`, where the VM writes `a\n` first. The coordinator's
   round-4 decision makes the program's value the classifier: the reference
   evaluation of the plan (`evaluate.py`, §6–§10 on values) yields the Strings
   passed to `IO.print`, and D20 applies exactly when one holds a non-scalar Char.
   Both seed lanes are recorded observations. The native bytes must equal the
   whole trace in the lane's own encoding, whose truncation of the lead byte from
   2^21 was measured on 19 codes; the Bun lane's output must be a prefix of the
   VM's. Eleven expectation controls refuse undeclared non-scalar output (the wide
   code included), a divergence on scalar output, another class, a VM that writes
   the non-scalar String or less than the earlier prints, the wide plan printing
   U+1F600, a built but unprinted surrogate declared as a divergence, other native
   bytes, Bun output beyond the VM's and a native lane without its Bun record.
11. **Plans spell a String as its code list.** Round 3 also found the reference
   codec lossy: plans spelled String constants as JSON text, so `json.loads`
   merged a surrogate pair into U+1F600 and decode refused codes above U+10FFFF
   that encode wrote. Plans and decode now use code lists, encode refuses a text
   spelling, and seven admitted code-list controls and two goldens
   (`string-surrogate-pair`, seed `False{}`; `string-beyond-unicode`, seed `1n`)
   pin §2's "every u32 code, in order". No committed image changed.
12. **Enter checks its operand count.** The next review laundered arrows through
   `id(x: none) -> none`: `fits` lets a `none` value flow into either arrow kind,
   so validation admits an erased closure invoked live, a live closure invoked
   erased (its body reads a slot never filled) and a Program's `k` invoked erased
   (`Enter(terminal, [])`), and §7 said nothing about any of them. §7 step 1 now
   halts with `HostFailure image` (`ill-typed`) before the fuel test unless a
   Closure takes exactly its `live_argument` operands, an Action zero or one and
   the terminal continuation one; Program phases 1 and 2 use the same check.
   `fits` stays loose: a generic function instantiated at an arrow type returns
   a `none`-typed value into an arrow-typed node (§3). No golden exercises that
   (every golden still validates when `none` never fits an arrow), so the run
   control `arrow-through-identity`, `id(λx. x)(On{})`, is the one that kills
   such a mutant. The same review showed that U32 and File may name one opaque
   type; that is admitted, with an ordinary run, because the pair has no pinned
   shape and a `none` value already delivers a U32 word to a File position,
   where the host refuses an unknown token as `HostFailure io handle`. Seven run
   controls freeze these runs for vm-model and vm-core.
13. **Book invocations follow eval-cli's walk.** Review round 4 found §8's "as in
   eval-cli" unwitnessed and out of order: no golden passed an ordinal, and
   eval-cli walks the live parameters left to right, so `f 5` with a missing
   second ordinal is `argument-range`, and `h 1 0` with a leftover is
   `structured-argument`. §8 now states that walk: `unknown-export`; per live
   parameter, a missing ordinal (`argument-arity`), an arrow (`function-argument`,
   the closures head's cause), a tag at or beyond the constructor count
   (`argument-range`) and a constructor with a live field (`structured-argument`);
   then leftover ordinals (`argument-arity`); last the describe domain. An opaque
   type has no constructor, so U32 and File refuse every ordinal: admitting a U32
   ordinal as a scalar would also forge File tokens, since the two may name one
   opaque type (run control `u32-file-alias`). A `none` parameter refuses for the
   same reason. The pinned heads check neither File nor generic Book parameters
   (`Unsupported parse declaration-form` and `parameter-type`), so those two
   verdicts rest on this rule alone. Goldens `invoke-args` (23 invocations) and
   `invoke-arrow` (5) freeze every cause beside eval-cli's answers, the reference
   predicate is `serializer.invocation`, and six codec mutants of its order are
   killed.
14. **A display visit is one rendered constructor.** Review round 5 found §8's
   "1,048,576 visits and 16 MiB of text" undefined for a Nat word and silent on
   inclusivity, and the gate's two readings apart: `evaluate.describe` charged a
   Nat word `n + 1` visits, while `check-spec.described` admitted any Nat up to
   1,048,576 and counted neither Objects nor bytes, so a Book golden returning
   `1048576n` was derived as a printed value that the reference evaluation
   exhausts. For `1,048,576 <= n <= 2,796,201` the readings give different
   frozen outcomes. §8 now charges one visit per rendered constructor (a Nat word
   `n` is `n + 1`, its logical view), counts the `tree`'s bytes with separators,
   and admits both bounds inclusively. `describe` counted no separator bytes and
   built a Nat's text before its check; both are fixed. `described` applies the
   same rule to the seed's value. Four run controls meet each bound exactly and
   pass it by one, two seed controls refuse one visit and one byte beyond, and four
   evaluator mutants (each bound exclusive, a Nat as one visit, separators free)
   are killed. No expectation changed.
15. **Fuel runs out at a frozen boundary.** The targeted round-5 re-review found
   D16 unwitnessed: no golden, run control or mutant reached fuel exhaustion, so
   the evaluator mutants `if False:` and `if self.fuel <= 1:` of `debit` left the
   gate's summary unchanged, and a vm-core whose fuel never ran out, or ran out one
   entry early, passed every frozen check. §7 now states the boundary: a run
   completes with fuel equal to its calls, and one unit less stops its last entry
   after one call fewer; the operand check precedes the fuel test; an Action is
   debited before its effect and `k` after it. Eleven run controls freeze it by
   literal review of `recursion-map` (6 Applications), `closure-nested` (its last
   entry an Invoke), `foreign-print` (5 entries: at 4 `vm\n` is written and `k`
   stops, at 3 the Action's second application stops before its effect), a Book
   and a Program at fuel 0, and two ill-typed Enters that meet fuel 0. Five
   evaluator mutants (fuel that never runs out or runs out early, the effect
   before the debit, the fuel test before the operand check, a free terminal
   continuation) survive with those controls withheld and each dies by one. Run
   controls now carry their fuel, and the receipt records each one's argv. No
   golden or expectation changed.
16. **Book arguments are decimal u32 words, read before FN.** The same re-review
   found §8 silent on the syntax of FUEL and the ordinals, and its order against
   eval-cli, which reads every word with Base's `U32.read` before it looks the
   function up: `absent x` and `two F 9 x` answer `HostFailure arguments
   expected-u32` there, where §8 said `unknown-export` and `argument-range`. No
   frozen invocation had a malformed word, so vm-core, vm-model and eval-cli could
   each read another grammar; a host parsing with `>>> 0` would admit `4294967297`
   as 1. `U32.read` admits exactly the nonempty ASCII digit strings of value at
   most 2^32-1, leading zeros included: its test `(10·acc + c - 48) mod 2^32`
   divided by 10 equals `acc` only for a digit `c` that does not overflow. §8 now
   defines that word, names its cause, and makes it step 1, before
   `unknown-export`. It also fixes what surrounds it: the image is validated
   first, because its entry kind selects the Book or Program form, and a missing
   word is `HostFailure arguments usage`. eval-cli spells its usage refusal
   differently and caps its budget at 1,048,576 transitions; neither is compared,
   and every frozen budget stays within the cap. `serializer.invocation` takes the
   words after IMAGE and reads them with `serializer.decimal`; an invocation row
   may name its FUEL word, which eval-cli receives as its budget. Golden
   `invoke-words` freezes 16 invocations, each agreeing with eval-cli (§12). Ten
   codec mutants of the grammar and its order (words after the lookup or per
   parameter, FUEL unchecked, reduction modulo 2^32, an exclusive maximum, no
   leading zeros, a ten-digit cap, the empty word as 0, other scripts' digits,
   Python's `int`) and two invocation controls are killed. vm-expected.json only
   gains rows; the earlier invocations' argv already carried `1000000` as FUEL.
17. **A Nat Case's predecessor is moved, and made only when bound.** The same
   re-review found §6.1 leaking. It made Succ's field `n - 1` at selection,
   allocating a Big from 2^31, and then `dup`ed every field into its slot:
   allocation writes rc 1, the dup made it 2, and the Scope pop left one
   reference without an owner. That contradicted §12's zero-leak obligation and
   left the allocation point, and with it §5's lockstep addresses, to each
   implementer. Checked source reaches it: `nat-case-big` (seed `True{}`) binds
   `p = 2^31` from `U32.to_nat(2147483649)` and passes it to `Nat.is_eq`. By
   §5–§7 the Big is allocated with rc 1, `dup`ed by the Reference (2), dropped
   when `check`'s Activation ends at its tail entry (1), `dup`ed and dropped by
   the Intrinsic, and freed with `Nat.is_eq`'s Activation; under the old text one
   reference remains. §6.1 now separates selection, which reads a tag and
   allocates nothing, from binding after the Scope push. An Object's fields and
   Chr's code word are `dup`ed, since the scrutinee keeps them. The predecessor
   is made only for a selected Succ Branch, as an immediate below 2^31 or a Big
   allocated then, and moved into its slot. A Default or Zero arm makes none: run
   control `nat-default-big`, a tags-mode Nat Case on 2^31 + 1 whose Succ row is
   `none`, would otherwise leak an eager Big. It is image-only, since the pinned
   checker lowers `case _:` on Nat to a binding Branch. The allocation follows
   the push, which orders frame-region (kind 3) before heap (kind 2) exhaustion.
   The reference evaluation has no RC, so this gate checks only the two values;
   the evaluator mutant `nat-predecessor-narrowed` (31 bits kept) survives every
   other golden and dies by `nat-case-big`, and §12 binds vm-model's zero-leak
   audit to both.

## Findings that need an owner

1. **A D4 classification defect in the literals head.** For
   `def main() -> IO(Unit): IO.print("vm")`, which the seed runs, both `eval-cli`
   and `check-cli` at `2ea222e` report `Invalid parse function-result`. D4 requires
   Unsupported. The goldens `foreign-print` and `io-bind` record the observation
   as it is; their plans are hand-built from §1's rules because no Knot core
   exists for them. The literals owner, or io-check, should fix the
   classification. The same `Invalid parse function-result` answers generic
   result types the seed prints: `def main() -> List<Flag>` (seed `[On{}]`),
   `-> Bool & Bool` (`(True{}, False{})`) and `-> Result<Bool,Bool>`
   (`Done{True{}}`).
2. **The speed gate needs vm-rc.** The frozen workloads allocate far more than
   they keep live. By SPEC §5's size rule, without release `deep-recursion` alone
   allocates 10^9 Activations of at least 16 bytes (16 GB), `peano` at least
   2×10^8 Succ Objects of 32 bytes (6.4 GB) and `list-fold` at least 2.4×10^8 list
   cells of 32 bytes (7.7 GB), each beyond D19's 4 GiB maximum; the other three
   are unmeasured.
   vm-lockstep's first ratio gate therefore needs vm-rc first, or separate
   bump-sized variants frozen by the coordinator.
3. **parse-cli over S stops early.** The literals head's `parse-cli` uses the
   literal-free lexer, so all 34 files of S end Unsupported (28 at a literal, 6 at
   a declaration form). The recorded counts are the byte-identity targets for
   E2E-2 today, not an A2(S) cost basis.
4. **No Char constructor pattern.** Knot reports `Unsupported check
   char-constructor-pattern` for `case Chr{x}`, so tag dispatch on Char (§3) has no
   golden yet.
5. **The main-line parser classifies six closure goldens Invalid.** The tree's
   own `src/parse-cli.bend` (before closures merges) reports
   `Invalid parse expected-=` for the arrow-typed lets in `closure-capture-off`,
   `closure-capture-on`, `closure-captures` and `closure-shadow`, and
   `Invalid parse function-result` for the arrow results of `closure-nested` and
   `closure-return`. The seed runs all six, and the closures head parses them.
   The bootstrap gate enforces D4 only on `src/`, so it passes, but its corpus now
   records these outcomes: its `progress.json` and `reference.json` receipts drift
   semantically, and this increment leaves them unrefreshed as shared receipts.
   Measured by the gate runner on this branch in review round 4 (after `fc17357`)
   against main's committed receipt, the parse histogram moves from 785 to 882
   files: `Parsed` 144 to 162, `Unsupported lex literal` 185 to 213,
   `Unsupported parse declaration-form` 239 to 282, `parameter-type` 57 to 59,
   `Invalid parse expected-=` 2 to 6 and `Invalid parse function-result` 8 to 10.
   Exactly these six goldens account for the new Invalid rows; the 23 goldens of
   review round 1, the 3 of round 2, the 4 of round 3 and the 5 of round 4 all
   end Unsupported. The six rows added since round 3's count of 876 (three `lex
   literal`, two `declaration-form`, one `parameter-type`) are round 4's five
   goldens and round 3's later `print-non-scalar-wide`. **When the coordinator refreshes these
   receipts, the six Invalid rows must not be accepted as a baseline.** Owner:
   merge-wave, whose closures merge should turn them into parses or Unsupported
   first; otherwise the refresh records them as known D4 debt with that owner.
   Review round 5 confirmed this as a **merge condition** on the coordinator's
   `npm run gates:refresh` for main, not executor rework: no gate stops a refresh
   from absorbing the rows, and `vm/golden/` stays in the bootstrap corpus, since
   removing it would hide them. Round 5 added no `.bend` file, so the histogram
   above stands.
6. **Frozen evaluator snapshots.** Pinning the two heads separately makes this
   gate reproducible before merge-wave, but it does not qualify their combination.
   After merge-wave, the goldens' plans should be re-derived from the merged
   checker's display, which is the same check this gate runs today.
7. **eval-cli reports an InternalFailure for results it cannot describe.** The
   literals `eval-cli` at `2ea222e` reports `InternalFailure eval result-tag` for a
   Book result that is, or contains, a U32, Char or String, although `check-cli`
   reports `Checked` and the seed prints the value: goldens `result-u32` (seed
   `5`), `result-u32-field` (`Box{5}` with `type Box is Data: Box{item: U32}`),
   `result-char` (`'a'`) and `result-string` (`"ab"`). SPEC §11 counts an
   InternalFailure as a broken invariant; under D4 a result Knot cannot describe
   is Unsupported, which is what knot-vm-1 reports (`Unsupported invoke
   result-type`, SPEC §8). Owner: literals.
8. **eval-cli reports a HostFailure for a closure result.** The closures `eval-cli`
   at `a1d6891` reports `HostFailure invoke function-result` for
   `def main() -> Flag -> Flag: x => On{}`, which its `check-cli` reports `Checked`
   and the seed prints as `x => On{}`. The image and invocation are well formed,
   so under D4 this too is Unsupported, as knot-vm-1 reports it. Owner: closures,
   or merge-wave when it merges them.
9. **A style preflight blocker: `vm/bench/sha256-64k.bend::Digest`.** The
   offline preflight over the branch's 87 changed Bend files (`git diff
   --name-only main...HEAD -- '*.bend'`; 207 declarations) exits 3 with one
   structural blocker: `Digest` (a datatype, line 5, 2,277 state bytes) has a
   truncated context (`caller-or-byte-limit`), so Anticipation and Payoff are
   unavailable and it cannot pass automatically; its supporting role is also
   impossible. It has existed since `6c4f284`, and round 1 reported only a
   23-file subset. The file is hash-pinned by `bench/workloads.json` and is not
   restructured to fit the preflight. Owner: the coordinator, who should review
   `Digest` explicitly in the live style pass or record it as unresolved in the
   style state. The task context is unavailable (`missing_task_context`), which is
   advisory; the composition is available (18,837 of 48,000 bytes).
10. **eval-cli reads what the image drops at invocation.** Both answers are
   recorded as declared divergences on `invoke-args`, and knot-vm-1 follows the
   image (§8). (a) The literals `eval-cli` admits `is_zero 0` for an
   `x: U32` parameter as the value 0, because its loader models U32 as one
   nullary constructor `#U32`, while refusing every other U32 ordinal as
   `argument-range` (`opaque-parameter`). (b) It refuses `real 0`, where
   constructor 0 of `Ghost{-proof: Flag}` has only an erased field, as
   `structured-argument`, since it counts erased fields; the image has none and
   admits the value (`erased-field`). Under D4 neither is a source error. The
   owner is literals, or merge-wave when the invocation walk is shared; the fix
   is to walk live fields and treat U32 as having no ordinal.
