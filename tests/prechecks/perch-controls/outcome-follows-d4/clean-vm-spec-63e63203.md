<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=63e63203bb2e; base=454bf3059679; builder=scripts/prechecks/packets@47dbd98ca1c7; sources: vm/SPEC.md@63e63203 sha256=9d65a6ae4cdd8b78181ff8846add9e6415c935f46dc2362d74aab6459815caed; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511; vm/golden/expectations.json@63e63203 sha256=e5c5c8b55866236578b95e6295901153d05ddd4a3af3339e06ed45b31fb00c83; vm/golden/expectations.json@63e63203 sha256=e5c5c8b55866236578b95e6295901153d05ddd4a3af3339e06ed45b31fb00c83 -->
# Claim
Outcome claims this branch changed:

vm/SPEC.md:572-576 (section: 8. Books, Programs and Actions) - verbatim text:

> **Book** (`IMAGE FN FUEL [ORDINALS…]`). These checks run in this order, before any
> 1. FUEL, then each ORDINAL left to right, is a decimal u32 word, else
>    `HostFailure arguments expected-u32`. eval-cli reads every word before it looks
>    `FN` up, so a malformed word refuses the invocation whatever `FN` names
>    (`absent x`) and whatever an earlier ordinal would be refused for
>    (`two F 9 x`).

vm/SPEC.md:586-592 (section: 8. Books, Programs and Actions) - verbatim text:

> **Book** (`IMAGE FN FUEL [ORDINALS…]`). These checks run in this order, before any
> 5. `FN`'s result type must be **describable**: algebraic, with every live field of
>    every constructor describable in turn. A cycle through algebraic types stays
>    describable (Nat's `Succ{Nat}`); a `none` field, an arrow and an opaque type are
>    not, so neither are the pinned Char (its U32 field) and String. Otherwise
>    `Unsupported invoke result-type`: Knot has no describe spelling for such a
>    result, so the VM refuses the request instead of inventing one (§11; goldens
>    `result-u32`, `result-u32-field`, `result-char` and `result-string`).

vm/SPEC.md:619-622 (section: 8. Books, Programs and Actions) - verbatim text:

> The bounds are
> inclusive: at most 1,048,576 visits and 16 MiB (16,777,216 bytes) of `tree`,
> separators included. A result that needs more is `Exhausted` kind 2 (`display`),
> never a truncated value (§12's four display run controls).

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap and representation: NatRange, RCOverflow, the image limits of `vm/SPEC.md` §4 (size, records per table, arity and slots), and display), and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. Kind 2 was widened in vm-spec review round 8: an image past a resource limit is exhausted, not malformed. |

vm/SPEC.md:662-742 (section: 9. Primitives and numeric bounds (D15)):

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
>   and `nat-succ-range` beyond it). A Nat Case binds `n-1` (`nat-pred`; a Big
>   predecessor in `nat-case-big`); Succ adds
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
> **Inspection.** Before a prim computes or allocates anything, §6 inspects each
> operand at the type and over the extent below, in operand order. A scalar's
> extent is its word; a String's is whole: each SCon cell and its Char word, head
> to tail, to SNil. The first ill-typed word halts with `HostFailure image`
> (`ill-typed`). No prim reads less than its extent, whatever its answer or its
> moves: a moved operand is inspected like any other, `append` reads the `b` it
> neither copies nor drops, and `eq` and `is_empty` read both lists to their ends
> although the answer may be known sooner.
>
> | Ids | Prims | Operands, read at | Extent | Moved |
> |---|---|---|---|---|
> | 0–15 | U32 `add` … `shrn` | `U32, U32`; `not` one `U32`; `shln`, `shrn` `U32, Nat` | each word | — |
> | 16 | `U32.to_nat` | `U32` | the word | the operand |
> | 17 | `U32.from_nat` | `Nat` | the word | the operand |
> | 18 | `Char.from_u32` | `U32` | the word | the operand |
> | 19 | `Char.to_u32` | `Char` | the word | the operand |
> | 20, 21 | `Char.is_eq`; `Char.is_space` | `Char, Char`; `Char` | each word | — |
> | 22–31 | Nat `add` … `is_ge` | `Nat, Nat` | each word | — |
> | 32, 33 | `U32.show`; `Nat.show` | `U32`; `Nat` | the word | — |
> | 34 | `String.eq` | `String, String` | `a` whole, then `b` whole | — |
> | 35 | `String.append` | `String, String` | `a` whole, then `b` whole | `b` |
> | 36–38 | `String.reverse`, `length`, `is_empty` | `String` | whole | — |
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

vm/SPEC.md:791-914 (section: 11. Outcomes and the Exhausted-lane rule):

> ## 11. Outcomes and the Exhausted-lane rule
>
> Accepted, Invalid, Unsupported, Exhausted, HostFailure and InternalFailure are
> recorded separately. Malformed images, unknown ids and malformed invocations are
> HostFailure, and an image past a resource limit of §4 is Exhausted kind 2; source forms Knot does not handle are Unsupported, and so is a Book
> result that §8 cannot describe and an effect that a Book entry would perform (D22); a broken invariant is a defect. A timeout or
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
> | literals eval | unary Nat and String up to 2^20 (`Exhausted primitive budget`: `nat-big`, `nat-range`); 1,048,576 transitions (`Exhausted eval budget`), one per term evaluated and one per successor or character materialized, so `Nat.is_gt(U32.to_nat(1048576),0n)` exhausts them; display 4,096 worklist steps and 65,536 characters (`Exhausted inspect budget`), two steps per constructor and two per field, so a tree of N constructors takes 4N − 2 and a Nat `n` renders only for `n` ≤ 1,023 |
> | knot-vm-1 | Nat at most 2^32-1; call fuel; §4's image limits (16 MiB, records, arity, `slots`); 16 MiB frames; 65,536 pages (4 GiB) of memory (D19); display bounds of §8 |
>
> `NatRange`, `RCOverflow`, §4's image limits and display are representation-resource
> exhaustion, kind 2 at the host boundary; the VM's own outcome keeps the precise
> cause, request and limit, because `exhausted(2)` alone does not say which bound
> was hit. Frame capacity is kind 3. Model tracing memory is a harness bound and
> never excuses the VM.
>
> **An exhausted eval lane** where the VM owes the seed's value is excused only by
> one of the three literals eval bounds, named by the phase eval-cli prints
> (`Exhausted<TAB>phase<TAB>budget`), and only when the program passes that budget.
> (Where a VM bound of golden/bounds.json applies, the VM's own outcome is Exhausted
> and eval's lane is only recorded.) The gate measures it without eval-cli
> (`check-spec.py` `EVAL_BOUNDS` and `reach`): `primitive` by the largest Nat or String
> length a node yields in the reference evaluation; `eval` by a lower bound on
> eval-cli's transitions, the terms the reference evaluation evaluates plus the Nat
> and String sizes its Literals and Intrinsics yield; `inspect` by the steps and
> characters of the seed's value. Any other Exhausted, or a documented one whose
> budget the program does not pass, is refused. For each excused lane,
> vm-expected.json and the receipt record the cause, the bound, the budget and the
> boundary reached.
>
> **The rule.** Wherever the seed succeeds inside the VM's declared domain and
> budgets, the VM MUST return the seed's value and effect trace, except the output
> D20 refuses (below). Another lane's
> exhaustion never excuses the VM. A VM that exhausts early, corrupts a result or
> reports an engine trap as a budget fails. Unsupported, timeout, unknown failure
> and a missing lane are neither Exhausted nor agreement. An Unsupported outcome is
> D4's refusal of a form Knot does not handle: a recorded capability gap, never a
> bound. Expected values are never regenerated from a candidate VM.
>
> **Non-scalar output (D20).** The program's own value decides it, never a seed
> lane. The reference evaluation of the plan ([evaluate.py](evaluate.py), §6–§10 on
> values) yields the Strings a Program passes to output effects, in order. It
> implements `IO.print`, the only effect the goldens use; any other foreign or a
> Halt fails the gate and counts as neither agreement nor D20 (a Halt's message is
> refused like a print's, §8, but only a run control reaches it). When one String holds
> a non-scalar Char, the VM writes the earlier Strings and refuses that one as
> `HostFailure io abi` (§10); the golden is `divergent-by-contract (non-scalar
> output)`, neither seed agreement nor a bound. Otherwise the case is ordinary seed
> agreement, whatever Chars the program builds. The seed lanes are recorded and never
> classify. The native lane exits 0 and writes every String as generalized UTF-8,
> surrogates included, but keeps only the low 8 bits of the lead byte from 2^21, so
> `Chr{67237376}` (0x401F600) writes `F0 9F 98 80`, the UTF-8 of U+1F600; its bytes
> must equal the whole trace in that encoding. The Bun lane refuses a non-scalar Char
> where it is constructed (`bend: N is not a Unicode scalar value`, exit 1), printed
> or not; its earlier output must be a prefix of the VM's, and a native-lane Program
> records it. D20 goldens: `print-non-scalar` (`IO.print(SCon{Chr{55296}, SNil{}})`,
> ASCII source; native `ED A0 80 0A`), `print-non-scalar-mid` (`"a\u{D800}b"`; native
> `61 ED A0 80 62 0A`, of which the VM writes nothing), `print-non-scalar-wide`
> (`Chr{67237376}`; native `F0 9F 98 80 0A`) and `print-non-scalar-second` (`"a"`, then
> the lone surrogate; the VM writes `a\n`, the Bun lane nothing). `non-scalar-code`
> (`55296\n`) and `non-scalar-unprinted` (`a\nnonempty\n`, where the Bun lane writes
> `a\n` and refuses) build a surrogate without printing it and agree with the seed.
> The refused entry stays debited (§7), so each D20 row of vm-expected.json freezes its
> `calls`, by literal review of the entries: 4 for the first three goldens (main,

[truncated after 12,288 bytes; 3,663 bytes omitted]

Frozen expectations that name the same cause:

`vm/golden/expectations.json:1690-1702` (frozen expectation code naming `result-char`)
```
 1690          "exit": 6,
 1691          "stdout": "",
 1692          "stderr": "InternalFailure\teval\tresult-tag\n"
 1693        }
 1694      },
 1695      {
 1696        "name": "result-char",
 1697        "source": "vm/golden/result-char.bend",
 1698        "lane": "literals",
 1699        "seed_stdout": "'a'\n",
 1700        "features": [
 1701          "Literal",
 1702          "describe"
```

`vm/check-spec.py:566-595` (frozen expectation code naming `result-string`)
```
  566  def print_argument(name: str, source: str, plan: dict, strings: dict, built: dict, registry: dict) -> str | None:
  567      """A Program `main = IO.print(e)` has no checked core in the pinned heads (Invalid parse
  568      function-result), so `e` is checked as the Book `main() -> String`, whose type table is
  569      `strings` (result-string's). Its projection, and that of every Base function it calls,
  570      must equal the hand plan's argument and functions."""
  571      m = PRINT.fullmatch(source)
  572      if not m:
  573          return None
  574      path = BUILD / 'print' / f'{name}.bend'
  575      path.parent.mkdir(parents=True, exist_ok=True)
  576      path.write_text(f'import Base\n\ndef main() -> String:\n  {m[1]}\n')
  577      shown = run([built['literals']['check'], '--bundle', '.', path.relative_to(ROOT)], 120)
  578      require(shown['exit'] == 0, (name, 'print argument not checked', shown))
  579      book = from_display(shown['stdout'], strings, '', registry)
  580      require(book[-1]['name'] == 'main', f'{name}: print argument book {[f["name"] for f in book]}')
  581      call = next(f for f in plan['functions'] if f['name'] == 'main')['body']
  582      require(call[0] == 'call' and plan['functions'][call[2]]['name'] == 'IO.print', f'{name}: main is not IO.print(e)')
  583      mine, theirs = (plan['types'], plan['functions']), (strings['types'], book)
  584      require(named(call[3][0], *mine) == named(book[-1]['body'], *theirs),
  585              (name, 'print argument differs from the checked core', book[-1]['body']))
  586      callees = called(call[3][0], plan['functions'])
  587      require(callees == {f['name'] for f in book[:-1]}, f'{name}: print argument calls {sorted(callees)}')
  588  
  589      def signature(f, types, functions):
  590          return ([types[p]['name'] for p in f['parameters']], types[f['result']]['name'], f['slots'],
  591                  named(f['body'], types, functions))
  592      for f in book[:-1]:
  593          mine_f = next(g for g in plan['functions'] if g['name'] == f['name'])
  594          require(signature(mine_f, *mine) == signature(f, *theirs), (name, f['name'], 'differs from the checked core'))
  595      return 'IO.print argument: checked-core'
```

`vm/check-spec.py:930-1014` (frozen expectation code naming `result-u32`)
```
  930  def expectation_controls(cases: dict, plans: dict, bounds: dict, sources: dict, evaluator=None) -> list:
  931      """What the rule must refuse: an eval lane that disagrees with the seed, a bound that is
  932      not Exhausted or that stands in for an Unsupported result, and a D20 classification that
  933      is not the program's own output."""
  934      def row(label, seed, ev):
  935          return {'name': f'control:{label}', 'seed': {'exit': 0, 'stdout': seed, 'stderr': ''},
  936                  'eval': {'exit': 0, 'stdout': ev, 'stderr': ''}}
  937  
  938      def without(name, *keys):
  939          return {k: v for k, v in cases[name].items() if k not in keys}
  940  
  941      def exhausted(label, seed, phase):
  942          return {**row(label, seed, ''), 'eval': {'exit': 4, 'stdout': '', 'stderr': f'Exhausted\t{phase}\tbudget\t0:0:0:0\n'}}
  943  
  944      def emoji(plan):
  945          """print-non-scalar-wide's plan printing U+1F600, which its native bytes cannot tell apart."""
  946          plan = json.loads(json.dumps(plan))
  947          plan['functions'][1]['body'][3][0][3][0][3][0][3] = 0x1F600
  948          return plan
  949      describe_bound = {'outcome': 'HostFailure', 'cause': 'invoke scalar-result',
  950                        'basis': 'round 1: a Book-describe bound, which section 11 no longer admits'}
  951      unprinted, second = cases['non-scalar-unprinted'], cases['print-non-scalar-second']
  952      out = []
  953      for label, name, case, table, plan in [
  954              ('eval-disagrees', 'value-on', row('eval-disagrees', 'Off{}\n', 'Evaluated\t0\t1\tOn{}\n'), bounds, None),
  955              ('eval-keeps-erased-field', 'erased-construct',
  956               row('eval-keeps-erased-field', 'ProofBox{Off{}, On{}}\n', 'Evaluated\t1\t0\tProofBox{Off{}}\n'), bounds, None),
  957              ('eval-nat-binds-n', 'nat-pred',
  958               row('eval-nat-binds-n', '2n\n', 'Evaluated\t0\t1\tSucc{Succ{Succ{Zero{}}}}\n'), bounds, None),
  959              ('bound-not-exhausted', 'value-on', cases['value-on'], {**bounds, 'value-on': describe_bound}, None),
  960              # Section 11: eval-cli's lane is excused only by a documented bound, past its budget.
  961              ('eval-undocumented-exhausted', 'nat-big',
  962               {**cases['nat-big'], 'eval': exhausted('', '', 'check')['eval']}, bounds, None),
  963              ('eval-primitive-within-budget', 'nat-pred', exhausted('eval-primitive-within-budget', '2n\n', 'primitive'),
  964               bounds, None),
  965              ('eval-transitions-within-budget', 'nat-pred', exhausted('eval-transitions-within-budget', '2n\n', 'eval'),
  966               bounds, None),
  967              ('eval-inspect-within-budget', 'nat-pred', exhausted('eval-inspect-within-budget', '1023n\n', 'inspect'),
  968               bounds, None),
  969              ('bound-for-unsupported', 'result-u32', cases['result-u32'], {**bounds, 'result-u32': describe_bound}, None),
  970              # Section 11: a Book's eval lane is unavailable only where its review declares the exact
  971              # Unsupported line that the head prints; no 
[truncated after 6,144 bytes; 4,401 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
