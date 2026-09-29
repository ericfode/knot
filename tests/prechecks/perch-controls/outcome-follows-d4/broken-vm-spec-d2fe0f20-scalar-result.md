<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=d2fe0f2048fb; base=454bf3059679; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/SPEC.md@d2fe0f20 sha256=8766740dd99fadc82c5e393412a0b972bdffdcdb3de02162ce8dcbb2b86fa508; vm/golden/write-sources.py@d2fe0f20 sha256=e2632c0f73731e6e3ef52cc6c319cea1c38c218c5c7c0042da3a8c2594cb7623 -->
# Claim
Outcome claims this branch changed:

vm/SPEC.md:410-417 (section: 8. Books, Programs and Actions) - verbatim text:

> A Nat word
> `n` renders as its logical view, `n` times `Succ{`, then `Zero{}`, then `n` times
> `}`. Erased fields do not exist and are not printed (golden `erased-construct`:
> eval-cli prints `ProofBox{On{}}`, the seed `ProofBox{Off{}, On{}}`). eval-cli
> reports `InternalFailure eval result-tag` for any U32, Char or String result, so
> the VM reports `HostFailure invoke scalar-result` for one anywhere in the tree;
> a closure is `function-result` and an untyped (`none`) immediate is
> `abstract-result`.

vm/SPEC.md:412-417 (section: 8. Books, Programs and Actions) - verbatim text:

> Erased fields do not exist and are not printed (golden `erased-construct`:
> eval-cli prints `ProofBox{On{}}`, the seed `ProofBox{Off{}, On{}}`). eval-cli
> reports `InternalFailure eval result-tag` for any U32, Char or String result, so
> the VM reports `HostFailure invoke scalar-result` for one anywhere in the tree;
> a closure is `function-result` and an untyped (`none`) immediate is
> `abstract-result`.

vm/SPEC.md:412-419 (section: 8. Books, Programs and Actions) - verbatim text:

> Erased fields do not exist and are not printed (golden `erased-construct`:
> eval-cli prints `ProofBox{On{}}`, the seed `ProofBox{Off{}, On{}}`). eval-cli
> reports `InternalFailure eval result-tag` for any U32, Char or String result, so
> the VM reports `HostFailure invoke scalar-result` for one anywhere in the tree;
> a closure is `function-result` and an untyped (`none`) immediate is
> `abstract-result`. Rendering is iterative, bounded by 1,048,576 visits and 16 MiB
> of text; hitting either is `Exhausted` kind 2 (`display`), never a truncated
> value.

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

vm/SPEC.md:440-479 (section: 9. Primitives and numeric bounds (D15)):

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
>   `not` and `and` are bitwise. Witnesses: `u32-wrap`, `u32-unsigned`,
>   `u32-div-zero`, `u32-rem-zero`, `u32-shift`, `u32-shr`, `u32-not`, `u32-cmp`.
> - Nat `sub` floors at 0 (`base.bend` lines 562–571; `nat-sub-floor`). `add`, `mul`,
>   Succ and every conversion check the mathematical result before narrowing:
>   above 2^32-1 is `Exhausted` kind 2 (`NatRange`), never U32 wraparound
>   (`nat-big` inside the bound, `nat-range` beyond it).
> - `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32` keep the word.
>   `Char.is_space` is 9..13 or 32 (`base.bend` 1765–1768; `char-space`).
> - Bool is False 0, True 1; Cmp is LT 0, EQ 1, GT 2.
> - String is the immutable Chr list: `eq` compares length and codes, `append`,
>   `reverse`, `length` and `is_empty` observe the list, and `U32.show`/`Nat.show`
>   give unsigned decimal without leading zeros except `0`.
>
> **Allocation order.** A String result is allocated last cell first: `append(a,b)`
> copies `a`'s cells onto `b` (moved) from `a`'s last character to its first;
> `reverse(a)` allocates from `a`'s first character; `show` from its last digit. A
> Big result is allocated before the operands are dropped. Prims without a golden
> witness (U32 `sub`, `mul`, `and`, `is_ne/lt/le/ge`, the conversions, and Nat
> `cmp`, `is_ne/lt/le/ge`) owe edge witnesses in vm-prims: 0, 1, 2^31 and 2^32-1.
>

vm/SPEC.md:510-553 (section: 11. Outcomes and the Exhausted-lane rule):

> ## 11. Outcomes and the Exhausted-lane rule
>
> Accepted, Invalid, Unsupported, Exhausted, HostFailure and InternalFailure are
> recorded separately. Malformed images and unknown ids are HostFailure; source forms
> Knot does not handle are Unsupported; a broken invariant is a defect. A timeout or
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
> | knot-vm-1 | Nat at most 2^32-1; call fuel; 16 MiB image; 16 MiB frames; 128 MiB memory; display bounds of §8 |
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
> and a missing lane are neither Exhausted nor agreement. Expected values are never
> regenerated from a candidate VM.
>
> [golden/vm-expected.json](golden/vm-expected.json) applies the rule to every
> golden: the eval-cli line where eval agrees with the seed (52 goldens); the seed's
> value rendered by §8 where eval is excused (`nat-big`); `Exhausted` kind 2
> `NatRange` where the seed's value lies outside the VM's domain (`nat-range`,
> justified in [golden/bounds.json](golden/bounds.json)); and the seed's stdout for
> the Program `foreign-print`. For that Program the eval lane is not excused but
> unavailable: both literals `eval-cli` and `check-cli` report
> `Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
> runs. Under D4 that should be Unsupported; it is recorded as observed, not
> relabelled, and its plan follows §1 by hand.
>

Frozen expectations that name the same cause:

`vm/golden/write-sources.py:57-85` (frozen expectation code naming `erased-construct`)
```
   57  put('nat-unpack','import Base\n\n'+flag+'def pred(x: Nat) -> Flag:\n  match x:\n    case 0n: Off{}\n    case 1n+n: On{}\n\ndef main() -> Flag:\n  pred(2n)\n','On{}',features=('Literal','Case','Branch'))
   58  # Added by the Claude continuation of vm-spec, frozen before their plans were written.
   59  more=[
   60   ('nat-sub-floor','Nat.is_eq(Nat.sub(2n,5n),0n)'),
   61   ('char-space','Bool.and(Char.is_space(Char.from_u32(9)),Bool.not(Char.is_space(Char.from_u32(14))))'),
   62   ('u32-show','String.eq(U32.show(4294967295),"4294967295")'),
   63   ('string-length','Nat.is_eq(String.length("abc"),3n)'),
   64   ('u32-not','U32.is_eq(U32.not(0),4294967295)'),
   65   ('u32-shr','U32.is_eq(U32.shrn(2147483648,31n),1)'),
   66   ('nat-mul','Nat.is_eq(Nat.mul(3n,4n),12n)'),
   67   ('nat-show','String.eq(Nat.show(10n),"10")'),
   68   ('char-eq',"Char.is_eq('a','a')"),
   69  ]
   70  for name,body in more:
   71   put(name,'import Base\n\ndef main() -> Bool:\n  '+body+'\n','True{}',features=('Literal','Intrinsic'))
   72  put('u32-cmp','import Base\n\ndef main() -> Cmp:\n  U32.cmp(4294967295,1)\n','GT{}',features=('Literal','Intrinsic'))
   73  put('case-char','import Base\n\n'+flag+"def vowel(c: Char) -> Flag:\n  match c:\n    case 'a': On{}\n    case 'e': On{}\n    case _: Off{}\n\ndef main() -> Flag:\n  vowel('e')\n",'On{}',features=('Literal','Case','Branch','Default'))
   74  flags='type Flags is Data:\n  Stop{}\n  Push{head: Flag, tail: Flags}\n\n'
   75  put('recursion-map',flag+flags+flip+'def flip_all(xs: Flags) -> Flags:\n  match xs:\n    case Stop{}: Stop{}\n    case Push{h,t}: Push{flip(h),flip_all(t)}\n\ndef main() -> Flags:\n  flip_all(Push{On{},Push{Off{},Stop{}}})\n','Push{Off{}, Push{On{}, Stop{}}}',features=('Application','Construct','Case','recursion'))
   76  put('recursion-tail',flag+flags+'def last(xs: Flags, d: Flag) -> Flag:\n  match xs:\n    case Stop{}: d\n    case Push{h,t}: last(t,h)\n\ndef main() -> Flag:\n  last(Push{Off{},Push{On{},Stop{}}},Off{})\n','On{}',features=('Application','Case','tail'))
   77  put('erased-construct',flag+erased+'def main() -> ProofBox:\n  ProofBox{Off{},On{}}\n','ProofBox{Off{}, On{}}',features=('erasure','Construct'))
   78  put('closure-captures',flag+pair+'def swap(a: Flag, b: Flag) -> Pair:\n  f : Flag -> Pair = x => Pair{b,a}\n  f(Off{})\n\ndef main() -> Pair:\n  swap(Off{},On{})\n','Pair{On{}, Off{}}','closures',('Closure','Invoke','capture'))
   79  # Word-Nat witnesses: the seed's native lane is their reference (see SPEC section 9).
   80  put('nat-big','import Base\n\ndef main() -> Bool:\n  Nat.is_eq(Nat.add(2147483647n,1n),2147483648n)\n','True{}',features=('Literal','Intrinsic','bound'),seed_lane='native')
   81  put('nat-range','import Base\n\ndef main() -> Bool:\n  Nat.is_gt(Nat.add(4294967295n,1n),4294967295n)\n','True{}',features=('Literal','Intrinsic','bound'),seed_lane='native')
   82  put('foreign-print','import Base\n\ndef main() -> IO(Unit):\n  IO.print("vm")\n','vm',features=('Foreign',))
   83  Path('vm/golden/plan.json').write_text(json.dumps({'basis':'Literal observations fixed before the serializer or VM implementation. Separate evaluator heads; no VM yet.','cases':cases},indent=2)+'\n')
   84  print('sources',len(cases))
   85  
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
