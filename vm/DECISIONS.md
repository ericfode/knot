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
  "perform" state, so the effect still runs exactly once across the yield. *(Round 11, D23: an
  Action's application builds a request instead, and Top's loop performs it in one Return-to-Top step that
  ends with `Enter(k, [r])` pending. The effect still runs exactly once across a yield; SPEC §7 has the text.)*
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
   the loop that performs each request the run returns and enters its `k` (D23), until Emit (exit 0) or Halt (`die`). Program images must carry the Unit, String and
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
   beyond what `none` instantiation already allows. That reading of a scrutinee was
   frozen by no control until the review of round 9 (entry 29): the reference evaluation
   refused a closure or an Object of another type there, and nothing checked it. Neither pinned head checks a
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
   continuation) survive with those controls withheld and each dies by one (round 10:
   the free terminal continuation now also dies by the print controls, which count that entry). Run
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
   *(Round 14, entry 38: that is the order of the checks and no order of effects; a heap stop
   leaves no Scope pushed.)*
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
   Eighteen run controls froze the Succ and Chr operands, the moved and String prims,
   a Halt's code and message and the print (not the Case scrutinees, the word prims,
   `show`, the Enter targets, the rendered words, the Action's continuation or the run's
   last word, which entry 29 adds) by literal review, the reviewer's
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

21. **A Book entry never performs an effect (D22).** *(Round 11: D23, entry 31, replaced this
   entry's mechanism. The outcome stands, a Book performs nothing, but the refusal is no longer
   made where the Action meets `k`: a Book builds the request and refuses when a read meets it,
   one entry later, so the counts, the order question and the ten mutants below are restated
   there.)* The vm-model review found an
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
   that performs effects, performs them where an Action meets its continuation (entry
   27). `evaluate.py` gains `Machine.entry`, and `effect`
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
   printed `x` from a pure argument and then its own `t` after 11; entry 27 withdrew it
   and `program-print-through-id` replaced it (§12). Two fuel
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
   inspection control killed it. *(Round 14, entry 38: the debit is the one change that a stop
   leaves; the Enter stays pending with everything else as it was.)*
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

27. **A Program's effect in an argument is witnessed by the seed; a Case over an applied
   effect is not frozen.** Review of the round-9 branch found the run control
   `program-print-in-value` (`main = say(got(IO.print("x")(R)(k)))`, `x\nt\n` after 11, "even
   inside a pure argument of `main`") contradicted by the pinned seed. Its source analogue

   ```
   def got(x: IO.OP<Flag>) -> Flag:
     match x:
       case Emit{v}: v
       case Halt{+c, +m}: Off{}
   def say(f: Flag) -> IO(Unit):
     match f:
       case Off{}: IO.print("f")
       case On{}: IO.print("t")
   def main() -> IO(Unit):
     say(got(IO.print("x", Flag, u => Emit{On{}})))
   ```

   ends `bend: runtime fail-stop` with exit 1 and no stdout on the seed's Bun lane and on
   its native lane alike (`scripts/bend-reference F.bend`, then `-o F.native && ./F.native`,
   re-run in this review round), and the seed's own test `tests/io/request_out_of_band.bend` pins
   why: an applied foreign effect answers a request that only the event loop decodes, so a
   Case that names both constructors over it is refused in every lane and the effect never fires (round 12: a Case
   with a catch-all is not, entry 33). The clause "even inside
   a pure argument of `main`" was this executor's addition in entry 21. D22 says only that a
   Book never performs an effect and that the Program entry is the only one that does; the
   coordinator's round-9 item 1 needed only that the same Action print under a Program, which
   the seed-run golden `foreign-print` already witnesses. §11 owes the seed's value where the
   seed succeeds, and a frozen MUST of an effect that the seed refuses had no basis in it.
   The seed's refusal begins where a Case reads the answer: `run(m) = λ@R. λk. m(R)(k)` and
   `run(m) = λ@R. λk. id(m(R)(k))` (a generic `id` over the IO.OP) both print `x` on the two
   lanes (exit 0, bytes `78 0a`), while a match that rebuilds `Emit` and `Halt` fail-stops like the one above. (This
   entry added that the source analogue with the request held in a variable crashes both lanes. Round 12 corrects
   it: the crash is the form of `main`, and a request held in a variable runs once `main` is a call; finding 13,
   entry 32.)

   ```
   def id(-A: Type, x: A) -> A:
     x
   def run(m: IO(Unit)) -> IO(Unit):
     R => k => id(IO.OP<R>, m(R, k))
   def main() -> IO(Unit):
     run(IO.print("x"))
   ```

   The finding offered three ways out. This executor took the one that needs no
   decision-table entry, since D22 is the coordinator's row: drop the claim and re-freeze
   the control on a shape the seed prints. `program-print-through-id` is that source's
   plan, `x\n` after 9 entries by literal review of §7 (main, IO.print, run, `R`, run's
   closure, the Action twice, the terminal continuation, id), and it does put an Action's
   application inside an argument of a call, which is what the withdrawn control showed of
   the machine. §8 now says which shape the seed refuses and that no control freezes it.
   The transition rules of §6 and §7 still apply there, so vm-model and vm-core, which
   perform the effect, are unchanged; nothing in the gate depends on either reading, and
   `evaluate.py` did not change. Refusing every Action applied off the IO spine (a
   frame-based rule) would refuse `run` above through `id`, where the seed succeeds, and so
   break §11. *(Round 11 corrects the next claim of this entry: the seed's boundary is not only a
   Case over the answer. It is the loop: an effect fires only where the pure evaluator returns
   its request to the loop, so a request that is dropped never fires, and one that any read meets
   is refused. D23, entry 31, adopts that boundary, and it settles the choice that this entry left to
   finding 11. Round 12 corrects that correction in turn: a Case that names both constructors is the only
   read that fail-stops on both lanes, and the native lane runs a Case with a catch-all; entry 33, finding 14.)*

28. **D22's silence is frozen.** Review of the round-9 branch found the clause "before the
   host call, writing nothing" frozen by no key. The Book controls that stop at an Action
   froze `{outcome, cause, calls}`, `evaluate.book` returned `{**outcome, 'calls'}` on a Halt
   and never its stdout, and the reviewer's `book-writes-then-refuses` (the effect appends
   `x\n`, then the step stops with D22's cause) survived every golden, run control and
   mutant. This executor's own D22 mutants (a Book that performs the effect, one that drops
   it) died because they change the outcome, while what D22 exists for, no host call and no
   output, was the unfrozen observable. The eight Book controls that stop at an Action now
   freeze `stdout` empty (`689934c8`, before the change) and `effects` 0 (`4b9b7aff`, likewise):
   `book-print`, `book-print-continuation-call`, `book-print-twice`, `book-print-non-scalar`,
   `book-print-ill-typed`, `book-args`, `fuel-book-effect-exact` and, since its Action meets
   fuel 0 and writes nothing either, `fuel-book-effect-short`. `evaluate.book` reports the
   bytes the run wrote on every outcome, a Halt included, and on success ahead of the describe
   line, so a Book that performed an effect would show it there as well. Two evaluator
   mutants die: `book-writes-then-refuses` by every `book-print*` control, and
   `book-writes-at-fuel-zero` (a write as the Action meets fuel 0) by `fuel-book-effect-short`
   alone. That left "no host call" frozen for a print only through its write: `IO.args` writes
   nothing, so `book-args`, whose control froze the cause, could not tell a refusal from a
   call followed by one. `Machine.effects` now counts the host calls that the reference
   evaluation makes, where the call would be (after D22's guard and D20's check, just before the
   write), and `book` and `program` report it. Two more mutants die: `book-calls-host-then-refuses`
   by the `effects` of the seven controls that enter their Action (`fuel-book-effect-short`
   meets fuel 0 first), and `book-args-calls-host`, a call made only for a foreign that writes
   nothing, by `book-args` alone, which only this key can kill. §8 says that both keys are frozen
   and that a harness must compare them: `stdout` against what its host wrote, `effects` against
   the host calls the run made (vm-core's `knot_io` trace, the effects that vm-model performs). Read from their branches, vm-core's `expected_run` carries `case.get('stdout', '')`
   for every outcome and vm-model's `agrees` requires an empty stdout of an Unsupported run,
   so neither changes for `stdout`; neither reads `effects`, an unknown key today, and both
   must (vm-core refuses every foreign but IO.print at load, round-9 item 1 below).

29. **Every kind of inspection point has a control, and the UTF-8 of a scalar has two.**
   Review of the round-9 branch instrumented the reference evaluation's `word`, `view`
   and `apply` and found 13 of its 22 inspection call sites never refusing in any golden
   or run control: a Case scrutinee in tag and in key mode, the Action's continuation,
   U32 arithmetic, the two Char prims, the Nat prims, `show`, a rendered root and a rendered
   field, and the run's last word (the twenty-second, the root's tag in `describe`'s header, viewed a
   word that the loop had already read, so it could not refuse; `describe` now reads the result's
   word first, where `inspect-render-closure` refuses it, and every remaining site refuses in some
   control). Twelve reviewer-written mutants that read less than
   §6 requires, and are exact on every well-typed word, survived all 96 goldens and 60 run
   controls. Entries 9 and 18 had implied otherwise (9 that a Case's reading of an erased
   position admits "no new unsoundness", 18 that eighteen controls froze the points of
   §6's list, which they froze only for the Succ and Chr operands, the moved and String
   prims, a Halt's code and message and the print); both now say which points were
   witnessed. The reviewer's controls were adopted, extended and frozen first (`79e6a113`):
   the calls come from walking §7, and the reference evaluation reproduced every count as
   written. Forty-three inspection controls now hand a word of another type through
   the `none`-typed `id`: `pick(id(w))` cases on `λ` at a Flag, a Nat and a Char (tag
   mode) and at a U32 and a Char (key mode), on a Box Object at a Pair and on the immediate 5
   at a Flag; the word prims through U32 `add` (first operand), `sub` (second), `shln` (its
   Nat amount), Char `is_space` and `is_eq` (second), Nat `add` and `sub` (second), and both
   `show` prims, each after 3 calls; an Invoke of an immediate or of an Object, after 2; an
   Action whose `k` is an immediate, which writes `x` first and halts after 7, because the
   target is read when its Enter comes; a Program whose `k` answers a closure or an
   immediate for its IO.OP, after 4; and a rendered closure and a Pair's closure field, after 2.
   Two more, `print-utf8-lengths` and `print-utf8-boundaries`, freeze the encoding that the
   goldens leave unwitnessed (they write ASCII beside the codes the native lane truncates): the
   expected text is Python's own, and the pinned seed writes the same 11 and 26 bytes for
   the same String constants on both lanes. Twenty inspection mutants and four UTF-8 mutants
   (85 evaluator mutants in all, with entry 28's four) are killed, each by the controls of its own point; the
   reviewer's `utf8-two-byte-wrong-lead` was a survivor too. What stays unwitnessed, and is
   named in §12: the prim ids that no control names (U32 `mul`, `div`, `mod`, `not`, `and`,
   `cmp`, the six comparisons and `shrn`, and Nat `mul` … `is_ge`), which vm-prims owes one
   control per id and operand, and the byte List and the operands of every foreign but
   `IO.print`, which vm-io owes. The reviewer's builds of vm-core (`dcc7c095`) and vm-model
   (`07e6db73`) agree with all 25 new controls, so neither has to change for them.

30. **Every rule that §2-§4 state and that the gate froze partly has a refusal.** Review of the
   round-9 branch replaced each `raise Malformed(...)` and `fail(...)` statement of
   `serializer.py` by `pass` (93 mutants): 48 survived the 112 refusals, 74 admitted controls, 60
   run controls and 141 mutants, and for 13 of them, and for `duplicate function name`, a corrupted
   golden exists that the committed codec refuses and the mutant admits. Each is a rule that
   §2-§4 state: a name has no NUL and its unused final bytes are zero, and U32 and File are
   opaque (§2); an index is in range (a function's), a Case reads a slot below the depth, a
   construct's tag and field types fit, a tag row has its own key, a key Branch binds nothing, a
   closure's arrow kind and result fit, an Invoke fits, and a Let and its body, and a function and
   its body, have types that fit (§3, §4). vm-core's production wasm refused all of them (the
   reviewer's measurement, repeated here), so this was a hole in the gate and in §4, which bound
   only vm-core to the refusals, and vm-model to none, though `check-model.py` already refuses each
   with the reference's exact reason; §4 now binds both. Sixteen controls were frozen first
   (`6025e059`): two byte-level, on `second`, one for each clause of the name rule, and fourteen
   plan-level. The reviewer's byte patches found the rules; each plan edit breaks one rule of a
   golden's plan so that its message is the validator's first, which states the rule more
   readably, and the image is what a VM reads either way. The refusals rise from 71 to 87 (22
   byte-level, 9 at the limits, 56 plan-level). Sixteen codec mutants remove one check each (the two
   clauses of the name rule, U32 and File not opaque, and twelve validator statements): each
   survives every golden and dies by the control that breaks its rule, three by another
   refusal that the next check gives, the rest by an admission. `duplicate function name`,
   enforced by the reference codec and by vm-core (`duplicate-function`) and spelled by
   vm-model, was stated by neither SPEC nor a control; it joins §4 step 4 (`FN` is found by name),
   so both VMs are bound. The reviewer also offered the generator that produced the 93 mutants
   as a gate step. It is not added: it would demand a killing control for each of the other 34
   statements, which finding 12 records, and §11 does not count the crash that removing 12 of
   them causes as a kill. Measured on the reviewer's builds of vm-core (`dcc7c095`) and vm-model
   (`07e6db73`): both refuse every one of the 81 non-oversize refusal controls, the 16 new among
   them, so neither VM changes for them.

31. **IO requests are values, and only Top's loop performs one (D23).** Review round 10 confirmed that
   the eager rule of entries 21 and 27 (an Action performs its effect where it meets its continuation)
   diverges from the seed wherever a request is built but not returned to the event loop. With
   `keep(-R, x, y) = y` and `run2 = R => k => keep(R, m1(R, x => Halt{7,"unreached"}), m2(R, k))`, both seed
   lanes print `kept` (exit 0) and the eager rule printed `dropped` then `kept`. The seed's `io_step`
   (`comp.ts`) performs the request that the pure evaluator returns to the loop, and no other, and
   `tests/io/request_out_of_band.bend` says so. It is not laziness: the seed builds unused arguments
   (measured here on the native lane, `second(fib(42n), 7)` takes 0.79 s of user time and
   `second(7, fib(42n))` 0.80 s), so a dropped request is built and never reaches the loop. The coordinator
   recorded D23; D22 is its consequence, not a second rule, because a Book invocation has no loop.

   The model (SPEC §5-§8, §10). Applying an Action to `k` builds an inert request, a class-5 cell
   `foreign, operand…, k`, after the debit that it always had. Only Top's phase 3 performs one, the request
   that a run returns to it, and then enters its `k`. A request that a let, an argument, a field, a capture
   or an Emit holds is dropped with no effect. A request that a Case inspects, that a Book renders or
   that any read of §6 meets is `Unsupported vm effect` (D4), before an ill-typed test and, at an Enter's
   target, before the debit, whatever rows the Case has (entry 33). A let-bound request is inside the model
   (goldens `let-dropped-request` and `let-live-request`); the seed's crash that this entry first blamed on
   a let is the form of `main` (finding 13, entry 32).

   The three choices that the round-10 review left open, each pinned by a control:
   - Operand inspection (§6) and D20's scalar check happen when the loop performs the request. A dropped
     request that holds an ill-typed String is no failure (`program-request-dropped-ill-typed`), and one that
     holds a non-scalar String is no `io abi` and writes nothing: the seed's native lane prints `kept`
     for it (golden `keep-non-scalar`; the Bun lane refuses the Char where it is built and writes nothing).
   - The fuel debit happens where the Action's second application builds the request, so a dropped request
     has paid its entry (`book-request-dropped`, `program-request-dropped-let`, `fuel-book-request-short`,
     `fuel-book-effect-short`), and the loop's performing is no entry. Every run that performs each request it
     builds therefore keeps its `calls`: the four D20 goldens (4, 4, 4, 13), `program-print-through-id` (9) and the
     fuel controls of `foreign-print`.
   - `k` is entered by the loop after the effect and read only then (`inspect-continuation-target`).
   D22's order question of round 9, whether the refusal precedes D20 and the inspection, is settled by
   construction. A Book performs no request, so nothing is inspected, converted or checked, and
   `book-print-non-scalar` and `book-print-ill-typed` stop at `got`'s Case as `Unsupported`.

   Frozen before the evaluator moved (D7): the goldens `keep-swapped`, `keep-first`, `run2-flag`, `spine`,
   `keep-non-scalar` and `book-drop`, which both seed lanes run to the same bytes (five failed the committed
   evaluator; `spine`, IO.bind's shape, agrees before and after and is the loop's control), and fourteen run
   controls by literal review. A fifteenth, `fuel-zero-request-target` (the Enter of a request at fuel 5), was
   added after the review of §7 step 1's claim that a request target is refused at fuel 0 too, which no control
   pinned; its value was walked before it was run. Seven controls of entries 21 and 28 changed value and were re-frozen, each in its own
   commit with its reason: `book-print`, `book-print-continuation-call`, `book-print-twice`,
   `book-print-non-scalar` and `book-args` from 4 to 5 entries, `book-print-ill-typed` from 5 to 6 (the request now
   reaches `got` before its Case refuses it), and `fuel-book-effect-exact` from fuel 4 to fuel 5, since at 4 the
   run is `Exhausted` after 4 (`fuel-book-request-short`). Outcome, `stdout` and `effects` of each are as
   before. Every other frozen value held: 96 goldens and 78 run controls needed no change. `book-drop`, which
   the seed runs on both lanes (`On{}`), is a Book that round 9's rule refused, so that rule broke §11.

   Evaluator mutants are 92. New for D23, each killed by the controls that name it (SPEC §12): the eager rule;
   a dropped request performed by its function or by its let; the loop entering `k` before the effect;
   a Case that picks an arm of a request, and a request taken for an ill-typed word at a Case, a scalar
   or an Enter's target; an Enter that tests fuel before it reads a request; a rendered field that admits one; operands read, or D20 checked, when the request
   is built; a loop that refuses, performs only the first, or performs the request an Emit holds; a Book
   that runs the loop, refuses where it builds the request (round 9's rule) or enters `k` without the effect;
   a continuation read when the request is built. Twelve mutants of entries 21 and 28 are retired because the
   rule they guarded no longer exists: `book-performs-effect` and `book-drops-effect` (now `eager-effect`,
   `book-runs-loop` and `book-enters-k-without-effect`), `program-refuses-effect` (`loop-refuses-request`),
   `book-refuses-before-debit` and `book-refuses-at-fuel-zero` (no Book step is refused at the Action's
   application, and `book-refuses-request-build` is that old rule, now wrong), `book-names-the-foreign`,
   `book-refuses-after-inspection` and `book-refuses-after-scalar-check` (nothing in a Book is inspected,
   converted or checked), and `book-writes-then-refuses`, `book-writes-at-fuel-zero`,
   `book-calls-host-then-refuses` and `book-args-calls-host` (their observables, `stdout` empty and
   `effects` 0, stay frozen on every Book control, and `book-runs-loop` dies by them).
   `effect-before-debit` became `debit-at-perform`, and `effect-refusal-refunds-debit`,
   `continuation-read-before-effect` and `continuation-unread-as-terminal` moved to the loop's line;
   `book-refuses-action-build` and `book-refuses-erased-application` are kept, and
   `enter-immediate-target-as-action` now supplies an Action tuple, so that it changes an outcome
   instead of crashing on a request that it cannot index (a crash is no kill).
   Measured on the reviewer's builds, vm-core `dcc7c095` and vm-model `07e6db73`, which perform the
   effect where the Action meets `k`: five of the six new goldens and 22 of the 100 run controls (the seven
   re-frozen and the fifteen new) disagree, besides the halt rows of round 9.
   `docs/compiler-campaign/VM-DESIGN.md` (section 2, IO) still says that invoking an Action with its
   continuation performs the call; D23 supersedes that sentence, and the file is the coordinator's to amend.

32. **The seed's crash is `main`'s form, and a request held anywhere else runs (round 12, review finding 1).**
   Entry 31 and finding 13 said that the seed crashes on a request bound by a `let`, used or dropped, and that
   "no golden can freeze the shape". The review of round 11 showed that the crash is caused by `main` being a
   bare `R => k => ...` lambda, whatever its body, and that a request held by a let, a field, an Emit or a
   capture runs on both seed lanes and agrees with D23 once `main` is a call. Reproduced here on the pinned
   seed: `main = R => k => IO.print("direct")(R, k)`, `R => k => k(Unit{})` and `R => k => Halt{1, "boom"}`
   crash (exit 1, no output: native `bend: memory fault (machine stack overflow?)`, Bun a TypeError), finding
   13's reproducer verbatim crashes, and the same source with the let deleted crashes identically (witnesses
   `main-lambda-print`, `-continue`, `-halt`, `-let` and `-nolet`). The reproducer with the lambda moved into a
   helper, `run(m, n) = R => k => once(R, m, n, k)` and `main = run(IO.print("dead"), IO.print("live"))`, prints
   `live` on both lanes: the dead let-bound request is built and never performed (golden
   `let-dropped-request`), and so is the variant that returns a let-bound live request (`let-live-request`).
   Four more goldens do the same for a request in a field, returned or dropped (`field-request-returned`,
   `field-request-dropped`), in an Emit's field (`emit-field-request-dropped`) and in a capture
   (`capture-request-dropped`). The earlier claim was wrong because no gate held it. Every seed fact that SPEC §8
   now cites is a witness that the gate re-runs on both lanes (§12, `golden/witnesses.json`).

   What stays: the run controls that build `main` as `λ@R. λk. body` (`program-request-dropped-let`,
   `program-request-in-emit`, `program-request-dropped-ill-typed` and the others) keep their values. They are
   literal review of §7 and §8 and make no claim about the seed, since a crash of `main`'s form is no value that
   a VM owes; the call-shaped goldens are their seed-witnessed twins. No frozen expectation moved, and the six
   goldens pass on the committed evaluator, which already follows D23: the eager rule and the dropped-request
   mutants die by them (SPEC §12). Their plans are hand-lowered (§1): the one Base declaration they reach is
   `IO.print`, ahead of the source's functions, and `Box` is the one added type, which needed `check_declarations`
   to accept a generic `type Box<-R: Type> is Type:` beside `type Flag is Data:`.

33. **A Case over a request is refused whatever rows it has, and the seed's lanes disagree (round 12, review
   finding 2).** *Superseded in round 13: the coordinator chose option b, D24 (entry 35). A Case with a
   Default takes it; the three `program-case-request-*` controls below are runs now, and the witnesses that show the
   native lane taking the catch-all are goldens. What stays true is the measurement, and the refusal of a Case without a
   Default.* Entry 27's round-11 correction and finding 11 said that the seed fail-stops in every lane on a
   Case over an applied effect's answer, and SPEC §8 said that no golden agrees with the seed there "because the
   seed does not succeed". The review of round 11 measured otherwise (witnesses `case-request-*`; native / Bun):

   | A Case over a request that | native | Bun |
   |---|---|---|
   | names both Emit and Halt (`case-request-both-arms`) | fail-stop, exit 1 | fail-stop, exit 1 |
   | names one constructor beside a catch-all (`-emit-default`, `-emit-default-u32`, `-halt-default-u32`) | exit 0, takes the catch-all (`2` where the arms give 1 and 2, `4` where they give 3 and 4) | fail-stop, exit 1 |
   | is only a catch-all or a binder (`-default-only`, `-binder`) | exit 0, the request is never read | exit 0 |

   D23 as decided refuses every read of a request. That stands, as a recorded capability gap for the last two
   rows, for these reasons. First, the pinned literals head answers `Unsupported check variable-pattern` for a
   catch-all on an algebraic type (`_` alone, a binder, and `_` after a constructor arm, each tried on a Flag:
   witnesses `catch-all-lone`, `-binder` and `-after-arm`, which the seed runs), so no Knot source lowers to
   such a plan and no compiled program can reach the divergence: only a hand-written plan can, and D4 has
   Knot say Unsupported for a form it cannot handle. A `_` after key arms on a U32 or a Char is accepted
   (`default-hit`, `case-char`) and is not about requests. Second, the lanes disagree with each other on the
   shape that matters. The Bun lane is the cross-check and the native lane the reference (entry 7), so that
   alone decides nothing. Third, the refusal is the one rule that both VMs must already implement at every other
   read (§6). Frozen by literal review before the controls ran: `program-case-request-emit-default`,
   `-halt-default` and `-default-only` (each 7 entries: main, IO.print, R, the Action applied to `k`, `k`'s
   closure and the Case's function; then `Unsupported vm effect`, nothing written, `effects` 0). The evaluator
   mutant `case-default-takes-request` (a Case with a Default over a request takes it) survived every earlier golden
   and run control, measured on the round-11 tip, and dies by exactly these three. The alternative, finding 2's option
   b, is finding 14.

34. **A type record's constructor count is refused before it sizes a list (round 12, review finding 3).**
   `serializer.decode` allocated `[None] * r[3]` from a data type record's raw count and checked the counts
   against the constructor table only after the loop: a golden with that word set to 0xFFFFFFFF asked for a
   32 GiB list before it was refused (the review's watchdog aborted at 32,788 MB), which §4 forbids and which on
   a smaller host is a MemoryError that is neither Malformed nor Exhausted. The codec now refuses
   `r[3] > len(ctors) - expect` as `constructor count` after the first-constructor check and before it allocates
   (§4 states the per-record order: first constructor, count, name). Three byte-level controls pin it on
   `second`: `type-grouping` (`constructor grouping`), `type-count-max` (0xFFFFFFFF, `constructor count`) and
   `type-count-short` (the counts sum to 2 of 3, `constructor count`), and three codec mutants die by verdict:
   `constructor-count-exclusive`, `constructor-grouping-unchecked` and `constructor-count-sum-unchecked`. No mutant
   restores the late check as it was: sized from the raw count it would allocate 32 GiB at `type-count-max`, which is a
   host's memory and no verdict, and a crash is no kill (§11). *(Corrected in round 13, entry 37: the clause-level audit of
   entry 36 did omit the check, and the gate held 35 GB for it; that omission now sizes the list by the constructor table.)*
   The ordering of the check against the allocation is held by that control against the committed codec, by the gate's
   assertion that its own peak memory stays under 4 GiB, and by the two VMs' gates. The audit of the rest of `decode` found
   no other count that sizes anything before the structure holds it: section counts are checked against the words left,
   records against their lengths, closure and Case lengths before their arrays, and arities and `slots` against §4's limits.
   Measured: 0xFFFFFFFF in every data type record of four goldens refuses in under a millisecond at a 22 MB process peak.

35. **D24: a request matches no row, so a Case takes its Default (round 13).** The coordinator
   chose option b of finding 14 (main `51ca324b`): the seed's native lane takes the catch-all on every shape measured in
   entry 33, and the pattern matrix of the nest increment now accepts catch-alls on algebraic types, so compiled programs
   will reach these shapes; §11 owes the native lane's value wherever it succeeds. *(Corrected in entry 37: nest's checker
   accepts a catch-all but lowers it into a row for each remaining constructor and emits no Default, so a compiled program
   reaches the complete tables of the `-compiled` controls, which the VM refuses; the Default rule is reached by a
   hand-written plan and by a keys Case.)* SPEC §6, §6.1 and §8 now say: a class-5
   scrutinee is not inspected; it matches no row of a tags table or of a keys table, so the Case's Default takes it, unread,
   and a Case without a Default stops `Unsupported vm effect`; a binder or a lone catch-all holds no Case and binds the
   request as a value. That is D24's text as written ("a Case over a request takes its Default when it has one", with D23's
   refusal remaining "for a Case without a Default"), and a keys Case always has a Default, so no keys Case refuses a request.
   Two points of it are pinned by a frozen control each:

   - **Either mode.** The rule does not ask what the Case compares. `case-request-default-keys` (a Book: a request handed
     through `id` to a keys Case whose Default answers `Off{}`; `Evaluated 8 0 Off{}` after 6 entries) is the twin of
     `case-request-default-at-flag`. The first commits of round 13 read the rule as a tags-mode rule and kept a keys Case
     refusing (`inspect-request-keys`); that contradicted the text and the any-type point below, and was corrected in the
     same round (two commits: the control re-frozen, then the evaluator). The evaluator mutant `keys-case-refuses-request`
     (the old key-mode refusal) dies by that control alone. No compiled program reaches a keys Case with a request, since a
     request arrives there only through a `none` position that a hand-written plan hands a request, so the choice is the
     text's alone.
   - **Any scrutinee type.** The Case never reads the word beyond its class, so the Default is taken at IO.OP and at a
     type that a plan names by mistake alike (`case-request-default-at-flag`, a Book whose Case names Flag: `Evaluated 8 0
     Off{}` after 6 entries). `case-request-default-at-io-op-only` dies by it and by the keys control.
   - **Without a Default, refused as before**: `Unsupported vm effect`, never ill-typed (`case-request-without-default-ill-typed`),
     and no row is picked (`case-request-picks-arm`); the seven Book controls that hand `got` a request and
     `program-case-request` freeze it.

   Frozen first (D7, two red commits) and then implemented. Three goldens promote witnesses of entry 33: the native lane's
   values by seed, the Bun lane recorded beside each (it fail-stops on all three): `case-request-emit-default-u32`
   (`case Emit{v}: 1 / case _: 2`, printed: `2`), `case-request-halt-default-u32` (`4`) and `case-request-emit-default`
   (`case Emit{v}: d / case _: d`: exit 0, no output). Their plans are hand-lowered (§1) and their entry counts were
   walked by hand before an evaluator ran: 13, 13 and 9 entries, effects 1, 1 and 0 (the request that the Case receives
   is dropped; the print that the two U32 goldens perform is `2\n` or `4\n`). The three `program-case-request-emit-default`,
   `-halt-default` and `-default-only` controls stop being refusals: each ends exit 0 after the same 7 entries with nothing
   written and `effects` 0, since the Default's Flag goes into an Emit's unread field (the goldens hold the Default's
   value). The witnesses `case-request-emit-default`, `-emit-default-u32` and `-halt-default-u32` are retired, as the goldens carry them
   (14 witnesses become 11; `witness_refusals` uses `case-request-both-arms`); `case-request-default-only` and `-binder`
   stay, since a lone catch-all holds no Case. One control is new, `case-request-default-at-flag`. The evaluator
   mutant `case-default-takes-request` is the rule now and is removed; five are new, and each dies by named controls
   (SPEC §12): `case-request-refused-with-default` (D23's refusal: the three goldens, the three Default controls and the
   two Book controls), `case-request-ignores-default` (picks the first present row: the `2` and `4` goldens print 1 and 3),
   `case-request-without-default-ill-typed`, `case-request-default-at-io-op-only` and `keys-case-refuses-request`;
   `case-request-picks-arm` is re-anchored on the Case without a Default. Round 11's control `inspect-request-keys`
   is `case-request-default-keys` and a run. Nothing else moved: vm-expected.json gained exactly three rows.

36. **Round 13, review findings 1 to 3: the conditions of §4 are listed form by form, and each is pinned.** The review of
   round 12 ran 47 mutants of the reference codec against the frozen controls and 19 survived: a loader could omit a condition
   and pass every control that the two VMs are held to. Finding 1: four conditions of step 4 had no control (a repeated keys
   row, a Construct of a nullary constructor, an Invoke that takes the wrong number of operands, a Case whose slot and scrutinee
   are two concrete types). Finding 2: finding 12 was wrong (above). Finding 3: canonicality had one control, several controls
   pinned one instance of their rule (the last padding byte, the first digest word), and UTF-8 was undefined. Nothing in
   `serializer.py` changes, since it already refused each image; the controls were frozen against it, and each mutant survives the
   old battery and dies by its control.
   - **The text.** §2 defines a name (well-formed UTF-8 by the Unicode Standard's Table 3-7, spelled out; no NUL; every unused byte zero)
     and says that `Closure.site` starts at 0. §4 step 4 is listed form by form with the label of each condition's control, and step
     5 is ten clauses (main word; names in order and used; constants in order, used and once; constructors in order; nodes in
     post-order; sites from 0; arms' result types), each about words that a decoded plan does not keep, so no earlier step can
     refuse a breach. The clauses are the decomposition that a loader without an encoder needs.
   - **The controls.** 121 refusals (99 byte-level, on a valid golden's records laid out again by `Layout`; 22 plan-level): 211 in
     all. One clause each. A name in every malformed form of UTF-8 (overlong in 2, 3 and 4 bytes, a surrogate, beyond U+10FFFF, a lead of
     `F5`, cut inside and before ASCII, a stray continuation), each unused byte, the empty name, a repeated name, digest words 25 to
     31; every record kind with a length or a count that contradicts its words; the ten canonicality clauses (four for the sites);
     the four conditions of finding 1 (the Invoke in three: a live arrow with none, with two, an erased one with one); and the
     statements of finding 2. Two admitted plan controls hold the other side of UTF-8: a name of each length and one with every
     edge of a length.
   - **The mutants.** 48 codec mutants (89 to 137), each omitting one clause and dying by the control that breaks it alone; ten rule
     mutants, one per canonicality clause (13 to 23), which delete a clause of `piecewise_rejected`; the gate's total is 261 (203
     before). The clauses are held against re-encoding on 5,797 images (`canonical_differential`), and the statement audit is
     finding 12's rewrite.
   - **One change of the gate's own rule.** `rejected` reads a `ValueError` of the re-encoding as `noncanonical`: a plan that the
     encoder refuses (a name that holds a surrogate, which a decoder that admits surrogates yields) is the decoding of no image.
     The reference never raises there. It makes the reviewer's `utf8-surrogates-accepted` die by a changed refusal instead of a raise.
   - **What stays open.** Nothing that the reviewer named. Three of its mutants raise by construction (finding 12, above); each is
     held and has a codec mutant that models the omission without the raise. The count of refusals, controls and mutants moves
     again whenever a rule does; SPEC §4 and §12 state today's, and `vm-core`'s harness reads the two sentence shapes that carry the
     refusal and run-control counts.

37. **Round 13, review round 1: three confirmed findings (the audit's memory; D24 and compiled programs; a fourth row of §8).**
   The coordinator's review of the tip `3b43fca4` confirmed three findings, all measured and reproduced by a verifier. This
   entry records each; the fixes are separate commits, no frozen expectation of an existing golden or control moved, and the
   witnesses and controls that they add were frozen first (D7), with the entries counted by hand before any of them ran.
   - **Finding 1: the gate held 35 GB.** The clause-level audit of entry 36 omits every refusal of the reference codec, and its
     omission of `decode`'s `constructor count` guard is exactly the late size check that entry 34 said no mutant restores: without
     it `type-count-max` (0xFFFFFFFF) sized `[None] * r[3]`, a list of 32 GiB. The gate passed on a host with the memory
     (`/usr/bin/time -l`: 103.86 s, a maximum resident set of 34,793,570,304 bytes, in the gate's own process) because the
     allocation succeeds and the refusal then changes to `constructor grouping`, which counts as a kill; on a host without it
     the allocation raises MemoryError, which is a crash and no kill, and the audit would fail with a misleading message. SPEC
     §12, `check-spec.py` and entry 34 all said the opposite. Fixed as the review proposed: that one omission now also sizes its
     list by the constructor table (`BOUNDED`, `min(r[3], len(ctors))`), `expect += r[3]` stays, and the omission is killed by
     `control type-count-max: HostFailure image: constructor grouping` with the same 178 omissions and 136 kills as before. The gate
     asserts that its own peak memory stays under 4 GiB (`PEAK_RSS`), so that a later omission that sizes an allocation from a raw
     word fails on any host instead of passing where the memory exists. Measured after: `/usr/bin/time -l` 38.90 s and 1,094,483,968
     bytes for the largest process of the run (a seed build), 430,030,848 bytes (410 MiB) in the gate's own process.
     What the audit still cannot hold is the order of the check against the allocation in a codec that allocates first: that mutant
     would ask for 32 GiB, so the committed codec's order is held by running `type-count-max` against it, and by the assertion.
   - **Finding 2: D24's Default is unreachable from compiled programs.** D24's rationale (`docs/COMPILER-CAMPAIGN.md`: nest's pattern
     matrix accepts catch-alls, so compiled programs will reach these shapes) does not hold for the lowering. `campaign/nest` at
     2a84a4f5 accepts a catch-all on an algebraic type and lowers it into a row for each constructor that no source arm names, the
     catch-all's body copied into each, with no Default (`src/check.bend`, `default_arms` and `fallback`: a terminal default "is
     checked once while live, then shared by its remaining runtime tags"); the image encoder (`campaign/image` 54f47b2a,
     `src/image.bend`) has no Default term and builds every tags Case as a complete table. Reproduced here on my own build of that
     commit (`BEND_NO_TELEMETRY=1 bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/check-cli.bend -o .local/nest-check`, then
     `.local/nest-check` on a source over `type Op is Data: Emit{v: Flag} / Halt{c: Flag, m: Flag}`, since that checker refuses an
     `IO.OP<R>` parameter as `Unsupported parse parameter-type`): `Emit: On / _: Off`, `Emit: On / Halt: Off / _: On` and
     `Emit: On / Halt: Off` all print the core `case $0 [0(1 $1:0;)=>v0.1;1(1 $1:0;1 $2:0;)=>v0.0]`; `Emit: On / Halt{On{}, m}: Off / _: On`
     and the same with the `_` only inside `match c` both print `case $0 [0(1 $1:0;)=>v0.1;1(1 $1:0;1 $2:0;)=>case $1
     [1=>v0.0;0=>v0.1]]`; a lone `_` and a binder print the bare body `v0.1`, so §8's third row does hold for compiled programs.
     The merged head (`campaign/literals-integ` at 9f98fb09, built the same way, `.local/integ-check --bundle .`, over `import Base`
     and `type Cmd is Data: Send{v: Flag2} / Stop{c: U32, m: Flag2}`, since Base already declares Emit and Halt) agrees on the flat
     shapes: `Send: 1 / _: 2` and `Send: 1 / Stop{c, m}: 2 / _: 3` both print `f(1:2)->0=case $0 [0(1 $1:1;)=>v0.1;1(1 $1:0;1 $2:1;)=>v0.2]`,
     a lone `_` and a binder print `v0.3`, and `Send: 1 / Stop{c, m}: (match c: case 0: 2 / case _: 3)`, with or without a dead outer
     `_`, prints `... 1(1 $1:0;1 $2:1;)=>case $1 [0=>v0.2;_=>v0.3]]`. It refuses the exact source of `case-request-nested-default`,
     a `_` after the literal field pattern `Stop{0, m}`, as `Unsupported check variable-pattern 186:187:15:9`, at check time and before
     any image exists, so that witness is a seed fact whose exact source no compiled program reaches today. Its plan is reached by nest's
     constructor sub-pattern, and by `case-request-inner-default-only`'s source, which the merged head lowers to the same plan (the native
     lane fail-stops there and the VM agrees); adding a dead outer `_` to that source lowers to the same plan again.
     So a compiled Case over a request is a complete table with no Default: the VM answers `Unsupported vm effect` where the native
     lane takes the catch-all, and the three D24 goldens witness plans that no lowering emits.
     - *Fixed inside `vm/`, by the review's second option* (the first is nest's and image's to change, so it is the coordinator's
       call). SPEC §6, §6.1, §8 and §11 and entry 35 now say that D24's rule is the VM's for a plan that holds a Default (a
       hand-written plan, a keys Case), that a compiled program meets the refusal for a catch-all, and that this is a recorded
       `Unsupported` gap, never a bound. Four run controls freeze the compiled twins (`case-request-emit-default-u32-compiled`,
       `-halt-default-u32-compiled`, `case-request-emit-default-compiled` and `case-request-nested-default-compiled`: `Unsupported vm
       effect` after 8 entries, nothing written, `effects` 0, the entries walked by hand before they ran), and the three goldens
       are described as hand-lowered witnesses of the plan-level rule. No frozen expectation of a golden moved. The four twins die by
       `case-request-picks-arm` and `case-request-without-default-ill-typed` (so does the Book's, of finding 3), and the two retested plans of finding 3 by
       `case-request-refused-with-default` and `case-request-ignores-default` (each measured alone against the control); no new
       mutant was needed.
     - *For the coordinator: not vm-spec's to edit.* `docs/COMPILER-CAMPAIGN.md`'s D24 row says that compiled programs will reach
       the shapes, which is false of nest at 2a84a4f5. A rationale that is true of it: "A request matches no constructor row, so a
       Case takes its Default when its plan has one and otherwise stops `Unsupported vm effect`. The seed's native lane takes a
       source's catch-all, and the checker's lowering of an algebraic catch-all is a complete table with no Default, so compiled
       programs meet the refusal, a recorded `Unsupported` gap; hand-written plans and keys Cases reach the rule." The alternative
       that keeps D24's rationale is a change of nest's checker (keep a terminal catch-all as a Default term) and of the encoder
       (§3 maps it to a tags Default), which closes the second row of §8's table; the fourth row needs finding 3's shape too.
   - **Finding 3: a fourth row of §8's table.** The native lane takes a catch-all that sits beside a table naming every constructor
     (`Emit: 1 / Halt: 2 / _: 3` prints `3`) or that is reached only through a field pattern (`Emit: 1 / Halt{0, m}: 2 / _: 3` prints
     `3`), while the plan of such a source is a complete table with no Default, since §3 keeps a Default only where a row is absent.
     §8 had no row for it, and its sentences "wherever a Case can meet a request" (§8) and "D24 closed it" (§11) promised more than
     a plan can carry. The review's headline, that the image cannot express the native answer, is refuted by its own verifier and by
     two controls here: `case-request-both-plus-default-retested` and `case-request-nested-default-retested`, whose Default tests the
     slot again for the arms named after the catch-all, validate, round-trip and print `3` after 13 entries with one effect, as the
     native lane does. What stands is that no lowering emits them. Fixed: a fourth row of the table (§8); four seed witnesses,
     `case-request-both-plus-default` (`3`), `-nested-default` (`3`), `-inner-default-only` (a fail-stop on both lanes) and the Book
     `-book-both-plus-default` (`On{}`; the Bun lane prints its stuck term), each with its literal review written before
     `--freeze-new` observed the seed; the two sentences corrected. `-inner-default-only` is the review's p1e with the same constants
     as the nested witness: its plan equals the nested one's, so two sources, one plan and two native answers show that no rule of the
     VM agrees with the seed on it. The Book's plan has its own control, `case-request-book-both-plus-default-compiled` (`got` names Emit and Halt and its dead
     catch-all is dropped, `go` hands it the request: `Unsupported vm effect` after 6 entries, walked by hand before it ran), which
     is not `book-print`'s: that `got` returns Emit's field and there is no `go`. The gap closes by a
     lowering that emits the retested shape, or by a §3 that admits a Default beside a complete table (with `redundant-default` and
     the canonical-order clause changed); both are the coordinator's call.

38. **Round 14: atomic stops (the coordinator's ruling after vm-lockstep findings 1 and 2).** The lockstep (`campaign/vm-lockstep`)
   compared vm-core with the model on every transition of 296 runs and found two places where a halting step is not atomic in the VM. Its
   finding 1: the VM pops a Gather frame before it inspects the operands or tests Succ's `NatRange` (CORE.md choice 8 records this for an
   ill-typed operand as a stated limit that no control observes; the `NatRange` stop has the same mechanism; 23 of the 296 runs hit it).
   Its finding 2: §6's table dropped `act` at Return to Top and §8's phase 3 then refused an ill-typed IO.OP, while the sentence above
   the table said that a refusal changes no state (the runs `inspect-halt-code` and `inspect-halt-message`). The model follows the
   sentence and the VM follows the table. The lockstep accepts both as named halting relations (`GATHER_POPPED`, `TOP_RELEASED`, 23 and 2
   in `frozen.json`) until one normative reading exists. The coordinator's ruling is that reading: **no refusal, halt or exhaustion changes
   machine state; every check that a step can fail (operand inspection, NatRange, IO.OP inspection at Return to Top, limits) happens before
   the step mutates frames, `act`, `top`, the heap or the meters; the only exception is the fuel debit that §7 prescribes and the
   Enter-debit rule that keeps it.** The VM must not pop a Gather frame before it inspects its operands or tests NatRange, and Return to Top
   refuses an ill-typed IO.OP before it drops `act`.
   - **The text (SPEC §6.3, and the rows it reads).** One rule: a step that stops has no post-state, and the machine keeps the state in
     which the step began. The written order of a row's substeps is the order of its effects and never of its refusals ("check, then
     change"), and where two checks of one step would both stop the machine, a request names the stop before a word's type, and a
     word's type before a limit, the limits in the order of the row's substeps. Applying it to every row found more text that said
     otherwise, and each place is corrected: the Gather row (the frame is popped by the completion, not before it: finding 1); the Top
     row (refuse, then drop `act`, then the rest of §8: finding 2, and for a Book's description at phase 0 as well as for phase 3); §6.1's
     "a heap `Exhausted` (kind 2) leaves the Scope pushed", which is reversed (the checks keep their order, the frame region's before the
     fields', and both precede the effects); §6.2 and §7, where a tail entry pops Scopes and drops `act` before it allocates (the fit
     is judged as if the release had happened, so that a tail loop still reuses its cell, and a stop of steps 2 and 3 keeps the pending Enter
     and the debit and nothing else); InvokeFunction, which pops 3 words and pushes 4 (the fit is judged on the region as the pop leaves it);
     §8's phase 3 and §10 (inspection, D20's scalar check and the room for the conversion and the Result come before `act` is dropped
     and before the host call; `IO.print`'s Result is the Unit immediate, and a foreign whose Result allocates reserves its cells first: vm-io's);
     §9's prims (the room for every cell of a result is decided before the first is allocated); and §5 (a release that would overflow
     its worklist decrements no count and frees no cell; the room for every cell of a step is decided first). §11 says that every stop is atomic.
   - **What the reference evaluation can pin, and what it cannot.** evaluate.py has no frames, `act` or cells: its state is `fuel`, `calls`,
     `stdout` and `effects`, and it was already atomic, so it does not change (its docstring says so). A stop shows there as the outcome and
     those four, and the rule is that a stopped run reports what it held before the refusing step (an effect that an earlier step performed
     stays, one that the refused step would have performed is none), and that the same run given exactly the fuel that it has spent reaches
     the same stop, since a refused step pays nothing. That last property is the one that no earlier control could see: a refusal that tests
     fuel first is invisible at fuel 1,000,000. Frames, `act`, `top` and the heap at a stop are held by comparing machines, not here: vm-model's
     steps are atomic by construction (MODEL.md: "A refused transition leaves the machine as it was"), and the lockstep compares vm-core
     with it at every halt once its two relations are removed. What the reference evaluation cannot reach at all is the heap, the frame region,
     `RCOverflow` and a release's worklist; vm-core's frame-region and heap-limit rows (`nat-pred-frames`, `nat-pred-heap`,
     `describe-frames-short`, `append-heap-short`) freeze `calls`, `top` and the bump pointer at such a stop and are where they are held.
   - **The controls (27, D7).** `atomic_controls`, run controls 111 to 138. The expected values were written by literal review before any run
     (entries walked by hand, `stdout` and `effects` from each source), and the reference evaluation reproduced all of them on its first run, with the
     unchanged evaluate.py (the last five were added in review, the same way). Twenty are twins of existing controls or goldens at fuel = `calls`, freezing the `stdout` and `effects` that the first
     freeze left out, one or more for each stop kind of the ruling: an ill-typed Chr, Succ, word prim, Case scrutinee and rendered field;
     `NatRange` at a Succ, `Nat.add` and `Nat.mul` (the plans of the goldens `nat-succ-range`, `nat-range` and `nat-mul-range`, which freeze no
     `calls`: 2 each, the callee's entry being the last); Return to Top refusing a Halt's code (`inspect-halt-code`) or message
     (`inspect-halt-message`), an IO.OP that is a closure, and a Halt message with a surrogate; the loop refusing a String with a surrogate, one with a
     scalar `a` before it (`print-non-scalar-mid`: nothing of the prefix is written) and one with an ill-typed tail; a Case refusing a request and a Book's
     render of one (`book-request-rendered`, after 5); a display beyond its bound; fuel 0 at a Book's last entry (`fuel-book-short`) and at a Program's
     Action's second application (`fuel-action-short`: no request is built). Five stop after an effect and freeze what it wrote and called
     (`a\n` or `x\n` or `vm\n`, 1 effect: the last is `fuel-continuation-short`, whose `k` meets fuel 0 after the loop performed the request), and two
     order inspection before charge at the display bound (`Pair{1,048,574n, w}` has charged the whole visit bound
     when it reaches `w`: a Flag there is the 1,048,577th visit, `display`; a closure handed there as a Flag is `ill-typed` first). The last pair is
     the ordering of vm-core's round-7 finding 2 (describe counted a visit before it inspected the word, so an ill-typed word at the last visit
     was `Exhausted` display), at the reference's own outcome, with a Nat word for the visits instead of a chain of a million constructors.
   - **The mutants (23).** Each mutates before it refuses (SPEC §12), and dies by a changed observation. The gate requires more than a kill:
     at least one control of the atomic set (the 27 `atomic-*` controls and the three `fuel-zero-*` controls of a refused Enter, the same twin)
     must change under each, since a mutant that only a golden or another run control kills is not held by the controls of the rule that it
     violates (`ATOMIC_MUTANTS`, `SPENT_FUEL_TWINS`, and `atomic` in each mutant's receipt row; with the controls of three of them removed, the gate
     reports those three as survivors). Measured on the tree, each against the 111 goldens, the 120 run controls outside the atomic set (twelve of them the order controls of entry 39) and the 30
     inside it (a count is the controls that kill it):

     | Mutant | goldens | run controls outside the atomic set | atomic set |
     |---|---:|---:|---:|
     | `nat-range-spends-entry` | 0 | 0 | 4 |
     | `ill-typed-spends-entry` | 0 | 46 | 11 |
     | `case-request-spends-entry` | 0 | 13 | 1 |
     | `request-read-spends-entry` | 0 | 12 | 2 |
     | `d20-refusal-spends-entry` | 4 | 1 | 4 |
     | `display-refusal-spends-entry` | 0 | 2 | 2 |
     | `fuel-stop-spends-entry` | 0 | 8 | 3 |
     | `enter-operand-check-after-debit` | 0 | 8 | 3 |
     | `enter-request-target-after-debit` | 0 | 1 | 1 |
     | `nat-range-tests-fuel` | 0 | 0 | 4 |
     | `ill-typed-tests-fuel` | 0 | 0 | 11 |
     | `case-request-tests-fuel` | 0 | 1 | 1 |
     | `request-read-tests-fuel` | 0 | 0 | 2 |
     | `d20-refusal-tests-fuel` | 0 | 0 | 4 |
     | `display-refusal-tests-fuel` | 0 | 0 | 2 |
     | `effect-counted-before-scalar-check` | 0 | 0 | 3 |
     | `effect-counted-before-inspection` | 0 | 1 | 4 |
     | `effect-writes-before-scalar-check` | 1 | 0 | 1 |
     | `describe-writes-header-before-stop` | 0 | 1 | 4 |
     | `describe-charges-before-inspecting` | 0 | 0 | 1 |
     | `stop-discards-output` | 1 | 2 | 5 |
     | `nat-range-deferred` | 0 | 0 | 4 |
     | `ill-typed-deferred` | 0 | 23 | 4 |

     Nine survive every golden and every run control outside the atomic set (the three `nat-range-` mutants, `ill-typed-tests-fuel`,
     `request-read-tests-fuel`, `d20-refusal-tests-fuel`, `display-refusal-tests-fuel`, `effect-counted-before-scalar-check` and
     `describe-charges-before-inspecting`) and die by that set alone; the other fourteen die by earlier controls too. Before the two
     twins added after review (`atomic-print-non-scalar-mid`, `atomic-request-rendered`) and the three `fuel-zero-*` controls counted by name,
     four of the 22 (`request-read-spends-entry`, `request-read-tests-fuel`, `enter-request-target-after-debit` and
     `effect-writes-before-scalar-check`) were killed by no atomic control and only by earlier ones; the requirement above is what closes that.
     Evaluator mutants 97 to 120, 284 in all (entry 39 adds eight: 128, and 292 in all).
   - **What this does not claim.** That a machine leaves its frames, `act`, `top`, cells and free lists as it found them: no vm-spec control
     sees them, and the text above says who does. That the release worklist and the tail entry's release-then-allocate can be made atomic
     cheaply: SPEC states the requirement and the fit rule (as if the release had happened), and a reclaiming VM (vm-rc) must size the release
     first or undo it; the model is atomic by construction and vm-core does not reclaim yet. That the room for a foreign's Result and for a
     conversion's blocks is checked in vm-core today: CORE.md choice 11 records that `$utf8out` grows memory before D20's scan and traps at 4 GiB;
     §10 now orders D20's check, then the room, then the call, and the fix is vm-io's.
   - **For the coordinator: not vm-spec's to edit.** `docs/COMPILER-CAMPAIGN.md` should record the ruling. Proposed row: "D25 | Atomic stops. A step
     that stops the machine (a refusal, a halt or an exhaustion of any kind) has no effect: the machine keeps the state in which the step began, and
     every check that a step can fail is decided before the step changes frames, `act`, `top`, the heap, the meters or the output. The one exception is
     the fuel debit of SPEC §7 and the Enter-debit rule that keeps it. | vm-lockstep found that the VM popped a Gather frame before it inspected its
     operands or tested NatRange, and that SPEC §6's table dropped `act` before Return to Top refused an ill-typed IO.OP, while the model and the
     sentence above the table were atomic. One rule for both machines makes a halted state comparable, and removes the lockstep's two named halting
     relations. |"
39. **Review round 1 of round 14: the order of two reads (the review's major finding).** SPEC §6.3 says that where two checks of one step would both
   stop the machine, the earlier names the stop, and that the words a step reads come first, "in the order of §6 and §9 (operand order), each with its
   request first (`Unsupported vm effect`) and then its type (`ill-typed`)". §6's Intrinsic row and §9 had said the operand order since `31aeaf25` ("inspect
   every operand over its §9 extent, in operand order"; `String.eq` and `String.append` read "`a` whole, then `b` whole"), and no golden or run control
   pinned it: the review's three one-edit mutants of `evaluate.py` that read a prim's second operand, or its second String, before its first
   (`prim-words-`, `prim-nat-` and `prim-string-read-second-first`) survived all 111 goldens and all 138 run controls. Its witnesses hand a prim a closure and
   a request as the two operands: the closure first is `HostFailure image` (`ill-typed`), the request first `Unsupported vm effect`, after 7 entries either
   way, and each plan validates and round-trips through the codec. The orders next to it were held (a request before a type at one word, a Halt's code
   before its message and before D20's check, an inspection before a charge), so the gap was the order between two words. The repair pins the order and
   keeps the text: narrowing §6.3 to the orders that were held would have weakened §6 and §9 to fit the gate.
   - **The probe.** Before any change the tree at `54b52a84` let five more one-edit mutants of the same rule survive every golden and run control:
     `Char.is_eq` alone (its own line in `prim`), `String.eq` alone and `String.append` alone (the review's String mutant edits both, so a pair for `append`
     alone would have killed it and left `eq`), and a String read with every cell before any Char word, or with the next cell before a Char word (`codes`;
     §9: "each SCon cell and its Char word, head to tail"). Each is the same finding in another place, so each place has its pair.
   - **The controls (12, D7).** `order_controls`, run controls 139 to 150, after the atomic controls in `run_controls`. A pair for each of `U32.add` (the one line
     of every word prim), `Char.is_eq`, `Nat.add` (every Nat prim), `String.eq`, `String.append` and a String's own reads (`String.reverse` of an SCon whose Char
     word and tail are the two bad words): `order-<pair>-closure-then-request` and `order-<pair>-request-then-closure`. The expected values were written by
     literal review before the first run: the closure first is `HostFailure image` (`ill-typed`), the request first `Unsupported vm effect`, each with `stdout`
     empty, `effects` 0 and `calls` 7 (main and the Base function 2, the identity of each bad word 2, the request's three entries) at fuel 1,000,000, and the
     reference evaluation reproduced all twelve on its first run with the unchanged evaluate.py. They are Book controls, so no host is called, and no seed
     claim, like the other controls that hand a request to a read.
   - **The mutants (8).** `ORDER_MUTANTS`: the review's three, with its edits verbatim; `prim-char-eq-`, `prim-string-eq-` and `prim-string-append-read-second-first`,
     one site each; and `string-chars-after-cells` and `string-tail-cell-before-char`. Each survives every golden and dies by the two order controls of its own
     pair and by no other control (four for the review's String mutant, which does both String prims). As for the atomic mutants, the gate requires more than a
     kill: at least one `order-*` control must change under each (`order` in the receipt row). Evaluator mutants 128, 292 in all (137 codec, 4 source, 128
     evaluator, 23 rule).
   - **What else the twelve kill, and what moved.** Sixteen earlier mutants also die by them: six of a request built and dropped or entered (`debit-at-perform`,
     `eager-effect`, `book-refuses-request-build`, `book-enters-k-without-effect`, `book-refuses-action-build`, `book-refuses-erased-application`, each by all
     twelve, since each builds a request), `word-request-as-ill-typed` and `view-request-as-ill-typed` (by the three request-first controls of the word prims and of
     the String reads), five that read less than their extent (`u32-arith-`, `char-prim-` and `nat-prim-first-unread`, `reverse-chars-unread` and
     `eq-reads-a-one-past-b`, by the pair of their prim), and three atomic mutants (`ill-typed-spends-entry`, `request-read-spends-entry`, `ill-typed-deferred`).
     Three rows of entry 38's table moved (40 to 46, 6 to 12 and 20 to 23), and the nine that die by the atomic set alone did not. SPEC §12's sentence that
     named `inspect-request-chr` and `-prim` as the only killers of a request taken for an ill-typed scalar, and its counts of the killers of the eager rule (ten
     goldens and twenty-four run controls, which round 13's three goldens and later controls had already outgrown) and of `book-enters-k-without-effect`
     (fourteen Book run controls), were re-measured on the tree: thirteen goldens and forty-six run controls, and thirty. The count of images on which
     the canonicality clauses are held against re-encoding (SPEC §12 and GATES.md said 5,797, stale since the atomic controls added admitted images) is the
     receipt's 5,843: 211 refusals, the 166 admitted controls, 111 goldens, 480 layouts and 4,875 perturbations, 527 of them noncanonical.
   - **Two survivors of the review that are no mutants.** `construct-nat-limit-first` (a Succ that tests the range before it inspects its word: an int always passes
     the inspection, and a non-int never reaches the range test) and `book-stop-discards-effects` (a Book's `effects` is always 0). Neither changes anything that
     the reference evaluation reports, so neither is added; the review's own other mutants (`view-type-before-request`, `word-type-before-request`,
     `halt-outgoing-before-code`, `effect-count-after-k`, `stop-discards-effects`, `stop-refunds-a-call`, `stop-keeps-quantum-of-fuel-only`) are killed today.
   - **What this does not claim.** That the order holds where the reference evaluation cannot show it: what a machine's frames hold when it names the stop is the
     lockstep's, and the operands of a foreign but `IO.print` and the byte List's whole extent are vm-io's, as before.

## What vm-model and vm-core must now follow (round 9)

Item 1 (D22) is superseded by round 11's items 1 to 3.

Each item names the SPEC text and the controls that freeze it; `check-spec.py`'s
`run_controls`, `plan_controls` and goldens are the shared harness, so merging this
branch brings all of them.

1. **D22 (§7 step 2, §8, §10; entry 21).** Under a Book entry `Enter(Action, [k])` stops
   `Unsupported vm effect` after its debit, before any operand is read, inspected or
   checked for D20, before the foreign id is checked and before any host call, for every
   foreign (`book-args`). Building an Action, dropping it and applying it to its erased
   `R` stay free, and the Program entry is unchanged (`program-print-through-id`, 9
   calls, `x\n`; round 10 replaced `program-print-in-value`, entry 27). Controls: `book-print`, `book-print-continuation-call`,
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
   unaffected. The counts are 96 goldens and 60 run controls (85 after round 10, 100 and 102 goldens after round 11, below), which vm-core's gate reads
   from SPEC §12.

## What vm-model and vm-core must now follow (round 10)

The review of round 9 changed no behaviour of the machine, so neither VM has to change for a
frozen control. Measured on the reviewer's builds, vm-core `dcc7c095` and vm-model `07e6db73`
(which still predate D22, entries 21 and 28): both agree with the 26 new inspection, UTF-8 and
`program-print-through-id` run controls (23, 2 and 1) and refuse the 16 new refusal controls with the
frozen reason. What changes is what they are held to, all by the harnesses that read `check-spec.py`:

1. **The run-control count is 85, the refusal count 87 (22 byte-level, 9 at the limits, 56
   plan-level).** vm-core's gate reads both from SPEC §12 and §4 (`run_control_count`,
   `refusal_counts`); the sentence shapes are unchanged and the numbers are new. vm-model reads
   the lists themselves.
2. **`stdout` and `effects` are compared on every Book control that stops at an Action (§8, entry
   28).** The eight controls freeze `stdout` empty and `effects` 0. vm-core's `expected_run` and
   vm-model's `agrees` already carry `stdout`; neither reads `effects`, which is the number of host
   calls the run made. vm-core compares it with the `knot_io` calls of its host trace, and vm-model
   with the effects its model performs, so that `book-args`, whose `IO.args` writes nothing, is
   checked as well (vm-core refuses that foreign at load today, so the control is the D22 item of
   round 9).
3. **`program-print-through-id` replaces `program-print-in-value`.** It is `x\n`, exit 0, after 9
   entries, and the seed prints `x` for its source on both lanes (entry 27). The shape that the seed
   refuses was left unfrozen in round 10, and D23 freezes it in round 11 (entry 31, finding 11).
4. **vm-model is bound to every §4 refusal (§4, entry 30).** It already refuses them with the
   reference's reason. It must also refuse two functions of one name, which its validator spells.
5. **The inspection points of §6 are frozen more widely (entry 29).** Each of the 43 inspection
   controls halts `HostFailure image` (`ill-typed`) after 2, 3, 4, 5 or 7 entries, the last with `x`
   already written; both VMs agree today. vm-prims owes the prim ids that no control names, one
   control per id and operand, and vm-io the byte List and the other foreigns' operands.
6. **A scalar String is written as canonical UTF-8.** `print-utf8-lengths` and
   `print-utf8-boundaries` freeze it after 5 entries; both VMs agree today.

## What vm-model and vm-core must now follow (round 11)

D23 changes the machine, so unlike round 10 both VMs must change: both perform an Action's effect where
it meets its continuation. `check-spec.py`'s goldens, `run_controls` and `evaluate.py` are the shared
harness, and SPEC §5 to §8, §10 and §12 are the text. Entry 31 has the reasons.

1. **Enter of an Action with `k` builds a request and performs nothing (§5, §7 step 2).** `dup` each of
   the Action's operands in order, allocate a class-5 Request (payload `foreign, operand…, k`: the Action's
   foreign word, the duplicated operands, and `k`, whose reference moves in; owning edges are the operands,
   then `k`), drop the Action, and Return the request. The step reads no operand, converts none, checks no
   foreign id and calls no host. vm-core's `$enter` Action branch performs through `$perform` today and
   vm-model's Action case performs; both move that to item 2. Round 9's Book guard goes, since a Book builds
   requests as a Program does: `book-drop` must evaluate `On{}`, and `book-request-dropped` (4 entries) too.
2. **Top's phase 3 is a loop (§8).** A request returned to Top(3) is performed in this order: inspect every
   operand over its whole extent (§6, §10), D20's scalar check, the host call and the Base result `r`; then
   `dup` `k`, drop the request, and continue with `Enter(k, [r])` with the phase still 3. Emit and Halt end it
   as before. It is a loop and not a recursion: frames must not accumulate across IO steps (a VM that enters
   `k` inside the Action's application nests one frame per step). The step is no entry and pays no fuel or
   quantum; the entries of the Action's second application and of `k` do, so no `calls` of a run that performs
   each request it builds moves.
3. **A request is never inspected (§6).** At every point of §6's list the class is read first, and a
   request (class 5) stops the run `Unsupported vm effect`, not `HostFailure image`: before the type test, before any
   state changes, and at an Enter's target before the operand count and the debit. A Let, Reference,
   Construct, Foreign, a Closure's captures, an Enter's operands and an Emit's field do not read a request.
   Controls: `program-case-request`, `book-request-rendered`, `book-request-field`, `inspect-request-chr`,
   `inspect-request-prim`, `inspect-request-keys`, `inspect-request-print`, `enter-request-target` and
   `fuel-zero-request-target` (the same Enter at fuel 5, which meets fuel 0 and is refused, not exhausted). *(Round 13, D24:
   a Case with a Default takes a request, so `inspect-request-keys` is now the run `case-request-default-keys`, and a Case
   is no read of this list when it has a Default.)*
4. **Seven frozen values move (each re-frozen in its own commit).**

   | control | before | now | why |
   |---|---|---|---|
   | `book-print`, `-continuation-call`, `-twice`, `-non-scalar`, `book-args` | 4 entries | 5 | the request reaches `got`, whose Case refuses it |
   | `book-print-ill-typed` | 5 | 6 | as above, one `id` call more; the ill-typed tail is never read |
   | `fuel-book-effect-exact` | fuel 4, refused after 4 | fuel 5, refused after 5 | at fuel 4 the run is `Exhausted` after 4 (`fuel-book-request-short`) |

   Outcome (`Unsupported vm effect`), `stdout` empty and `effects` 0 are unchanged. Everything else holds as
   frozen: the D20 goldens' `calls` (4, 4, 4, 13), `program-print-through-id` (9), the other fuel controls
   (`fuel-book-effect-short` at fuel 3 included), the 43 inspection controls, `halt-*`, the key controls and the 96
   earlier goldens.
5. **New expectations.** Goldens: `keep-swapped`, `keep-first`, `run2-flag` and `keep-non-scalar` (the seed's
   bytes, `kept`, `kept`, `first`, `kept`), `spine` (`first`, `second`) and `book-drop` (`On{}`, a Book,
   its lane declared `Unsupported parse parameter-type`). Fifteen run controls: `book-request-dropped`,
   `program-request-in-emit`, `program-request-dropped-let`, `program-request-dropped-argument`,
   `program-request-dropped-ill-typed`, `program-case-request`, `book-request-rendered`, `book-request-field`,
   `inspect-request-chr`, `-prim`, `-keys`, `-print`, `enter-request-target`, `fuel-zero-request-target` and
   `fuel-book-request-short`.
6. **Counts (§12, GATES.md).** 102 goldens; 100 admitted run controls, which vm-core's `run_control_count`
   reads from §12; refusals unchanged at 87 (22 byte-level, 9 at the limits, 56 plan-level); mutants 86 codec, 4
   source, 92 evaluator and 10 rule.
7. **Harness.** `stdout` and `effects` are compared as in round 10, and `effects` is now frozen on Programs
   too: 1 on `program-request-dropped-let`, `-argument` and `-ill-typed` (the one request the loop performs),
   0 on `program-request-in-emit`, `program-case-request` and `inspect-request-print`. The reference
   evaluation's `prints` and `effects` count only the requests that the loop performs. vm-core's `expected_run` and vm-model's `agrees`
   read `Unsupported vm effect` and the new calls without change; the seed's crash on a `main` that is itself a
   lambda (finding 13, corrected in round 12) is not something either VM should reproduce.

## What vm-model and vm-core must now follow (round 12)

The review of round 11 confirmed three findings (entries 32 to 34) and changed no rule of D23, so neither VM
has to change its machine for D23 beyond round 11's list; what changes is the set of images and controls
that they are held to. Not measured on the reviewer's builds of vm-core and vm-model, which are other
worktrees; the checks below are what the harnesses read from `check-spec.py`, SPEC §4, §8, §11 and §12.

1. **The loader refuses a type record's constructor count before it sizes anything (§4, entry 34).** For each
   data type record: its first constructor must be the constructor table's next (`constructor grouping`), then
   its count must fit what the table still holds (`constructor count`), then the name; and the counts sum to
   the table's size (`constructor count` again). A loader that sizes a list, a region or a table from the raw count
   before this check asks for 32 GiB at `0xFFFFFFFF` and traps or exhausts instead of reporting `HostFailure
   image`. Three new byte-level refusals, each on `second`: `type-grouping`, `type-count-max` and
   `type-count-short`, all `HostFailure image` with the reference reason where the VM reports one. The refusal
   count is 90 (25 byte-level, 9 at the limits, 56 plan-level); vm-core's `refusal_counts` reads it from §4.
2. **Six goldens with a request in a let, a field, an Emit or a capture (§8, §11, entry 32).**
   `let-dropped-request`, `let-live-request`, `field-request-returned`, `field-request-dropped`,
   `emit-field-request-dropped` and `capture-request-dropped` are Programs whose expected rows are the seed's
   bytes (`live\n`, `live\n`, `boxed-then-returned\n`, `live\n`, `live\n`, `live\n`, basis `seed`). Their rows are
   the outcome and the bytes, as every golden's is: no entry count is frozen for them (lockstep derives each
   golden's exact count later, §12). The machine of round 11 already produces them: the dropped request is built
   (debited) and never performed, and the loop performs the one request that a run returns. The goldens are 108.
3. **Three run controls for a Case with a Default over a request (§6, §8, entry 33).**
   `program-case-request-emit-default`, `-halt-default` and `-default-only` stop `Unsupported vm effect` after 7
   entries with nothing written and `effects` 0, as `program-case-request`. *(Superseded by D24: round 13's list
   item 2 says the opposite. A VM takes the Default of a Case over a request.)* The run
   controls are 103 (34 effect controls), which vm-core's `run_control_count` reads from §12.
4. **Nothing else moves.** No frozen value changed: the 102 earlier goldens, the 100 earlier run controls and the 87
   earlier refusals hold as frozen, and the seed witnesses (`golden/witnesses.json`, 14, §8 and §12) are
   evidence for the text, not obligations: the VMs do not read them.
5. **Counts (§12, GATES.md).** 108 goldens, 103 admitted run controls, 90 refusals (25 byte-level), 117 admitted
   controls in the gate line, mutants 89 codec, 4 source, 93 evaluator and 13 rule (199).

## What vm-model and vm-core must now follow (round 13)

Both VMs still implement the eager rule of round 8 (an Action's effect performed where it meets its continuation), and neither
has followed round 9's, 10's, 11's or 12's list. They next follow **D22, D23 and D24 together**, and this round's loader controls.
This list is the one to work from; the earlier lists remain the detail behind each item (entries 21 to 36). `check-spec.py`'s
`run_controls`, `plan_controls`, `byte_controls` and goldens are the shared harness, and merging this branch brings all of them.

1. **A request is a value, and only Top's loop performs it (D23; §5 class 5, §6, §7 step 2, §8; round 11's items 1 to 3).**
   `Enter(Action, [k])` builds a class-5 Request (`foreign`, the duplicated operands, `k`) and returns it: no operand read, no
   foreign id checked, no host call, and the Action's second application is the entry that is debited. Top's phase 3 is a loop:
   it inspects the request's operands whole, makes D20's scalar check, calls the host, builds the Base result, `dup`s `k`, drops the
   request and enters `k`, and ends only at an Emit or a Halt. A dropped request is no effect. D22 follows: a Book has no loop,
   so it never performs one (`book-drop` is `On{}`; `book-request-dropped` is 4 entries).
2. **A request is never inspected, except that a Case takes its Default (D24; §6, §6.1; supersedes round 12's item 3).**
   At every read of §6 the class is read first and a request stops the run `Unsupported vm effect`, whatever the type and before
   any state changes, and at an Enter's target before its operand count and its debit. The one exception: a **Case whose scrutinee
   is a request takes its Default**, in tags mode and in keys mode alike (a class-5 word reads no tag and no key, matches no row,
   and the Default binds nothing), at any scrutinee type, with or without rows (`program-case-request-emit-default`,
   `-halt-default`, `-default-only`: exit 0 after 7 entries, nothing written, `effects` 0; `case-request-default-at-flag` and
   `case-request-default-keys`: Books, `Evaluated 8 0 Off{}` after 6, the second at a keys Case; the goldens
   `case-request-emit-default-u32` prints `2`, `case-request-halt-default-u32` `4`, `case-request-emit-default` nothing). A Case
   **without** a Default, a tags Case whose every row names a constructor, still stops `Unsupported vm effect`
   (`program-case-request` and the seven Book controls that hand `got` a request). A keys Case has a Default always, so it never
   refuses one: round 11's `inspect-request-keys` (a refusal after 6) is now `case-request-default-keys` (a run after 6). A VM must
   not read the request's payload, perform it, or take a row. Only a plan that holds a Default takes one, and a compiler's plan
   does not (nest's checker expands a catch-all into a row for each remaining constructor): the five `-compiled` controls
   refuse the request, `Unsupported vm effect` with nothing written (four Programs after 8 entries, the Book after 6), and the two `-retested` controls, whose
   Default tests the slot again, take it (`3\n` after 13 entries, one effect); a VM follows the plan, not the source.
3. **Frozen values that are new or moved since round 8 (re-freeze each; the outcome, `stdout` and `effects` are otherwise as before).**
   `book-print`, `-continuation-call`, `-twice`, `-non-scalar` and `book-args` refuse after 5 entries (were 4), `book-print-ill-typed`
   after 6 (was 5), `fuel-book-effect-exact` at fuel 5 (was 4), and the three `program-case-request-*` Default controls, which round 12
   froze as `Unsupported vm effect` after 7 entries, run to exit 0 after the same 7 (D24). New controls: the request controls of round 11 (fifteen) and round 12's `call-shaped`
   goldens (six), the three D24 goldens, `case-request-default-at-flag`, and the seven of review round 1: the four
   Programs `case-request-emit-default-u32-compiled`, `-halt-default-u32-compiled`, `case-request-emit-default-compiled` and
   `case-request-nested-default-compiled`, the Book `case-request-book-both-plus-default-compiled`, and the two
   `case-request-both-plus-default-retested` and `-nested-default-retested`.
4. **`stdout` and `effects` are compared on every run control that freezes them** (`effects` is the number of host calls the run
   made: the `knot_io` calls of vm-core's trace, the effects of vm-model's model), and `calls` at every stop (§7: a stop keeps its debit).
5. **The loader refuses every image of `byte_controls` and `plan_controls`, and admits every admitted control (§2, §4).** Round 13
   adds 121 refusals, listed in SPEC §4 form by form. What a loader must now check that the earlier lists did not name: a name is
   well-formed UTF-8 (no overlong form, no surrogate, nothing above U+10FFFF, no cut or stray sequence) and admits every scalar,
   including non-ASCII names at each length (the two admitted names); each unused byte of a name is zero; all eight digest words;
   no repeated key in a keys row, no Construct of a nullary constructor, an Invoke of a live arrow takes one operand and of an
   erased arrow none, a Case's slot and scrutinee are one concrete type or the slot is `none`; and **the ten canonicality clauses**
   (§4 step 5: a loader with no encoder checks them one by one; `piecewise_rejected` is a model of it). Each refusal carries the
   reference's reason where the VM reports one.
6. **The counts, which both harnesses read from SPEC.** §4 states `freezes 211 refusals (124 byte-level, 9 at the limits, 78
   plan-level)` and §12 `111 admitted **run controls**` (42 effect controls); the sentence shapes are unchanged and the numbers
   are new. Goldens 111; admitted controls 127 (7 code lists, 111 runs, 8 admitted plan controls, `arity-at-limit`); mutants
   137 codec, 4 source, 97 evaluator and 23 rule (261). vm-model reads the lists themselves.
7. **Not obligations.** The 15 seed witnesses (`golden/witnesses.json`) and the codec's refusal accounting (`statement_audit`, finding
   12) are evidence for the text and for the reference; neither VM reads them.

## What vm-model and vm-core must now follow (round 14)

Round 13's list stands in full (D22, D23 and D24, the loader controls and the counts it states move as item 6 below says). Round 14 adds one rule, and
**the atomic stops of SPEC §6.3 (entry 38)**, with the order of its checks (entry 39), which vm-core and vm-model follow together with D22, D23 and D24.
`check-spec.py`'s `run_controls` is the shared harness, so merging this branch brings the 39 new controls (27 atomic, 12 order).

1. **A step that stops changes nothing (§6.3).** The machine keeps the state in which the step began: control pending, `act`, frames and `top`, every cell,
   the free lists and the bump pointer, the meters and everything written or called; the one change a stop leaves is the debit of an Enter whose step 2 or 3
   stopped. Every check is decided before the step's first change, and where two of them would stop the machine the earlier names the stop: the words that the
   step reads, in operand order (§6 and §9: a prim's operands from first to last, a String cell by cell, each SCon cell and then its Char word, head to tail), each
   with its request first and then its type; then the limits, in the order of the row's substeps. The order controls (item 5) freeze the words.
2. **vm-core.**
   - Gather completion (Construct's Succ and Chr, an Intrinsic): inspect every operand, in operand order, test `NatRange` and decide the room for the result
     **before** popping the Gather frame. This retires CORE.md choice 8's "stated limit" and the lockstep's `GATHER_POPPED` (23 runs).
   - Return to Top, at phase 0 as well as phase 3: the refusals of §8 (a Book's description: each word inspected and then charged, and the room for the text; a
     request's operands, D20's check and the room for the conversion; an IO.OP, a Halt's code and message and D20's check of it) come **before** `act` is
     dropped and before any output or host call. This retires `TOP_RELEASED` (`inspect-halt-code`, `inspect-halt-message`).
   - Eval Case: the room for the Scope and what the fields need are decided before either takes effect, so a heap stop at the predecessor leaves no Scope pushed.
     **`nat-pred-heap` freezes the old reading**: its `top` 65,572 counts the Scope that §6.1 used to leave pushed, and moves to 65,560, the `top` of
     `nat-pred-frames`; the row's basis (vm-spec D17, "the allocation follows the push") is now the order of the checks. `bump` and `calls` do not move.
   - Enter, steps 2 and 3: a stop keeps the debit and the pending Enter and nothing else; the callee's Activation is judged after the tail entry's pops and release
     (§6.2), and a Call frame on the region as it stands. Return, top InvokeFunction: the fit of the push is judged after the pop.
   - Describe inspects a word **before** it charges the visit (round-7 finding 2); `atomic-display-leaf-ill-typed` is the reference outcome of that ordering
     (the Nat word `1,048,574` and `Pair`: 1,048,576 visits, so an ill-typed `w` is refused, and a Flag `w` is `display`: `atomic-display-leaf-charged`).
   - §5's allocation-room rule holds for prims (`append`'s block) as it does at the ceiling rows.
3. **vm-model.** Its steps are atomic already: run the 27 atomic controls and the 12 order controls (they are run controls, at the fuel frozen with each), and check the three places where the text
   moved: a Book's description is part of the Return-to-Top step (the lockstep's trace folds it in, `advanced`; the model's own `run` ends at `Answered` after `act`
   is dropped, and a stop of the description must keep `act`), §6.1's stop leaves no Scope, and a tail entry's stop restores its Scopes and `act` (`body_entered` is
   atomic because a failure discards the whole transition).
4. **vm-lockstep.** Delete `GATHER_POPPED`, `TOP_RELEASED` and their counts (`halting_relations` in `frozen.json`, 23 and 2); compare a halt as any state, frames, `top`,
   `act` and heap included. Say which stops compare the pending control: today only the fuel stop's pending Enter is compared (95 fuel stops), because vm-core's
   registers cannot name any other. The display controls are `untraced`; the 27 controls and the `inspect-render-*` runs are witnesses for the description's
   stop once they are traced, and the 12 order controls are witnesses for the order in which a Gather completion inspects its operands.
5. **New expectations.** Twenty-seven run controls (§12): the 20 twins (fuel = `calls`; `stdout` and `effects` frozen, the three of a fuel stop among them), the five that
   stop after an effect, and the two of the display order. Both harnesses compare `stdout` and `effects` on every run control that freezes them and `calls` at every stop, as round 13's item 4 says.
   Then twelve order controls (`order-*`, §12, entry 39): a closure and a request handed to the two reads of one prim, once each way round, each after 7 entries with
   `stdout` empty and `effects` 0, and each stopped by the read that comes first, `ill-typed` when it is the closure and `Unsupported vm effect` when it is the
   request. The reads are the operands of a word prim, of `Char.is_eq` and of a Nat prim, the two Strings of `String.eq` and of `String.append`, and one String's cells.
6. **Counts (§12, GATES.md).** 150 admitted run controls, 166 admitted controls in the gate line (7 code lists, 150 runs, 8 admitted plan controls, `arity-at-limit`);
   211 refusals (unchanged: 124 byte-level, 9 at the limits, 78 plan-level), 111 goldens, 15 seed witnesses; mutants 137 codec, 4 source, 128 evaluator and 23 rule
   (292). The two sentence shapes that vm-core reads (`N admitted **run controls**`, `freezes N refusals (...)`) are unchanged in form.
7. **Witness states, by hand from §5 and §6 (not run on any machine: confirm them on the first run, D7).** At `nat-succ-range` the `NatRange` stop
   happens with four frames on the region: Top(0) (3 words), the Gather of `Nat.is_gt` (5), the Call frame of `succ`'s entry (4; the entry is not a tail entry,
   since a Gather lies between it and Top) and the Gather of the Succ with its operand (4), so `top` = F0 + 64 = 65,600 for this 696-byte image (F0 = 65,536).
   A machine that pops the Gather first shows 65,584. At `inspect-halt-code` and `inspect-halt-message` Return to Top(3) refuses with the Top frame alone (`top` =
   F0 + 12) and `act` the Activation of the closure whose body built the Halt, where a machine that drops `act` first shows 0.
8. **Not obligations, and later.** The release worklist and the tail entry's release-then-allocate are atomic in the model and required by §6.3 of any reclaiming VM
   (vm-rc: size the release first, or undo it); the room for a foreign's Result and for a conversion's blocks before the host call is vm-io's, with CORE.md choice 11
   (D20's check, then the room, then the call).

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
   Round 11's six goldens change it once more, as measured by the gate runner (all 21 gates passed) after
   `c5d98d11` against the same receipt: 893 files and `Unsupported lex literal` 220 (six more: each of
   `keep-swapped`, `keep-first`, `run2-flag`, `spine`, `keep-non-scalar` and `book-drop` exits 3, `Unsupported`, in
   the main-line parser). No row is `Invalid`, so the six stay six (`Invalid parse expected-=` 6 and `Invalid parse
   function-result` 10 are as before), every other count is unchanged, and both files agree across the two
   lanes. The merge condition stands, and no shared bootstrap receipt was refreshed.
   Round 12's six goldens and fourteen witnesses (round 13 moved three of the witnesses to goldens, so the corpus keeps
   their files) and main's four `tests/perch-arithmetic` sources (the merge of D24) change it once more,
   as measured by the gate runner (all 21 gates passed) at `024e7638` against the same receipt: 917 files, `Parsed` 163,
   `Unsupported lex literal` 238 (each new source exits 3 `Unsupported` in the main-line parser, the three promoted
   goldens at their `"x"`), `Unsupported parse declaration-form` 291 and `parameter-type` 59. No row is `Invalid`, so
   the six stay six (`Invalid parse expected-=` 6 and `function-result` 10 are as before), and both files agree across the
   two lanes. The merge condition stands, and no shared bootstrap receipt was refreshed.
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
11. **The seed refuses a Case over the IO.OP an applied effect answers; the VM performed the
   effect.** *Resolved in round 11 by D23 (entry 31).* `got(IO.print("x")(R)(k))` and a match that
   rebuilds `Emit` and `Halt` fail-stop on both seed lanes with the effect never firing
   (`tests/io/request_out_of_band.bend`; entry 27 lists the sources and bytes), and until round 10 §7
   performed the effect there, as vm-core and vm-model did. The finding described the boundary as a
   Case over the answer and offered two ways out: refuse the Case, or record a divergence by contract.
   The boundary is wider, and the answer is neither of the two as posed: the seed fires an effect only
   where the pure evaluator returns its request to the loop, so `keep(m1(..), m2(k))` printed `kept`
   on both lanes and `dropped` then `kept` under the eager rule (a divergence on a shape the seed
   *succeeds* on, which §11 forbids). D23 makes a request a value that only Top's loop performs, and
   a request that any read meets, the Case among them, `Unsupported vm effect`. (Round 12: even that boundary
   was narrower than said. Only a Case naming both constructors fail-stops on both lanes; finding 14.)
12. **Every refusal of the decoder and the validator is pinned, held by a raise, or unreached (rewritten in round 13;
   rounds 9 to 12 were wrong).** They said that 34, then 33, refusal statements of `serializer.py` were "pinned by no
   control" (13 because removing them only crashes the decoder, 20 because "no image at all" reaches them) and left them to
   the two VMs' gates. The review of round 12 showed the second half false: `name length` (a type named `''`, or a name record
   with a word too many), `tag case on a non-data type` (a tags Case on U32 with no rows and no Default), `key case on a
   non-scalar type` (a keys Case on a Flag that has a Default) and `tag table is not dense` (a Flag's table one row short)
   each have a one-edit image that the codec refuses and that a codec without the statement admits, and no frozen control was
   one of them, so a loader that omitted them passed every control the VMs are held to. The audit's "no image at all" was true of
   its own search only, and the inference from it, and the deferral to the VMs, were not. The same review found conditions inside
   the tests of statements that had a control, which no control reached: 19 of its 47 mutants survived every frozen
   control.
   The claim is held by the gate now, not by an audit's transcript (`statement_audit`, `CRASH_HELD_MUTANTS`, SPEC §12): the gate omits
   each of the codec's 100 refusals (`raise` statements, `fail` calls and `limit` calls, each turned into `pass` with the `return`
   or `continue` after it kept) and each operand of the `or` in the 78 tests that have one, in turn (178 omissions), and each is one of these:
   - **Killed (136).** A frozen image, refusal, verdict or admitted control changes when the omission is made. Among them are
     all the statements of the earlier list but the nine held or unreached below. Measured outside the gate, by re-running the
     reviewer's own 47 mutants (its probe `mut_codec.py`) against this tree: 44 die by a control (its decoder that accepts
     surrogates dies because `rejected` reads an encoder's refusal as a plan that no image encodes), and the three that remain
     are below.
   - **Held by a raise (33).** Omitting the refusal or the clause makes the reference raise on the control that pins it: four
     refusals (`name index`, `child offset`, `node record` and `constant index`, on `name-index-beyond`, `child-not-record`,
     `node-record-short` and `constant-index-beyond`), and twenty-nine clauses, each a bound that keeps an index or a key inside its
     table (`CRASH_HELD` names the control of each: an unknown kind, a record cut short, a tag beyond its type, a representation or
     a Construct that names an arrow, a table too long, a capture beyond the depth, and so on). §11 counts no crash as a kill, so the
     gate requires the raise on that control, and that nothing else kills the mutant. Three of the reviewer's mutants remove a whole
     bound and raise by construction (the entry kind and the constant kind index a table; the block of `tag case on a non-data
     type` takes its `return` with it, so `types[t]['constructors']` raises on every type that has none): each survives every
     frozen image and raises on its control (`entry-kind`, `constant-kind-unknown`, `tag-case-on-opaque`). The codec mutants
     `decoder-entry-kind-mod-2`, `decoder-constant-kind-mod-4` and `validator-tag-case-on-any-type` model the same omissions
     without a raise, and die by those controls.
   - **Unreached (5), each with its argument in `UNREACHABLE`.** `constructor order` (every constructor record has a tag below its
     type's count and no tag repeats, and the counts sum to the table, so the records fill every slot); the decoder's closing
     `opcode` and the validator's `unknown node` (`node record` refuses an opcode beyond the table, and the thirteen within it have a
     case each); the validator's `standalone {op}` (the decoder refuses a Branch or a Default that no Case holds, so the validator
     is handed none); the validator's `type index` (the decoder refuses a type word beyond the table first).
   - **The encoder's input checks (4).** `u32_list` (`text_spelling` holds it) and its two clauses, and an unknown plan node, which no
     decoded plan holds.
   A refusal or clause that a new statement adds and nothing pins fails the gate, as does an entry that a control has come to kill or
   that no longer raises where it is said to. What the gate does not claim: that no other image exists for an omission that is held or
   unreached (it argues the five, and shows the thirty-three raise), and anything about an operand of an `and`, a comparison's
   boundary or what a test computes (the audit drops only the operands of `or` tests). The earlier text's numbers (34, 33, 13, 20) are
   retired. *(Round 12: `constructor grouping` and the sum check of `constructor count` were pinned, by `type-grouping` and
   `type-count-short`; entry 34.)*
13. **The pinned seed crashes on a Program whose `main` is itself `R => k => ...`.** *Retired in round 12 as
   a seed defect about `let`; recorded as the seed fact about `main`'s form (entry 32).* The first report blamed
   a request bound by a `let` (`dead : IO.OP<R> = IO.print("dead")(R, x => Halt{7, "unreached"})`, then a body):
   exit 1 on both lanes without output, Bun `TypeError: s.fun is not a function. (In 's.fun(s.arg)', 's.fun' is
   an instance of Object)`, native `bend: memory fault (machine stack overflow?)`. The let is innocent. The
   reproducer below crashes on both lanes (witness `main-lambda-let`), crashes identically with the let deleted
   (`main-lambda-nolet`) and with any other body of a bare-lambda `main` (`main-lambda-print`, `-continue` and
   `-halt`), and runs once `main` is a call, with the let intact (golden `let-dropped-request`, `live` on both
   lanes). The same requests held by a
   parameter (`keep`, `pick`) ran because their `main` was a call. §11 does not bind the VM to a crash: it is
   no value. The owner is the coordinator, if the seed pin moves, and whoever writes the compiler campaign's
   differential tests: a source whose `main` is a lambda has no seed value to compare with. It crashes:

   ```
   def once(-R: Type, m: IO(Unit), n: IO(Unit), k: Unit -> IO.OP<R>) -> IO.OP<R>:
     dead : IO.OP<R> = m(R, x => Halt{7, "unreached"})
     n(R, k)
   def main() -> IO(Unit):
     R => k => once(R, IO.print("dead"), IO.print("live"), k)
   ```

   and this runs, printing `live` on both lanes:

   ```
   def run(m: IO(Unit), n: IO(Unit)) -> IO(Unit):
     R => k => once(R, m, n, k)
   def main() -> IO(Unit):
     run(IO.print("dead"), IO.print("live"))
   ```
14. **The seed's lanes disagree on a Case with a catch-all over a request; D23 refuses it (coordinator's choice).**
   *Resolved in round 13: the coordinator chose option b as D24, and entry 35 has the rule and the controls; entry 37
   records that nest's lowering emits no Default, so compiled programs do not reach it. The text below is the round-12
   record.* Recorded in entry 33, which has the measurements and the witnesses. D23 as decided is option a: every Case over
   a request is `Unsupported vm effect`, and the shapes on which the native lane succeeds are a recorded capability
   gap that no compiled program reaches, because the pinned literals head refuses every catch-all on an algebraic
   type. Option b, from review finding 2: a request selects no tag row, so a Case with a Default takes the
   Default and one without stops `Unsupported vm effect`. That is what the native lane does on all six shapes
   measured, and the Bun lane agrees on two of the three rows (the first and the third). It would change §6 and
   §6.1 (a class-5 scrutinee is not refused when the Case has a Default), the evaluator (`case-default-takes-request`
   becomes the rule, and the three `program-case-request-*` Default controls become runs that return the Default's
   value), three new goldens for the native lane's values (`2`, `4` and the empty output; basis `seed`, with the Bun
   lane recorded beside it), and both VMs' Case, which would take the Default of a class-5 word without reading
   its payload. It would change no compiled program. It is worth doing only if the self-hosting compiler is to emit
   a catch-all over an IO.OP, which its checker refuses today; the recommendation is to keep option a.
