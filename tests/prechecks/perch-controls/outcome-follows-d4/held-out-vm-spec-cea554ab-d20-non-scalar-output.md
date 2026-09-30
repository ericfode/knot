<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=cea554abc93f; base=none; builder=manual-excerpt@3a2ef420dff1; sources: docs/COMPILER-CAMPAIGN.md@cea554ab sha256=40e00d3b2f87172cf12890ff2fb1561395b84165009a65be9d0c0d56c46d8b7a; docs/COMPILER-CAMPAIGN.md@cea554ab sha256=40e00d3b2f87172cf12890ff2fb1561395b84165009a65be9d0c0d56c46d8b7a; docs/COMPILER-CAMPAIGN.md@cea554ab sha256=40e00d3b2f87172cf12890ff2fb1561395b84165009a65be9d0c0d56c46d8b7a; vm/SPEC.md@cea554ab sha256=66a6a69b70833beafc31ae0e8924e7f9394ab62e39ca9aa4bb5d7a78446711b5; vm/SPEC.md@cea554ab sha256=66a6a69b70833beafc31ae0e8924e7f9394ab62e39ca9aa4bb5d7a78446711b5; vm/SPEC.md@cea554ab sha256=66a6a69b70833beafc31ae0e8924e7f9394ab62e39ca9aa4bb5d7a78446711b5; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c -->
# Claim
`vm/SPEC.md:740-744` (section 10. IO and knot-io-2)

> and handle view, and enters `k`. Outgoing Strings must be Unicode scalars and are encoded as
> canonical UTF-8, with no surrogate merging or replacement. An outgoing String that
> holds a non-scalar Char (a surrogate, or a code above U+10FFFF) halts with
> `HostFailure io abi` before the host call: none of it is encoded or written (D20,
> §11). Only output is checked: building, storing or measuring a non-scalar Char is

# Evidence
`docs/COMPILER-CAMPAIGN.md:73-73` (decision row D4)

```
   73  | D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
```

`docs/COMPILER-CAMPAIGN.md:85-85` (decision row D16)

```
   85  | D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |
```

`docs/COMPILER-CAMPAIGN.md:89-89` (decision row D20)

```
   89  | D20 | Non-scalar Chars (lone surrogates and codes above U+10FFFF) on output. The program's value decides non-scalar output, not any seed lane's behaviour. A golden is `divergent-by-contract (non-scalar output)` exactly when a String the program passes to an output effect holds a Char outside the Unicode scalar range. This is determined from the program's own semantics: the reference evaluation of its plan, or eval-cli or vm-model on the same program. The VM then follows the `knot-io` contract: it refuses that String as `HostFailure io abi` before the host call, after the earlier output, and never encodes it. Constructing a non-scalar Char is legal in the VM; only outputting one is refused. The seed lanes are observations only, and both are recorded. The Bun lane may refuse early, when the Char is constructed. The native lane prints generalized UTF-8, truncating the lead byte of a code from 2^21. Neither lane classifies. A D20 case never counts as seed agreement; a program that builds a non-scalar Char but outputs only scalars is ordinary seed agreement. | The vm-spec review found the reference lane and the IO contract in conflict. The IO contract is the one the host enforces, and a VM that encoded what the host refuses could not be conformance-tested. Review round 4 found both lanes unfit to classify: the Bun lane refuses at construction, and the native bytes are lossy from 2^21. The coordinator then made the program's value the classifier. |
```

`vm/SPEC.md:751-757` (section 11. Outcomes and the Exhausted-lane rule)

```
  751  ## 11. Outcomes and the Exhausted-lane rule
  752  
  753  Accepted, Invalid, Unsupported, Exhausted, HostFailure and InternalFailure are
  754  recorded separately. Malformed images, unknown ids and malformed invocations are
  755  HostFailure, and an image past a resource limit of §4 is Exhausted kind 2; source forms Knot does not handle are Unsupported, and so is a Book
  756  result that §8 cannot describe; a broken invariant is a defect. A timeout or
  757  crash never counts as a semantic mutant kill.
```

`vm/SPEC.md:792-822` (section 11)

```
  792  **The rule.** Wherever the seed succeeds inside the VM's declared domain and
  793  budgets, the VM MUST return the seed's value and effect trace, except the output
  794  D20 refuses (below). Another lane's
  795  exhaustion never excuses the VM. A VM that exhausts early, corrupts a result or
  796  reports an engine trap as a budget fails. Unsupported, timeout, unknown failure
  797  and a missing lane are neither Exhausted nor agreement. An Unsupported outcome is
  798  D4's refusal of a form Knot does not handle: a recorded capability gap, never a
  799  bound. Expected values are never regenerated from a candidate VM.
  800  
  801  **Non-scalar output (D20).** The program's own value decides it, never a seed
  802  lane. The reference evaluation of the plan ([evaluate.py](evaluate.py), §6–§10 on
  803  values) yields the Strings a Program passes to output effects, in order. It
  804  implements `IO.print`, the only effect the goldens use; any other foreign or a
  805  Halt fails the gate and counts as neither agreement nor D20. When one String holds
  806  a non-scalar Char, the VM writes the earlier Strings and refuses that one as
  807  `HostFailure io abi` (§10); the golden is `divergent-by-contract (non-scalar
  808  output)`, neither seed agreement nor a bound. Otherwise the case is ordinary seed
  809  agreement, whatever Chars the program builds. The seed lanes are recorded and never
  810  classify. The native lane exits 0 and writes every String as generalized UTF-8,
  811  surrogates included, but keeps only the low 8 bits of the lead byte from 2^21, so
  812  `Chr{67237376}` (0x401F600) writes `F0 9F 98 80`, the UTF-8 of U+1F600; its bytes
  813  must equal the whole trace in that encoding. The Bun lane refuses a non-scalar Char
  814  where it is constructed (`bend: N is not a Unicode scalar value`, exit 1), printed
  815  or not; its earlier output must be a prefix of the VM's, and a native-lane Program
  816  records it. D20 goldens: `print-non-scalar` (`IO.print(SCon{Chr{55296}, SNil{}})`,
  817  ASCII source; native `ED A0 80 0A`), `print-non-scalar-mid` (`"a\u{D800}b"`; native
  818  `61 ED A0 80 62 0A`, of which the VM writes nothing), `print-non-scalar-wide`
  819  (`Chr{67237376}`; native `F0 9F 98 80 0A`) and `print-non-scalar-second` (`"a"`, then
  820  the lone surrogate; the VM writes `a\n`, the Bun lane nothing). `non-scalar-code`
  821  (`55296\n`) and `non-scalar-unprinted` (`a\nnonempty\n`, where the Bun lane writes
  822  `a\n` and refuses) build a surrogate without printing it and agree with the seed.
```

`vm/check-spec.py:655-687` (frozen expectation code for a Program golden)

```
  655  def output_expectation(case, plan, evaluator=None) -> dict:
  656      """Section 11 and D20: a Program's own value classifies its output, never a seed lane.
  657  
  658      The reference evaluation of the plan yields the Strings it passes to IO.print, in order.
  659      The VM writes each as UTF-8 and refuses the first that holds a non-scalar Char as
  660      `HostFailure io abi`, before its host call. The seed lanes are recorded observations:
  661      the native lane must have written the whole trace in its generalized UTF-8 (which
  662      truncates the lead byte of a code from 2^21), and the Bun lane, which refuses a
  663      non-scalar Char where it is constructed, printed or not, a prefix of the VM's output."""
  664      ev, name, seed = evaluator or reference, case['name'], case['seed']
  665      require(seed['exit'] == 0, f'{name}: program seed must succeed')
  666      vm, native = ev.program(plan, VM_FUEL), ev.program(plan, VM_FUEL, 'native')
  667      require(native.get('exit') == 0 and native['stdout'] == written(seed),
  668              f"{name}: the plan prints {native['stdout']!r} in the seed lane's encoding; the seed wrote {written(seed)!r}")
  669      bun = case.get('seed_bun') if case.get('seed_lane') == 'native' else seed
  670      require(bun is not None, f'{name}: a native-lane Program records its Bun lane')
  671      require(vm['stdout'].startswith(bun['stdout'].encode()) and (bun['exit'] != 0 or vm.get('exit') == 0),
  672              f"{name}: the Bun lane wrote {bun['stdout']!r} (exit {bun['exit']}); the VM writes {vm['stdout']!r}")
  673      argv = ['IMAGE', str(VM_FUEL), '--']
  674      if vm.get('cause') == 'io abi':
  675          at, code = len(vm['prints']), next(c for c in vm['prints'][-1] if not ev.scalar(c))
  676          require('divergence' in case, f'{name}: print {at} holds Char {code}; D20 refuses that output, '
  677                                        f'so it is never seed agreement')
  678          require(case['divergence'] == NON_SCALAR, f"{name}: divergence {case['divergence']!r} is not D20's")
  679          require(case.get('vm_stdout', '').encode() == vm['stdout'] and 'vm_stdout' in case,
  680                  f"{name}: VM output {case.get('vm_stdout')!r} is not {vm['stdout']!r}, what the earlier prints write")
  681          return {'argv': argv, 'outcome': 'HostFailure', 'cause': 'io abi', 'stdout': case['vm_stdout'],
  682                  'basis': f'divergent-by-contract ({NON_SCALAR})',
  683                  'reason': f'D20: print {at} holds Char {code}; the native lane exits 0', 'eval_lane': classify(case['eval'])}
  684      require(vm.get('exit') == 0, f'{name}: the reference evaluation ends {vm}')
  685      require('divergence' not in case, f'{name}: a {NON_SCALAR} divergence, but every printed Char is a scalar')
  686      return {'argv': argv, 'exit': 0, 'stdout': seed['stdout'], 'stderr': '', 'basis': 'seed',
  687              'eval_lane': classify(case['eval'])}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
