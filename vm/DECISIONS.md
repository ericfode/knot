# D15–D18: proposed exact wording, and points for the coordinator

D15–D18 were adopted at `454bf30` in `docs/COMPILER-CAMPAIGN.md`. The wording below
is what [SPEC.md](SPEC.md) implements; it refines the adopted rows without
changing their direction. This executor does not edit the campaign decision table.
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
10. **Non-scalar output is a divergence by contract (D20).** Review round 3 found
   §11's reference lane and §10's IO contract in conflict: the seed's native lane
   writes a non-scalar Char as generalized UTF-8 (`print-non-scalar`, ASCII source
   `IO.print(SCon{Chr{55296}, SNil{}})`, bytes `ED A0 80 0A`), while `knot-io`
   refuses it. Under D20 the VM refuses the whole String as `HostFailure io abi`
   before the host call (§10); the golden keeps the native bytes as hex, is marked
   `divergent-by-contract (non-scalar output)` and is never counted as agreement
   (§11). The seed's Bun lane refuses the same output and is recorded beside it.
   `print-non-scalar-mid` (`"a\u{D800}b"`) pins that no part of the String is
   written. The expectation rule refuses undeclared non-scalar output, a
   divergence on scalar output, another class and a VM output that does not
   precede the first non-scalar (four controls).
11. **Plans spell a String as its code list.** Round 3 also found the reference
   codec lossy: plans spelled String constants as JSON text, so `json.loads`
   merged a surrogate pair into U+1F600 and decode refused codes above U+10FFFF
   that encode wrote. Plans and decode now use code lists, encode refuses a text
   spelling, and seven admitted code-list controls and two goldens
   (`string-surrogate-pair`, seed `False{}`; `string-beyond-unicode`, seed `1n`)
   pin §2's "every u32 code, in order". No committed image changed.

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
   Measured by the gate runner on this branch after merging main (`481bb31`)
   against main's committed receipt, the parse histogram moves from 785 to 876
   files: `Parsed` 144 to 162, `Unsupported lex literal` 185 to 210,
   `Unsupported parse declaration-form` 239 to 280, `parameter-type` 57 to 58,
   `Invalid parse expected-=` 2 to 6 and `Invalid parse function-result` 8 to 10.
   Exactly these six goldens account for the new Invalid rows; the 23 goldens of
   review round 1, the 3 of round 2 and the 4 of round 3 all end Unsupported. **When the coordinator refreshes these
   receipts, the six Invalid rows must not be accepted as a baseline.** Owner:
   merge-wave, whose closures merge should turn them into parses or Unsupported
   first; otherwise the refresh records them as known D4 debt with that owner.
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
