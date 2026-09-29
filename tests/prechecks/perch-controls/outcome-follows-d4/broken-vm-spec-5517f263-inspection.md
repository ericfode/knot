<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=5517f2638f3e; base=454bf3059679; builder=scripts/prechecks/packets@40e325337e4a; sources: vm/SPEC.md@5517f263 sha256=f52eca73e1ba4882f5180bc729ade834c5ff29a230b1843746d4821fc244b5df; vm/check-spec.py@5517f263 sha256=2c2bf64534fb1cfa4e4a303ece215db7407b4237db5b788a9d2143053a3ddeee; vm/check-spec.py@5517f263 sha256=2c2bf64534fb1cfa4e4a303ece215db7407b4237db5b788a9d2143053a3ddeee; vm/check-spec.py@5517f263 sha256=2c2bf64534fb1cfa4e4a303ece215db7407b4237db5b788a9d2143053a3ddeee -->
# Claim
Outcome claims this branch changed:

vm/SPEC.md:247-249 (section: 4. Validation) - verbatim text:

> 1. Size first: an image above 16 MiB (4,194,304 words) is `Exhausted image-size`,
>    even when it is also malformed. Then length, magic, version, total, entry kind,
>    reserved word and registry digest.

vm/SPEC.md:260-266 (section: 4. Validation) - verbatim text:

> A refused image is `HostFailure image` with a reason. `check-spec.py` freezes 62
> refusals (20 byte-level, 42 plan-level); vm-core MUST refuse the same controls,
> and MUST admit its six admitted plan controls (three Cases on a `none` slot,
> among them `list-head-match`, and three whose arms fit their Case, among them
> `first-code`, S's shapes), its seven code-list controls and its 23 run
> controls; vm-model and vm-core MUST run each run control, at the fuel frozen with
> it, to the outcome frozen with it (§7, §12).

vm/SPEC.md:267-269 (section: 4. Validation) - verbatim text:

> Validation establishes these rules, not type soundness: a `none`-typed value may
> be instantiated at any type (§3), so the VM's inspection (§6) and entry check
> (§7) refuse the rest at run time as `HostFailure image` (`ill-typed`).

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

vm/SPEC.md:608-688 (section: 9. Primitives and numeric bounds (D15)):

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

vm/SPEC.md:732-815 (section: 11. Outcomes and the Exhausted-lane rule):

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
> Halt fails the gate and counts as neither agreement nor D20. When one String holds
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
>
> [golden/vm-expected.json](golden/vm-expected.json) applies the rule to every
> golden: the eval-cli line where eval agrees with the seed (75 goldens), agreement
> meaning that eval's tree equals the seed's printed value in §8's spelling (no
> spaces, erased fields dropped by the golden's declarations, a Nat unary); the seed's
> value rendered by §8 where eval is excused (`nat-big`, `u32-to-nat-big`,
> `nat-case-big`);
> `Exhausted` kind 2 `NatRange` where the seed's value lies outside the VM's domain
> (`nat-range`, `nat-mul-range`, `nat-succ-range`), each justified in
> [golden/bounds.json](golden/bounds.json), whose entries are all Exhausted;
> `Unsupported invoke result-type` where `main`'s result type is outside §8's
> describe domain (`result-u32`, `result-u32-field`, `result-char`,
> `result-string`: the seed prints `5`, `Box{5}`, `'a'` and `"ab"`, and eval-cli
> reports the `InternalFailure eval result-tag` defect recorded in DECISIONS.md
> each time), derived from the
> image's type table and never listed as a bound; the seed's stdout for the Programs
> `foreign-print`, `io-bind`, `non-scalar-code` and `non-scalar-unprinted`; and D20's
> refusal for `print-non-scalar`, `print-non-scalar-mid` and `print-non-scalar-wide`,
> with no output, and for `print-non-scalar-second` after `a\n`. For those
> Programs the eval lane is not excused but unavailable: both literals `eval-cli`
> and `check-cli` report `Invalid parse function-result` for
> `def main() -> IO(Unit)`, a program the seed runs. Under D4 that should be Unsupported; it is recorded as observed, not
> relabelled, and their plans follow §1 by hand. `io-bind`, `non-scalar-unprinted`
> and `print-non-scalar-second` keep Base's `IO.bind` (and `IO.pure`) unspecialized,
> so their `A`-typed nodes are `none`.
>

Frozen expectations that name the same cause:

`vm/check-spec.py:1017-1179` (frozen expectation code naming `first-code`)
```
 1017  def plan_controls(plans: dict) -> list:
 1018      """(label, plan, frozen validator message) for type-correct plan mutants; a message of
 1019      None marks a plan the validator MUST admit."""
 1020      def edit(name, path, value):
 1021          plan = json.loads(json.dumps(plans[name]))
 1022          target = plan
 1023          for step in path[:-1]:
 1024              target = target[step]
 1025          target[path[-1]] = value
 1026          return plan
 1027  
 1028      def body(i):
 1029          return ['functions', i, 'body']
 1030  
 1031      def edits(name, *changes):
 1032          plan = json.loads(json.dumps(plans[name]))
 1033          for path, value in changes:
 1034              target = plan
 1035              for step in path[:-1]:
 1036                  target = target[step]
 1037              target[path[-1]] = value
 1038          return plan
 1039  
 1040      char_rows = plans['case-char']['functions'][0]['body'][5]
 1041      flag = {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]}
 1042  
 1043      def flag_rows(depth):
 1044          """A tag table over a Flag at type index 1 answering its own value."""
 1045          return [['branch', 0, depth, 0, ['value', 1, 0]], ['branch', 1, depth, 0, ['value', 1, 1]]]
 1046  
 1047      def none_parameter(scrutinee):
 1048          """pred(x: none) cases on x at `scrutinee`; main passes it a Nat."""
 1049          return edits('nat-unpack', (['functions', 0, 'parameters'], [None]), (['functions', 0, 'slots'], 1),
 1050                       ([*body(0), 3], scrutinee), ([*body(0), 5], flag_rows(1)),
 1051                       (body(1), ['call', 1, 0, [['lit', 0, 'Nat', 7]]]))
 1052  
 1053      def none_let(scrutinee):
 1054          """pred lets a none-typed call result and cases on it at `scrutinee`."""
 1055          return edits('nat-unpack', (['functions'], [
 1056              {'name': 'seven', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['lit', 0, 'Nat', 7]},
 1057              {'name': 'pred', 'parameters': [], 'result': 1, 'slots': 1,
 1058               'body': ['let', 1, 0, ['call', None, 0, []], ['case', 1, 0, scrutinee, 'tags', flag_rows(1), None]]},
 1059              {'name': 'main', 'parameters': [], 'result': 1, 'slots': 0, 'body': ['call', 1, 1, []]}]))
 1060  
 1061      def answer(tag, depth):
 1062          return ['branch', tag, depth, 0, ['value', 0, tag]]
 1063      # S's shape (catalog.bend's `case Con{+head,+tail}: match head: ...`): first_on(xs: List<Flag>)
 1064      # matches the head bound from List's pinned `none` field at Flag. The seed prints True{}.
 1065      list_head_match = {
 1066          'entry': 'book', 'representation': {'Bool': 0, 'List': 1},
 1067          'types': [plans['u32-zero']['types'][0],
 1068                    {'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []},
 1069                                                                      {'name': 'Con', 'fields': [None, 1]}]},
 1070                    flag],
 1071          'functions': [
 1072              {'name': 'first_on', 'parameters': [1], 'result': 0, 'slots': 3,
 1073               'body': ['case', 0, 0, 1, 'tags', [answer(0, 1), ['branch', 1, 1, 2, [
 1074                   'case', 0, 1, 2, 'tags', [answer(0, 3), answer(1, 3)], None]]], None]},
 1075              {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0,
 1076               'body': ['call', 0, 0, [['con', 1, 1, [['value', 2, 1], ['value', 1, 0]]]]]}]}
 1077  
 1078      def key_arms(case_type):
 1079          """pick(x: none, k: U32) -> U32 answers the `none` x from both a key Branch (k = 0) and
 1080          the Default: `U32.is_eq(pick(7,0),7)`. Each arm body fits the U32 Case."""
 1081          return {
 1082              'entry': 'book', 'representation': {'Bool': 0, 'U32': 1},
 1083              'types': [plans['u32-zero']['types'][0], {'kind': 'opaque', 'name': 'U32'}],
 1084              'functions': [
 1085                  {'name': 'U32.is_eq', 'parameters': [1, 1], 'result': 0, 'slots': 2,
 1086                   'body': ['prim', 0, 8, [['ref', 1, 0], ['ref', 1, 1]]]},
 1087                  {'name': 'pick', 'parameters': [None, 1], 'result': 1, 'slots': 2,
 1088                   'body': ['case', case_type, 1, 1, 'keys', [['branch', 0, 2, 0, ['ref', None, 0]]],
 1089                            ['default', ['ref', None, 0]]]},
 1090                  {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['call', 0, 0, [
 1091                      ['call', 1, 1, [['lit', 1, 'U32', 7], ['lit', 1, 'U32', 0]]], ['lit', 1, 'U32', 7]]]}]}
 1092  
 1093      def first_code(nil, case_type=1):
 1094          """S's literal.bend `first_code(codes: List<U32>) -> U32` (Nil: 0, Con: the head), called
 1095          as `U32.is_eq(first_code(Con{7,Nil{}}),7)`; the seed prints True{}. The Case takes its
 1096          position's type, U32, and the Con arm returns the head, pinned `none` (SPEC section 3)."""
 1097          return {
 1098              'entry': 'book', 'representation': {'Bool': 0, 'U32': 1, 'List': 2},
 1099              'types': [plans['u32-zero']['types'][0], {'kind': 'opaque', 'name': 'U32'},
 1100                        {'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []},
 1101                                                                          {'name': 'Con', 'fields': [None, 2]}]}],
 1102              'functions': [
 1103                  {'name': 'U32.is_eq', 'parameters': [1, 1], 'result': 0, 'slots': 2,
 1104                   'body': ['prim', 0, 8, [['ref', 1, 0], ['ref', 1, 1]]]},
 1105                  {'name': 'first_code', 'parameters': [2], 'result': 1, 'slots': 3,
 1106                   'body': ['case', case_type, 0, 2, 'tags', [['branch', 0, 1, 0, nil], ['branch', 1, 1, 2, ['ref', None, 1]]], None]},
 1107                  {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['call', 0, 0, [
 1108         
[truncated after 6,144 bytes; 21,816 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
