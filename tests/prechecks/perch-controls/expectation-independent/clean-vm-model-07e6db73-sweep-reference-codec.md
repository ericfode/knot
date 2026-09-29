<!-- prechecks packet v1; rule=expectation-independent; increment=vm-model; head=07e6db733079; base=none; builder=manual-excerpt@3a2ef420dff1; sources: docs/compiler-campaign/GATES.md@07e6db73 sha256=55e1d241cc08a8dea28551716ba3a94cc56a11c5287d16dc9e22dc31258aa2bb; vm/check-model.py@07e6db73 sha256=1f45bd478b9a9afe0320d678d1d1a2d2c9356dce5df46f722ecd6d0bca94eae8; vm/check-model.py@07e6db73 sha256=1f45bd478b9a9afe0320d678d1d1a2d2c9356dce5df46f722ecd6d0bca94eae8 -->
# Claim
`docs/compiler-campaign/GATES.md:101-103` (vm-model gate: soundness sweep)

> with the reference evaluation's call count; the bounded soundness sweep, every
> single-word mutation of every golden refused exactly when the reference codec
> refuses it, for the same reason, and otherwise run soundly; `vm/PROOF.bend`

# Evidence
`vm/check-model.py:87-98` (check-spec's reference codec and evaluator)

```
   87  def load_check_spec():
   88      spec = importlib.util.spec_from_file_location('check_spec', HERE / 'check-spec.py')
   89      module = importlib.util.module_from_spec(spec)
   90      spec.loader.exec_module(module)
   91      return module
   92  
   93  
   94  cs = load_check_spec()
   95  codec = cs.codec
   96  reference = cs.reference  # vm/evaluate.py
   97  REGISTRY = codec.registry()
   98  DIGEST = codec.base_digest(REGISTRY)
```

`vm/check-model.py:767-816` (reference_verdicts and sweep_runs)

```
  767  def reference_verdicts(name: str) -> list:
  768      data = (GOLDEN / f'{name}.kimg').read_bytes()
  769      w = words(data)
  770      require(all(t['kind'] != 'data' or t['constructors'] for t in codec.decode(data, DIGEST)['types']),
  771              f'{name}: a zero-constructor type would make the reference allocate 2^32 entries')
  772      out = []
  773      for i in range(len(w)):
  774          for k, value in enumerate((0, (w[i] + 1) & codec.NONE, (w[i] - 1) & codec.NONE)):
  775              m = list(w)
  776              m[i] = value
  777              out.append(cs.rejected(b''.join(x.to_bytes(4, 'little') for x in m), REGISTRY, DIGEST))
  778      return out
  779  
  780  
  781  def sweep_runs(sweep: Path, swept) -> dict:
  782      """Validator soundness on bounded images: every single-word mutation (zero,
  783      successor, predecessor) of each swept golden, against the reference codec.
  784      The reference materializes a data type's constructor count before checking
  785      it, so a swept image must have no zero-constructor type, whose predecessor
  786      would be a 2^32-entry list."""
  787      reference = {name: reference_verdicts(name) for name in swept}
  788      with ThreadPoolExecutor(max_workers=8) as pool:
  789          got = dict(zip(swept, pool.map(lambda n: run([sweep, '--', GOLDEN / f'{n}.kimg', SWEEP_FUEL], 600), swept)))
  790      out = {}
  791      for name in swept:
  792          result, want = got[name], reference[name]
  793          lines = result['stdout'].strip().split('\n') if result['stdout'].strip() else []
  794          stats = {'mutations': len(want), 'admitted': 0, 'refused': 0, 'unsound': 0, 'differ': 0}
  795          examples = []
  796          good = result['exit'] == 0 and len(lines) == len(want)
  797          for j, line in enumerate(lines[:len(want)]):
  798              f = line.split('\t')
  799              require(f[:2] == [str(j // 3), str(j % 3)], f'{name}: sweep line {j} out of order')
  800              if f[-1] != 'sound':
  801                  stats['unsound'] += 1
  802                  examples.append(line)
  803              if f[2] == 'refused':
  804                  stats['refused'] += 1
  805                  refusal = model_refusal({'exit': 5 if f[3] == 'HostFailure' else 4, 'stderr': '\t'.join(f[3:-1])})
  806                  same = refusal == want[j]
  807              else:
  808                  stats['admitted'] += 1
  809                  same = want[j] is None
  810              if not same:
  811                  stats['differ'] += 1
  812                  examples.append(f'{line} | reference {want[j]!r}')
  813          good = good and stats['unsound'] == 0 and stats['differ'] == 0
  814          out[name] = {'result': {'exit': result['exit'], 'stderr': result['stderr'][-400:]}, 'agrees': good,
  815                       'stats': stats, 'examples': examples[:5]}
  816      return out
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
