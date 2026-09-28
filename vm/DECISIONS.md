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
  2 heap and representation (NatRange, RCOverflow, the image limits of SPEC §4:
  size, records per table, arity and `slots`; display), 3 frame region. **Quantum:** when a debit makes the count reach 65,536, the entry step
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
   be frozen (round 9: the golden `list-head-match`, entry 25, with its lane declared
   unavailable).
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
   words after IMAGE and reads them with `serializer.decimal`, which drops leading
   zeros before converting because Python's `int` refuses a string above 4,300
   digits; `serializer.arguments` selects the form by entry kind. An invocation row
   may name its FUEL word, which eval-cli receives as its budget. Golden
   `invoke-words` freezes 16 invocations, each agreeing with eval-cli (§12). Ten
   codec mutants of the grammar and its order (words after the lookup or per
   parameter, FUEL unchecked, reduction modulo 2^32, an exclusive maximum, no
   leading zeros, a ten-digit cap, the empty word as 0, other scripts' digits,
   Python's `int`) and two invocation controls are killed. What no eval-cli row
   can show (usage, whose text eval-cli spells otherwise; the Program form; a
   4,401-character word; the image before the words) is frozen in 13 argument
   controls by literal review, and five more codec mutants (usage deleted, the
   entry kind ignored, the Program's FUEL or its `--` unchecked, its FUEL read
   before its shape) are killed. vm-expected.json only
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
18. **Every read is inspected, over a stated extent.** Review round 6 found §6's
   inspection partial and evaluate.py stricter than the text. §6 listed Case
   scrutinees, prim reads, rendered words, Action operands and the final IO.OP,
   but not Construct; it said Chr yields its code word unchanged and gave Succ no
   rule for a non-Big pointer; and §9 said four conversions and `append`'s `b`
   are moved, without saying they are read. evaluate.py inspects the Succ and Chr
   operand, the moved words and every String whole (`eq`, `append`'s `b`,
   `reverse`, `length`, `is_empty`), so through a `none`-typed `id` it answered
   `HostFailure image ill-typed` where a VM following the text answers `On{}`,
   `True{}` or `False{}`. A copy of evaluate.py that followed the text (Chr and the
   four conversions return their operand, `append` conses onto `b` unread) passed
   the gate with the identical summary (.local/vm-spec/f7-text-before.log). We
   adopt the stricter rule, so that an ill-typed word never survives into a value
   the VM later trusts. §6 now lists every inspection point, the Succ and Chr
   operand among them, and says what is not inspected; checking a word is
   shallow, and a String's extent is whole, each cell and its Char word. §9's
   table gives every prim's operand types, extent and moves, and inspection
   precedes computation and allocation. §8's phase 3 reads a Halt's code and
   whole message, and §10 reads an Action's whole String before the scalar check.
   The list also names §7's check of an Enter's target, and a byte List's whole
   extent for `File.write_bytes`; the reference evaluation performs only
   `IO.print`, so vm-io owes that List's control and mutant (§12).
   Eighteen run controls freeze those points by literal review, the reviewer's
   seven probes among them (each Succ discarded by a `let`, as the Chr is, so that
   only its read can halt), with the calls §7 counts: 2 for Succ and Chr, whose
   construction is free; 3 for a prim, which sits in its Base function; 4 for a
   Halt; and 5 for the print. Eighteen evaluator mutants read less than an extent
   and exactly as much on well-typed words. Each survives every golden and every
   other control, and each dies by its own inspection control
   (.local/vm-spec/f7-mutants.log). The text-following copy now fails at
   `run control inspect-chr` (.local/vm-spec/f7-text-after.log). No golden,
   expectation or evaluate.py line changed.
19. **An image past a resource limit is Exhausted kind 2.** Review round 8 found
   §4.1, §11 and D16 making an image above 16 MiB `Exhausted` kind 2, while §4 and
   the gate made it `HostFailure image`: `decode` raised `Malformed('exhausted
   image-size')`, `rejected()` mapped every Malformed to `HostFailure image`, and
   three controls froze that. The coordinator decided for §4.1 and D16. `decode`
   now raises a distinct `Exhausted`, which `rejected()` reports as `Exhausted 2
   image-size`; the three controls were re-frozen first, in their own commit, by
   literal review. §4 now says a refused image is `HostFailure image` except past a
   resource limit, and states every limit in one table with its precedence: a count
   its structure admits and that passes its limit is `Exhausted` kind 2 (`records`,
   `arity`, `slots`), checked when the count is read and before what it governs;
   a count its structure cannot hold is malformed (`record count`, at two words
   per record, and `function record`); each limit is inclusive. Before, the record
   limit was `Malformed('record count')` and the arity and `slots` limits a
   validator failure (`limits`), none of them frozen by a control, and a Closure's
   `slots` had no limit although it sizes an Activation as a function's does. Ten
   limit controls freeze both sides (.local/vm-spec/f8-limit-mutants.log): each
   limit passed by one; a count of 2^20 + 1 records without room for them, and an
   arity of 4,097 in a record that holds two; an image of exactly 16 MiB, refused
   as `total`; 2^20 records, whose first zero word is a malformed record; a `slots`
   of 65,536 that its body does not reach, refused by step 4; and an admitted
   unused function of 4,096 parameters. Five codec mutants (a limit reported as
   malformed, an exclusive limit, the record limit before the count's fit, the
   arity limit before its record's length, a Closure's `slots` unlimited) survive
   every golden and every earlier control, and each dies only by a limit control.
   The rule mutant `rejected-limit-as-host-failure` (check-spec.py's `rejected`
   reporting the exhaustion as `HostFailure image` again) dies by `oversize`.
   `decode` now reads its words with an explicit little-endian `struct` format, so
   the 8 MiB and 16 MiB controls cost milliseconds per mutant. §8's image-first
   refusal, "`HostFailure image` whatever the words", now names the limits too.
20. **Only a documented eval bound, past its budget, excuses eval.** Review round 8
   found §11's rule unenforced for eval and its documented display bound four
   times too high. `vm_expectation` accepted any Exhausted eval lane at any
   boundary, and the three excused rows recorded only `"eval_lane": "Exhausted"`.
   §11 gave eval's display as "4,096 visits", but `describe` renders with 4,096
   worklist steps, one per item: a constructor and its opening text, then a slot and
   a separator or closing brace per field, so a tree of N constructors takes
   4N − 2 and a Nat `n` 4n + 2. The pinned eval-cli renders 1023n and refuses 1024n
   (`Exhausted inspect budget`); a 642-node tree of 100-character names renders in
   65,487 characters and 643 nodes do not (.local/vm-spec/f8-evalbound.log). §11
   now states that unit, keeping §8's visit for the VM. It also gives eval-cli's
   transitions their unit: one per term evaluated and one per successor or
   character materialized, so `Nat.is_gt(U32.to_nat(1048576),0n)` exhausts them
   although its primitive budget is inclusive at 2^20 (2^20 + 1 is `Exhausted
   primitive budget`). `check-spec.py` now matches the phase eval-cli names against
   `EVAL_BOUNDS` (`primitive`, `eval`, `inspect`), measures without eval-cli
   whether the program passes that budget (`reach`: the largest Nat or String
   length in the reference evaluation; a lower bound on transitions; the seed
   value's steps and characters), and refuses any other Exhausted. Each excused row
   records the cause, bound, budget and boundary reached (2^31, 2^31 and 2^31 + 1
   Nats past 2^20). Four expectation controls refuse an undocumented phase
   (`check`) and each budget unpassed, the Nat 1,023 at 4,094 steps among them; two
   excused controls admit the Nat 1,024 at 4,098 steps and a transitions exhaustion
   past 2^20. Four rule mutants (any Exhausted accepted, the budget not measured,
   steps counted as visits, transitions without materialization) are killed.

21. **A Book entry never performs an effect (D22).** The vm-model review found an
   admitted Book image applying `IO.print` to a continuation (a main that is
   `got(IO.print("x")(R, k))`) printing in the model, `evaluate.book` running the effect
   and dropping its output, and the seed's native lane fail-stopping. The coordinator
   recorded D22, and §7 step 2, §8 and §10 now state it: under a Book invocation the
   second application of any Action, `Enter(Action, [k])`, stops with `Unsupported vm
   effect` after its debit and before it reads, inspects or converts an operand, checks
   the foreign id or calls the host. Neither the whole-extent inspection nor D20's
   scalar check runs first, so the print of a non-scalar or an ill-typed String is
   refused the same way, as `Unsupported`, never `HostFailure`. An Action built, dropped
   or applied to its erased `R` is not an effect, and the Program entry, the only one
   that performs effects, performs them wherever an Action meets its continuation, even
   inside a pure argument of `main`. `evaluate.py` gains `Machine.entry`, and `effect`
   refuses before it reads an operand; `evaluate.book` no longer runs the effect.
   Fourteen effect controls (`effect_controls`, frozen before the change) rebuild the
   reviewers' probes on foreign-print's types: `book-print`,
   `book-print-continuation-call` and `book-print-twice` (bookio-1, bk-print and
   bookio-2) and `book-print-non-scalar` (bookio-nonscalar) stop `Unsupported vm effect`
   after 4 calls (main, IO.print, `R`, the Action), writing nothing;
   `book-print-ill-typed`, added to fix the order against the inspection, stops the same
   way after 5, and `book-args` (`IO.args`, foreign 0) after 4, added because vm-model
   answered `Unsupported vm foreign 0` for a foreign that is not `IO.print`: D22 fires
   for every foreign id, before it is checked. The pure `got(k(Unit{}))` of bk-direct
   (`book-continuation-called`), an Action built and dropped and one applied to its
   erased `R` still evaluate, after 3, 2 and 3; `program-print-in-value` (pg-print)
   prints `x` from a pure argument and then its own `t` after 11 (§12). Two fuel
   controls put the refusal after step 1's fuel test: `book-print` at fuel 4 is refused
   after its 4 debits, and at 3 its Action meets fuel 0 and stops `Exhausted` kind 1
   after 3. The refusal precedes both D20 and the inspection because a Book performs no
   effect, so no operand is converted for a host call that never happens. The order is
   this executor's reading of D22, whose text says only "before the host call"; the
   coordinator can overrule it, and the controls then change with it. Ten evaluator
   mutants (a Book that performs the effect, one that drops it silently, one that names
   the foreign it refuses, one that refuses before the debit or at fuel 0, one that
   refuses after the inspection or after D20's scalar check, one that refuses when an
   Action is built or when it meets its erased `R`, and a Program that refuses) are
   killed, each by a control of the group; the first two by every `book-print*` control.
22. **A stop after the debit keeps it.** The same review asked whether an Enter whose
   step 2 stops keeps step 1's debit. vm-model and evaluate.py kept it, but §7 was
   silent and no check counted the refused entry: a VM that refunded it, or counted
   it differently, agreed with every vm-spec check, since the goldens' `calls` were
   not frozen and the fuel controls stop on fuel. §7 now says that the debit stands
   whatever step 2 or 3 does (a D20 or D22 refusal, heap or frame exhaustion, a host
   failure): `fuel` is not refunded and `calls` counts the entry. The four D20 goldens
   freeze their `calls` by literal review, each in plan.json and expectations.json
   (`vm_calls`) and in vm-expected.json: `print-non-scalar`, `-mid` and `-wide` make 4
   entries (main, IO.print, the erased `R`, the Action applied to `k`, which D20
   refuses), and `print-non-scalar-second` 13 (main, say, IO.print, IO.bind, `R` on
   its closure, its live closure, `R` on the first Action, the Action applied to
   its continuation, which writes `a`, that continuation, `u => IO.print(s)`, IO.print,
   `R` on the second Action and the Action applied to `k`, refused). Two expectation
   controls refuse a review that refunds the refused entry (3) and one left unfrozen;
   the evaluator mutant `effect-refusal-refunds-debit` dies by the four goldens and by
   the Book effect controls, and the rule mutant `d20-calls-unchecked` by the two
   controls. Entry 15's mutant `effect-before-debit` now also dies by the D20 goldens'
   `calls` (its refused print is debited 3 times, not 4); before, only a fuel or an
   inspection control killed it.
23. **A key may be 0xffffffff.** `none` is `0xffffffff`, and neither §2 nor §3 said
   whether a keys row may carry it: a decoder that read a key word as an optional index
   would drop or misread the row. §2 and §3 now say that in a Case record `none` marks only an absent tag row (mode 0) and an absent
   default, and that a key is a plain u32, so a keys table has no absent row: a
   matching key at 0xffffffff is selected and a missing one falls to the Default.
   Three run controls (`key_controls`) freeze it, `key-max` and `char-key-max` (a U32
   and a Char at 4,294,967,295 take the key Branch) and `key-max-miss` (0xfffffffe
   takes the Default), each after 2 calls. Two evaluator mutants (a key that is
   absent, a key that is a wildcard) and a codec mutant that drops a keys row at
   0xffffffff die by them.
24. **A Halt's message is an outgoing String (D20).** vm-core refuses a Halt whose
   message holds a non-scalar Char as `HostFailure io abi` before `die`, but
   `evaluate.program` returned the Halt with its codes, and nothing in §8 or §10 said
   which was right (CORE.md, findings for the spec owner). §8's phase 3 and §10 now call
   the message an outgoing String: the code and then the whole message are inspected
   (§6), a message holding a non-scalar Char is refused as `HostFailure io abi` before
   `die`, with `w` still owned and nothing written, and otherwise the VM converts it,
   drops `w` and calls `die`. `evaluate.program` shares `outgoing` with `IO.print`.
   `halt-surrogate` freezes the refusal after 3 calls (main, the erased `R`, `k`'s
   closure), and two inspection controls freeze its order, a surrogate then `id(λ)` and
   `id(λ)` for the code beside a surrogate message, each `ill-typed` after 4. The
   success side is frozen too, at the level of values that the reference evaluation
   works at: `halt-scalar`, a Halt of code 1 whose message is `x` and U+1F600, ends with
   `halt` 1 and that `message` after the same 3 calls, so a `die` that refused every
   message, or every one above ASCII, differs. (The host's `die`, exit `code mod 256`
   with the message and LF on stderr, is IO-ABI.md's; vm-io owns it through the real
   host.) Five evaluator mutants (the check skipped, made while the message is read,
   made before the code, and the two refusals above) die by them, each by its own
   control. The frozen run has `halt` and `message` keys, a shape no earlier control
   has; the harnesses that read `cs.run_controls` must map it to `die` (below).
25. **A Book may have an unavailable core, and a Char has a tags-mode golden.**
   The round-8 hand-off left two shapes witnessed only by the codec and the model's
   agreement with `evaluate.py`: a tags-mode Case on Char (`case Chr{x}`, §3, whose
   `Chr` row binds the Char's own word) and S's Case on a List's `none`-typed head
   (`list-head-match`, whose plan was an admitted control). The seed runs both
   (`True{}`, on its Bun and native lanes). The literals head, these goldens' lane, declines both with its `check-cli` and its `eval-cli`, exit 3: `Unsupported check char-constructor-pattern` and `Unsupported parse parameter-type` (finding 4; owner literals). The closures head answers otherwise (`Unsupported lex literal`, `Unsupported parse declaration-form`) and is not consulted. They are now goldens, and the
   gate meets them without excusing Unsupported, which §11 and D4 forbid. A Book may
   lack a checked core, as a Program already does, only where its literal review
   declares the exact line in plan.json (`unavailable`, before observation); the gate requires the lane's two CLIs to print it. A CLI that prints a core, another line, another failure or no declaration is refused, and the expectation is the seed's
   value with `eval_lane` `Unsupported` and `eval_unavailable` the declared line,
   basis `seed`, never agreement. Five expectation controls (an undeclared line,
   a declaration where eval-cli agrees, another line, a Program, an Invalid Book
   lane) and three display-lane controls (`core:`) refuse each variant, and four rule
   mutants (the declaration unchecked, its cause unnamed, a core ignored, an
   undeclared Book without a core) are killed by them. `chr-pattern` is
   `Bool.and(code_is('a', 97), code_is(Char.from_u32(2147483649), 2147483649))`
   over `case Chr{x}: U32.is_eq(x, n)`: one Char immediate and one Big, so the Big
   word is both the scrutinee and the bound field, which vm-model's RC audit and
   lockstep can compare with the seed. `list-head-match` is the admitted control's
   plan, unchanged, and equal to the lowering of a display written by hand in the
   head's grammar (`LIST_HEAD_MATCH_DISPLAY`, by analogy with the display that
   check-cli prints for the same source over a monomorphic list). The coverage check
   requires a tags-mode Case on Char. The `first-code` shape stays owed a golden.
26. **A real eval lane that exhausts by transitions.** Review round 8's rule excused
   an eval lane by a documented bound but froze the transitions case only through a
   fabricated observation (`u32-to-nat-big` given an `Exhausted eval` line). The seed
   golden `nat-transitions`, `Nat.is_gt(U32.to_nat(1048576),0n)`, is the real
   observation: check-cli prints a core, and eval-cli reports `Exhausted eval budget`
   although its Nat 2^20 is inside the inclusive primitive budget. The gate measures
   1,048,585 transitions past the 1,048,576 budget, and the VM owes the seed's
   `True{}`. It parses as `Unsupported` on the main-line parser (a `declaration-form`),
   never `Invalid`.

## What vm-model and vm-core must now follow (round 9)

Each item names the SPEC text and the controls that freeze it; `check-spec.py`'s
`run_controls`, `plan_controls` and goldens are the shared harness, so merging this
branch brings all of them.

1. **D22 (§7 step 2, §8, §10; entry 21).** Under a Book entry `Enter(Action, [k])` stops
   `Unsupported vm effect` after its debit, before any operand is read, inspected or
   checked for D20, before the foreign id is checked and before any host call, for every
   foreign (`book-args`). Building an Action, dropping it and applying it to its erased
   `R` stay free, and the Program entry is unchanged (`program-print-in-value`, 11
   calls, `x\nt\n`). Controls: `book-print`, `book-print-continuation-call`,
   `book-print-twice`, `book-print-non-scalar` and `book-args` (4 calls),
   `book-print-ill-typed` (5), `book-continuation-called` (3), `book-action-dropped` (2)
   and `book-action-erased` (3); `book-print` at fuel 4 is refused and at fuel 3 stops
   `Exhausted` kind 1 after 3 (`fuel-book-effect-exact`, `fuel-book-effect-short`).
   vm-model performs the print under a Book today and names a foreign that is not
   IO.print `Unsupported vm foreign N` at the Action's application; both change, D22
   first for every foreign. vm-core refuses every foreign id but IO.print at load
   (CORE.md choice 2), so `book-args` is refused before any entry today: a Book image
   with another foreign must load and stop at the effect step with D22's cause, and the
   load-time refusal stays for Program images until vm-io. Its Action branch in `$enter`
   performs the effect through `$perform`; the Book guard goes before it, after
   `$debit`.
2. **The debit stands (§7; entry 22).** A step 2 or 3 stop keeps step 1's debit: compare
   `calls` at every stop. The D20 rows of vm-expected.json now carry `calls` (4, 4, 4
   and 13). vm-core records each golden's `calls` but compares none to a frozen value
   (`expected_dump` carries none): it must now. vm-model compares the reference
   evaluation's counts, which are the frozen ones.
3. **A Halt's message is an outgoing String (§8 phase 3, §10; entry 24).** After the
   code and the whole message are inspected, a message holding a non-scalar Char is
   `HostFailure io abi` before `die`, with `w` still owned; otherwise it is converted,
   `w` dropped and `die` called (vm-core's choice 9 order is now normative). vm-core
   already refuses; vm-model's `Died` path does not. Controls: `halt-surrogate` (3
   calls), `inspect-halt-after-surrogate` and `inspect-halt-code-first` (`ill-typed`
   after 4), and `halt-scalar`, a Halt of code 1 and message `x` and U+1F600 that ends
   `halt` 1 with that `message` after 3, so a `die` that refuses every message, or every
   one above ASCII, differs. `halt-scalar`'s frozen run has neither `exit` nor
   `outcome`, only `halt` and `message`: vm-core's run-control branch (`want = ... if
   'exit' in run else expected_run(run)`) and vm-model's `agrees` read one or the other,
   so both must map it to the host's `die` (exit `halt mod 256`, the message and LF on
   stderr, IO-ABI.md).
4. **A key may be 0xffffffff (§2, §3; entry 23).** `key-max` and `char-key-max` take the
   key Branch, `key-max-miss` the Default, each after 2 calls (vm-model already has its
   own controls).
5. **Three new goldens (§11; entries 25 and 26).** `chr-pattern` (a tags-mode Case on
   Char, immediate and Big), `list-head-match` and `nat-transitions`, each owing the
   seed's `Evaluated 0 1 True{}`. Their vm-expected.json rows carry `eval_unavailable`
   or `eval_bound` beside `basis` `seed`; harnesses that read rows by key are
   unaffected. The counts are 96 goldens and 60 run controls, which vm-core's gate reads
   from SPEC §12.

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
   char-constructor-pattern` for `case Chr{x}`. Tag dispatch on Char (§3) has its
   golden, `chr-pattern` (entry 25), which the seed runs and the literals head declines; the gap stays open. Owner: literals.
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
   removing it would hide them. Round 5 added no `.bend` file. The round-5
   re-review's two goldens change it, as measured by the gate runner after
   `5bd0f9b` against the same receipt: 884 files, `Parsed` 163 (`invoke-words`)
   and `Unsupported parse declaration-form` 283 (`nat-case-big`). Every other
   count, the six Invalid rows included, is unchanged, and both files agree across
   the seed's native and Bun lanes. Round 9's three goldens change it again, as
   measured by the gate runner (all 21 gates passed) after `ec961e9` against the
   same receipt: 887 files, `Unsupported lex literal` 214 (`chr-pattern`, at its
   `'a'`) and `Unsupported parse declaration-form` 285 (`list-head-match` and
   `nat-transitions`). No row is `Invalid`, so the six stay six, every other count
   is unchanged, and both files agree across the two lanes. The merge condition
   stands, and no shared bootstrap receipt was refreshed.
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
