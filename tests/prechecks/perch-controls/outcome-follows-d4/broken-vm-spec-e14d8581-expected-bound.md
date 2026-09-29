<!-- prechecks packet v1; rule=outcome-follows-d4; increment=vm-spec; head=e14d8581dc12; base=454bf3059679; builder=scripts/prechecks/packets@3a2ef420dff1; sources: bench/run.mjs@e14d8581 sha256=f9e3bdb3769e0594bf7dcb1686010a424fb2b28902478b6ac8a9212383511c62; tests/compiler-checker/check.py@e14d8581 sha256=1ab59fa30f7208d0883cc29e4ac338c3b372a72c7f84cf04d1c4c81a40850d0b; vm/SPEC.md@e14d8581 sha256=775b305468384b9e8ec07490db7b51716e2d159635be1d9b3e3ab584923842ac; vm/check-spec.py@e14d8581 sha256=3e4e0060d26798c3804c524a113b6f5ce99991c0ba932f24902e03465c9c2db4 -->
# Claim
Outcome claims this branch changed:

vm/SPEC.md:609-621 (section: 11. Outcomes and the Exhausted-lane rule) - verbatim text:

> [golden/vm-expected.json](golden/vm-expected.json) applies the rule to every
> golden: the eval-cli line where eval agrees with the seed (70 goldens), agreement
> meaning that eval's tree equals the seed's printed value in §8's spelling (no
> spaces, erased fields dropped by the golden's declarations, a Nat unary); the seed's
> value rendered by §8 where eval is excused (`nat-big`, `u32-to-nat-big`);
> `Exhausted` kind 2 `NatRange` where the seed's value lies outside the VM's domain
> (`nat-range`, `nat-mul-range`, `nat-succ-range`) and `HostFailure invoke
> scalar-result` outside the Book-describe domain (`result-u32`), each justified in
> [golden/bounds.json](golden/bounds.json); and the seed's stdout for the Programs
> `foreign-print` and `io-bind`. For those Programs the eval lane is not excused but
> unavailable: both literals `eval-cli` and `check-cli` report
> `Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
> runs.

vm/SPEC.md:618-621 (section: 11. Outcomes and the Exhausted-lane rule) - verbatim text:

> For those Programs the eval lane is not excused but
> unavailable: both literals `eval-cli` and `check-cli` report
> `Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
> runs.

vm/SPEC.md:618-622 (section: 11. Outcomes and the Exhausted-lane rule) - verbatim text:

> For those Programs the eval lane is not excused but
> unavailable: both literals `eval-cli` and `check-cli` report
> `Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
> runs. Under D4 that should be Unsupported; it is recorded as observed, not
> relabelled, and their plans follow §1 by hand.

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

vm/SPEC.md:483-539 (section: 9. Primitives and numeric bounds (D15)):

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

vm/SPEC.md:576-624 (section: 11. Outcomes and the Exhausted-lane rule):

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
> | knot-vm-1 | Nat at most 2^32-1; call fuel; 16 MiB image; 16 MiB frames; 65,536 pages (4 GiB) of memory (D19); display bounds of §8; Book describe: algebraic trees with unary Nats only, so a U32, Char or String leaf is `HostFailure invoke scalar-result` (`result-u32`: eval-cli has no describe spelling for it either; Programs print scalars through IO) |
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
> golden: the eval-cli line where eval agrees with the seed (70 goldens), agreement
> meaning that eval's tree equals the seed's printed value in §8's spelling (no
> spaces, erased fields dropped by the golden's declarations, a Nat unary); the seed's
> value rendered by §8 where eval is excused (`nat-big`, `u32-to-nat-big`);
> `Exhausted` kind 2 `NatRange` where the seed's value lies outside the VM's domain
> (`nat-range`, `nat-mul-range`, `nat-succ-range`) and `HostFailure invoke
> scalar-result` outside the Book-describe domain (`result-u32`), each justified in
> [golden/bounds.json](golden/bounds.json); and the seed's stdout for the Programs
> `foreign-print` and `io-bind`. For those Programs the eval lane is not excused but
> unavailable: both literals `eval-cli` and `check-cli` report
> `Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
> runs. Under D4 that should be Unsupported; it is recorded as observed, not
> relabelled, and their plans follow §1 by hand. `io-bind` keeps Base's `IO.bind`
> and `IO.pure` unspecialized, so its `A`-typed nodes are `none`.
>

Frozen expectations that name the same cause:

`tests/compiler-checker/check.py:49-111` (frozen expectation code naming `check-cli`)
```
   49  def main():
   50      BUILD.mkdir(parents=True,exist_ok=True)
   51      record={'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'incomplete',
   52              'scope':'Resolved syntax and semantic checking; no evaluator or Wasm emitter',
   53              'seed_revision':'574b6d39a235b539eb19a5c532993a0abb3d11ad'}
   54      try:
   55          manifest=json.loads((HERE/'cases.json').read_text())
   56          paths=sorted((ROOT/'src').glob('*.bend'))+[ROOT/'src/SPEC.md',HERE/'cases.json',HERE/'make-manifest.py',HERE/'bounds.bend',Path(__file__)]+[ROOT/c['file'] for c in manifest['cases']]
   57          record['inputs']={str(p.relative_to(ROOT)):digest(p) for p in paths}
   58          record['tools']={t:successful([t,'--version'])['stdout'].strip() for t in ('bun','node','python3')}
   59          record['seed_inputs']={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'.toolchain/bend-2.0.29-574b6d3/bend2').glob('*.ts'))}
   60          record['proof']=successful([SEED,ROOT/'src/check-PROOF.bend'])
   61          require(record['proof']['stdout'].strip()=='All terms check.',record['proof'])
   62          js=BUILD/'check-cli.js';native=BUILD/'check-cli'
   63          record['builds']=[successful([SEED,ROOT/'src/check-cli.bend','-o',p]) for p in (js,native)]
   64          record['generated']={str(p.relative_to(ROOT)):digest(p) for p in (js,native)}
   65          lanes={'bun':['bun',js],'native':[native]}
   66          record['fixtures']=[]
   67          require({str(p.relative_to(ROOT)) for p in (HERE/'fixtures').glob('*.bend')}=={c['file'] for c in manifest['cases'] if c['file'].startswith('tests/compiler-checker/fixtures/')},'Fixture manifest mismatch')
   68          for case in manifest['cases']:
   69              ref=run([SEED,ROOT/case['file']]);observe(ref,case['reference'])
   70              item={'file':case['file'],'reference':ref,'lanes':{}}
   71              for name,command in lanes.items():
   72                  actual=run([*command,ROOT/case['file']]);observe(actual,case['knot']);item['lanes'][name]=actual
   73              record['fixtures'].append(item)
   74          record['budgets']=[]
   75          flag=next(c for c in manifest['cases'] if Path(c['file']).stem=='flag')
   76          for name,command in lanes.items():
   77              for depth in (0,1,3,4,5):
   78                  r=run([*command,ROOT/flag['file'],65536,depth])
   79                  observe(r,flag['knot'] if depth>=4 else {'exit':4,'diagnostic':'Exhausted\tcheck\tbudget\t'})
   80                  record['budgets'].append({'lane':name,'depth':depth,'result':r})
   81          record['bounds']=[]
   82          bounds_expected=('Done 256\nExhausted\tcheck\tbudget\t0:0:1:0\n'*4).strip()
   83          for suffix,command in (('.js',['bun']),('',[])):
   84              output=BUILD/('bounds'+suffix)
   85              build=successful([SEED,HERE/'bounds.bend','-o',output])
   86              r=successful([*command,output]);require(r['stdout'].strip()==bounds_expected,r)
   87              record['bounds'].append({'build':build,'observation':r,'sha256':digest(output)})
   88          record['mutants']=[]
   89          for name,file,old,new,witness in MUTANTS:
   90              directory=BUILD/name
   91              directory.mkdir(exist_ok=True)
   92              for source in (ROOT/'src').glob('*.bend'): shutil.copy2(source,directory/source.name)
   93              target=directory/file;source=target.read_text();require(source.count(old)==1,(name,'mutation must be unique'))
   94              target.write_text(source.replace(old,new))
   95              typecheck=successful([SEED,directory/'check-cli.bend','--check-only'])
   96              require(typecheck['stdout'].strip()=='All terms check.',typecheck)
   97              out=directory/'check-cli.js';build=successful([SEED,directory/'check-cli.bend','-o',out])
   98              case=next(c for c in manifest['cases'] if Path(c['file']).stem==witness)
   99              actual=run(['bun',out,ROOT/case['file']]);require(actual['exit'] in (0,2,3),actual)
  100              try: observe(actual,case['knot'])
  101              except AssertionError: killed=True
  102              else: killed=False
  103              require(killed,(name,'survived'))
  104              record['mutants'].append({'name':name,'file':file,'old':old,'new':new,'source_sha256':digest(target),'typecheck':typecheck,'build':build,'witness':case['file'],'expected':case['knot'],'actual':actual,'outcome':'semantic-kill'})
  105          record['status']='passed'
  106      except Exception as e:
  107          record['failure']=repr(e)
  108          raise
  109      finally:
  110          RECEIPT.write_text(json.dumps(record,indent=2)+'\n')
  111      print(f"Checker gate passed: {len(record['fixtures'])} reference fixtures, {2*len(record['fixtures'])} checked observations, 10 depth and 16 catalog-bound observations, {len(record['mutants'])} semantic mutants; {RECEIPT}")
```

`bench/run.mjs:11-23` (frozen expectation code naming `eval-cli`)
```
   11  const LANES = ['native', 'bun'];
   12  const command = (lane, file) => lane === 'native' ? [file] : ['bun', '--no-env-file', file];
   13  const json = object => JSON.stringify(object, null, 2) + '\n';
   14  
   15  function checkBuild(entry, executable, output) {
   16    const program = path.join(ROOT, 'tests/subsets/s1/flag.bend');
   17    if (entry === 'eval-cli') {
   18      const observed = run([...executable, program, 'flip', 65536, 0]);
   19      if (observed.stdout !== 'Evaluated\t0\t1\tOn{}') throw new Error('seed-built evaluator failed flag literal guard');
   20      return { valid: true, result: 1, observation: observed };
   21    }
   22    const wasm = `${output}.guard.wasm`, request = `${output}.guard.json`;
   23    const observed = run([...executable, program, wasm]);
```

`vm/check-spec.py:667-762` (frozen expectation code naming `foreign-print`)
```
  667  def plan_controls(plans: dict) -> list:

[truncated after 6,144 bytes; 7,479 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
