<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=0f511b06ba24; base=454bf3059679; builder=scripts/prechecks/packets@40e325337e4a; sources: vm/SPEC.md@0f511b06 sha256=62e8be5ac99176eeb33a59b31bed499df195a64d85810e1d25259b42b4e2224a -->
# Claim
Outcome claims this branch changed:

vm/SPEC.md:218-220 (section: 4. Validation) - verbatim text:

> 1. Size first: an image above 16 MiB (4,194,304 words) is `Exhausted image-size`,
>    even when it is also malformed. Then length, magic, version, total, entry kind,
>    reserved word and registry digest.

vm/SPEC.md:231-232 (section: 4. Validation) - verbatim text:

> A refused image is `HostFailure image` with a reason. `check-spec.py` freezes 61
> refusals (20 byte-level, 41 plan-level); vm-core MUST refuse the same controls.

vm/SPEC.md:233-235 (section: 4. Validation) - verbatim text:

> Validation establishes these rules, not type soundness: a `none`-typed value may
> be instantiated at any type (§3), so the VM's inspection (§6) and entry check
> (§7) refuse the rest at run time as `HostFailure image` (`ill-typed`).

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

vm/SPEC.md:491-547 (section: 9. Primitives and numeric bounds (D15)):

> ## 9. Primitives and numeric bounds (D15)
>
> **Registry.** `registry.json` freezes ids 0..38 exactly as literals' `primitive.bend`
> `code` table orders them (derived and re-checked mechanically by the gate), with
> each Base name, input kinds, quantities and output. It reserves 39 `U32.or` and 40
> `U32.xor`: base-pin's SHA-256 needs them, and they stay refused until vm-prims
> freezes seed witnesses for them. `U32.not` is already id 5. New ids append; a
> changed meaning or binary grammar needs a new version.
>
> **Derivation rule.** A reachability pass over the **final merged S**, from
> compile-cli and parse-cli, follows calls, value references and selected foreign
> bodies after erasure. Each reachable seed intrinsic either has a registered prim
> with the seed's semantics, or compilation is Unsupported. Each reachable non-prim
> body that inspects an immediate representation (in particular `U32{Word}`) is
> rejected. The pass is rerun whenever S changes; 41 ids today do not claim S's
> registry is complete.
>
> **Semantics** (the pinned Base bodies, on words):
> - U32 `add`, `sub` and `mul` wrap modulo 2^32; comparisons are unsigned; `div` by 0
>   is 0 and `mod` by 0 is the dividend; `shln` and `shrn` by 32 or more give 0;
>   `not` and `and` are bitwise. Witnesses: `u32-wrap`, `u32-sub-wrap`,
>   `u32-mul-wrap`, `u32-unsigned`, `u32-lt-unsigned`, `u32-div-zero`,
>   `u32-rem-zero`, `u32-not`, `u32-and`, `u32-cmp`; shifts below 32 `u32-shr` (by
>   31); shifts by 32 or more `u32-shift` (`shln` by 32), `u32-shl-33`, `u32-shr-32`
>   and `u32-shr-33`, the last three observed as a Nat rather than through an
>   equality. Equalities answer False as well as True (`u32-ne`, `nat-ne`,
>   `char-ne`, `string-ne-order`, `string-ne-length`).
> - Nat `sub` floors at 0 (`base.bend` lines 562–571; `nat-sub-floor`). `add`, `mul`,
>   Succ and every conversion check the mathematical result before narrowing:
>   above 2^32-1 is `Exhausted` kind 2 (`NatRange`), never U32 wraparound
>   (`nat-big` and `u32-to-nat-big` inside the bound; `nat-range`, `nat-mul-range`
>   and `nat-succ-range` beyond it). A Nat Case binds `n-1` (`nat-pred`); Succ adds
>   one (`nat-succ`); `Nat.cmp` orders (`nat-cmp`).
> - `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32` keep the word.
>   `Char.is_space` is 9..13 or 32 (`base.bend` 1765–1768; `char-space`).
> - Bool is False 0, True 1; Cmp is LT 0, EQ 1, GT 2.
> - String is the immutable Chr list: `eq` compares length and codes, `append`,
>   `reverse`, `length` and `is_empty` observe the list, and `U32.show`/`Nat.show`
>   give unsigned decimal without leading zeros except `0`. `string-codes` and
>   `nat-show-codes` observe `append`, `reverse` and `show` through their character
>   codes, not through `String.eq`.
>
> **Ownership.** Every prim borrows its operands, and §6 drops them after the result
> is allocated, except for these moves, which consume the operand into the result:
> `String.append(a,b)` moves `b`, whose reference becomes the result's tail, and
> drops only `a`; `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32`
> move their operand word, which is the result (a Big cell is reused, never copied
> or dropped). Golden `string-append-mortal` appends a freshly allocated `b`, so
> dropping it as well is a use after free.
>
> **Allocation order.** A String result is allocated last cell first: `append(a,b)`
> copies `a`'s cells onto the moved `b` from `a`'s last character to its first;
> `reverse(a)` allocates from `a`'s first character; `show` from its last digit. A
> Big result is allocated before the operands are dropped. Prims still without a
> golden witness (U32 `is_ne/le/ge`, `U32.from_nat`, `Char.from_u32`, and Nat
> `is_ne/lt/le/ge`) owe edge witnesses in vm-prims: 0, 1, 2^31 and 2^32-1.
>

vm/SPEC.md:584-637 (section: 11. Outcomes and the Exhausted-lane rule):

> ## 11. Outcomes and the Exhausted-lane rule
>
> Accepted, Invalid, Unsupported, Exhausted, HostFailure and InternalFailure are
> recorded separately. Malformed images, unknown ids and malformed invocations are
> HostFailure; source forms Knot does not handle are Unsupported, and so is a Book
> result that §8 cannot describe; a broken invariant is a defect. A timeout or
> crash never counts as a semantic mutant kill.
>
> The observation lanes are the seed, pinned Knot eval-cli, the Bend model on the
> image, and the Wasm VM on the image. The seed's **native** lane (the C1 lane) is
> the reference; its Bun lane is a cross-check. A lane may be excused **only** by a
> documented bound, and its receipt must name the bound, the budget and the boundary
> reached:
>
> | Lane | Documented bounds (observed evidence) |
> |---|---|
> | seed native | Nat to about 2^48; its runtime resources |
> | seed Bun | about 32K stack frames (`List.length`); unary Nat materialization: `nat-big` passed 60 GB of RSS in about 6 minutes and was stopped, so word-Nat goldens use the native lane |
> | literals eval | unary Nat and String up to 2^20 (`nat-big`, `nat-range`: `Exhausted primitive budget`); at most 1,048,576 transitions; display 4,096 visits and 65,536 characters |
> | knot-vm-1 | Nat at most 2^32-1; call fuel; 16 MiB image; 16 MiB frames; 65,536 pages (4 GiB) of memory (D19); display bounds of §8 |
>
> `NatRange`, `RCOverflow`, image size and display are representation-resource
> exhaustion, kind 2 at the host boundary; the VM's own outcome keeps the precise
> cause, request and limit, because `exhausted(2)` alone does not say which bound
> was hit. Frame capacity is kind 3. Model tracing memory is a harness bound and
> never excuses the VM.
>
> **The rule.** Wherever the seed succeeds inside the VM's declared domain and
> budgets, the VM MUST return the seed's value and effect trace. Another lane's
> exhaustion never excuses the VM. A VM that exhausts early, corrupts a result or
> reports an engine trap as a budget fails. Unsupported, timeout, unknown failure
> and a missing lane are neither Exhausted nor agreement. An Unsupported outcome is
> D4's refusal of a form Knot does not handle: a recorded capability gap, never a
> bound. Expected values are never regenerated from a candidate VM.
>
> [golden/vm-expected.json](golden/vm-expected.json) applies the rule to every
> golden: the eval-cli line where eval agrees with the seed (70 goldens), agreement
> meaning that eval's tree equals the seed's printed value in §8's spelling (no
> spaces, erased fields dropped by the golden's declarations, a Nat unary); the seed's
> value rendered by §8 where eval is excused (`nat-big`, `u32-to-nat-big`);
> `Exhausted` kind 2 `NatRange` where the seed's value lies outside the VM's domain
> (`nat-range`, `nat-mul-range`, `nat-succ-range`), each justified in
> [golden/bounds.json](golden/bounds.json), whose entries are all Exhausted;
> `Unsupported invoke result-type` where `main`'s result type is outside §8's
> describe domain (`result-u32`: the seed prints `5`, eval-cli reports the
> `InternalFailure eval result-tag` defect recorded in DECISIONS.md), derived from the
> image's type table and never listed as a bound; and the seed's stdout for the Programs
> `foreign-print` and `io-bind`. For those Programs the eval lane is not excused but
> unavailable: both literals `eval-cli` and `check-cli` report
> `Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
> runs. Under D4 that should be Unsupported; it is recorded as observed, not
> relabelled, and their plans follow §1 by hand. `io-bind` keeps Base's `IO.bind`
> and `IO.pure` unspecialized, so its `A`-typed nodes are `none`.
>

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
