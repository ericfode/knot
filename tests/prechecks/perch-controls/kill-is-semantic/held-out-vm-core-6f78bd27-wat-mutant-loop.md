<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-core; head=6f78bd2766b5; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/CORE.md@6f78bd27 sha256=88092560423c9ef49a91fabb196abaad65658c429c8c8c08af1ce947debcfdb3; vm/CORE.md@6f78bd27 sha256=88092560423c9ef49a91fabb196abaad65658c429c8c8c08af1ce947debcfdb3; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87 -->
# Claim
`vm/CORE.md:403-404`

> - **Mutants.** Thirty-five, each killed by a wrong observation in a named group
>   (one by a trap, below):

`vm/CORE.md:436-438`

>   - the pre-fix VM's trap restored at both (`top-trap`, group `trap`). Its
>     defect is the trap, so it is killed by a trap, but only when all three
>     rows at exactly 4 GiB trap and the other seven ceiling rows stay right.

# Evidence
`vm/check-core.py:208-214` (shown)

```
  208  def shown(result: dict, want: dict) -> dict:
  209      """The host-visible run, with stdout as its digest where `want` freezes one (a display
  210      run control's 16 MiB line is frozen by SHA-256)."""
  211      seen = {k: result[k] for k in ('exit', 'stdout', 'stderr')}
  212      if 'stdout_sha256' in want:
  213          seen['stdout_sha256'] = sha(seen.pop('stdout').encode())
  214      return seen
```

`vm/check-core.py:412-423` (harness, clean)

```
  412  def harness(jobs: list, timeout=600) -> dict:
  413      p = subprocess.run(['node', str(HARNESS)], input=json.dumps(jobs), capture_output=True, text=True,
  414                         timeout=timeout * SCALE)
  415      require(p.returncode == 0, f'harness failed: {p.stderr[-2000:]}')
  416      return {r['id']: r for r in map(json.loads, p.stdout.splitlines())}
  417  
  418  
  419  def clean(result: dict) -> bool:
  420      """A reported outcome, not an engine trap, host stack failure or host error."""
  421      stderr = result['stderr']
  422      return result.get('status') not in ('Trap', 'HostStack') and not any(
  423          s in stderr for s in ('HostFailure\tio\ttrap', 'HostFailure\tio\thost', 'Exhausted\tio\tcall-stack'))
```

`vm/check-core.py:1057-1059` (main: comment before the mutant jobs)

```
 1057      # mutants: a changed observation in their group, never a crash, except group `trap`, whose
 1058      # defect is a trap where section 5 gives an outcome. Runs use the test build, so a golden
 1059      # also compares the VM's own outcome registers.
```

`vm/check-core.py:1081-1082` (main: full_heap)

```
 1081      full_heap = [j for j in ceiling_mutant_jobs if j['dump']['bump'] == 1 << 32]
 1082      require(len(full_heap) == 3, f'three ceiling rows fill the heap to exactly 4 GiB: {[j["id"] for j in full_heap]}')
```

`vm/check-core.py:1089-1124` (main: the mutant loop)

```
 1089      def observed_wrong(job, out):
 1090          return shown(out, job['want']) != job['want'] or any(out['state'][k] != v for k, v in job.get('dump', {}).items())
 1091  
 1092      killed = []
 1093      for name, breaks, edits, group in MUTANTS:
 1094          text = source
 1095          for old, new in edits:
 1096              require(text.count(old) == 1, f'mutant {name}: edit applies once')
 1097              text = text.replace(old, new)
 1098          wasm = BUILD / f'mutant-{name}.wasm'
 1099          if group == 'shape':
 1100              wasm.write_bytes(build.assemble(text))
 1101              reached = module_shape(wasm)['reaches_itself']
 1102              require(reached is not None, f'mutant {name} survives the call-graph check')
 1103              killed.append({'mutant': name, 'breaks': breaks, 'group': group,
 1104                             'killed_by': [f'function {reached} reaches itself'], 'wrong_observations': 1, 'crashes': 0})
 1105              continue
 1106          wasm.write_bytes(build.assemble(build.test_source(text)))
 1107          batch = [{**{k: v for k, v in j.items() if k not in ('want', 'dump')}, 'wasm': str(wasm)} for j in groups[group]]
 1108          if group in ('ceiling', 'full-heap', 'trap'):  # about 4 GiB each: one process per run
 1109              out = {k: v for part in pool(lambda j: harness([j]), batch, workers=2) for k, v in part.items()}
 1110          else:
 1111              out = harness(batch)
 1112          crashed = [j['id'] for j in groups[group] if not clean(out[j['id']])]
 1113          if group == 'trap':  # the frozen outcome is never a trap, so a trap is the wrong observation
 1114              wrong = [j['id'] for j in full_heap if out[j['id']]['status'] == 'Trap']
 1115              right = [j['id'] for j in groups[group] if j not in full_heap
 1116                       and clean(out[j['id']]) and not observed_wrong(j, out[j['id']])]
 1117              require(len(wrong) == len(full_heap) and len(right) == len(groups[group]) - len(full_heap),
 1118                      f'mutant {name}: traps {wrong}, right {right}')
 1119          else:
 1120              wrong = [j['id'] for j in groups[group] if clean(out[j['id']]) and observed_wrong(j, out[j['id']])]
 1121          require(wrong, f'mutant {name} survives group {group} (crashes: {crashed[:5]})')
 1122          killed.append({'mutant': name, 'breaks': breaks, 'group': group, 'killed_by': wrong[:5],
 1123                         'wrong_observations': len(wrong), 'crashes': len(crashed)})
 1124      record['mutants'] = killed
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
