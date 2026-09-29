<!-- prechecks packet v1; rule=expectation-independent; increment=vm-core; head=6f78bd2766b5; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/CORE.md@6f78bd27 sha256=88092560423c9ef49a91fabb196abaad65658c429c8c8c08af1ce947debcfdb3; vm/SPEC.md@6f78bd27 sha256=f52eca73e1ba4882f5180bc729ade834c5ff29a230b1843746d4821fc244b5df; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87; vm/check-core.py@6f78bd27 sha256=d28a69fa0c6c6ecf6984413aafd3818c82a5e04da5557f666226dbf749c55d87 -->
# Claim
`vm/SPEC.md:766-766` (section 11, The rule)

> bound. Expected values are never regenerated from a candidate VM.

`vm/CORE.md:57-59`

> canonical check comes last. A refusal therefore names the reference codec's
> first defect. The gate requires this on:
> - the 62 frozen controls, counted against SPEC §4's own figure;

# Evidence
`vm/check-core.py:167-179` (observed_reason)

```
  167  def observed_reason(result: dict) -> str | None:
  168      """The VM's refusal of the image, from its stderr line or, for image size, its
  169      exhaustion. A traced run that got past vm_boot failed at run time (an `ill-typed`
  170      word, SPEC section 6), which is no refusal of the image."""
  171      require(result.get('booted') is not None, 'a refusal is read from a traced run')
  172      if result['booted']:
  173          return None
  174      line = result['stderr'].strip()
  175      if line.startswith('HostFailure\timage\t'):
  176          return line.split('\t')[2]
  177      if line == 'Exhausted\tio\tmemory' and result.get('state', {}) and result['state']['cause'] == 'image-size':
  178          return 'image-size'
  179      return None
```

`vm/check-core.py:406-409` (host)

```
  406  def host(module: Path, sandbox: Path, argv: list, node_flags=()) -> dict:
  407      p = subprocess.run(['node', *node_flags, str(HOST), str(module), str(sandbox), '--', *argv],
  408                         capture_output=True, timeout=120 * SCALE)
  409      return {'exit': p.returncode, 'stdout': p.stdout.decode(), 'stderr': p.stderr.decode()}
```

`vm/check-core.py:588-591` (a mutant of group controls)

```
  588      ('validator-offset', 'name bytes are read one word early',
  589       [('(local.set $p (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $at) (i32.const 2)) (i32.const 2))))',
  590         '(local.set $p (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $at) (i32.const 1)) (i32.const 2))))')],
  591       'controls'),
```

`vm/check-core.py:752-752` (main)

```
  752      module, test = HERE / 'vm.wasm', BUILD / 'vm-test.wasm'
```

`vm/check-core.py:928-945` (main: the frozen refusal controls through the host)

```
  928      def traced(rows, where, timeout=600):
  929          return harness([{'id': r['label'], 'wasm': str(test), 'files': {r['argv'][0]: str(where / r['argv'][0])},
  930                           'argv': r['argv'], 'trace': 'yields'} for r in rows], timeout)
  931  
  932      rows = []
  933      for i, (label, data, _, _) in enumerate(controls):
  934          (malformed / f'c{i}.kimg').write_bytes(data)
  935          rows.append({'label': label, 'sha256': sha(data), 'reference': spec.rejected(data, reg, digest),
  936                       'argv': argv_for(f'c{i}.kimg', data)})
  937      got = pool(lambda r: host(module, malformed, r['argv']), rows)
  938      dumped = traced(rows, malformed)
  939      refused = []
  940      for r, g in zip(rows, got):
  941          code = expected_reason(r['reference'])
  942          g.update(state=dumped[r['label']]['state'], booted=dumped[r['label']]['booted'])
  943          require(clean(g), f"control {r['label']}: {g}")
  944          require(observed_reason(g) == code, f"control {r['label']}: VM {g['stderr']!r}, reference {r['reference']!r}")
  945          refused.append({'control': r['label'], 'reference': r['reference'], 'vm': code, 'exit': g['exit']})
```

`vm/check-core.py:1057-1060` (main: the mutants are edits of vm.wat)

```
 1057      # mutants: a changed observation in their group, never a crash, except group `trap`, whose
 1058      # defect is a trap where section 5 gives an outcome. Runs use the test build, so a golden
 1059      # also compares the VM's own outcome registers.
 1060      source = (HERE / 'vm.wat').read_text()
```

`vm/check-core.py:1066-1068` (main: control_jobs)

```
 1066      control_jobs = [{'id': f"control:{r['label']}", 'files': {r['argv'][0]: str(malformed / r['argv'][0])},
 1067                       'argv': r['argv'], 'want': {'exit': g['exit'], 'stdout': g['stdout'], 'stderr': g['stderr']}}
 1068                      for r, g in zip(rows, got)]
```

`vm/check-core.py:1083-1083` (main: groups)

```
 1083      groups = {'goldens': goldens_jobs, 'fixtures': fixture_jobs, 'controls': goldens_jobs + control_jobs + admitted_jobs,
```

`vm/check-core.py:1089-1090` (main)

```
 1089      def observed_wrong(job, out):
 1090          return shown(out, job['want']) != job['want'] or any(out['state'][k] != v for k, v in job.get('dump', {}).items())
```

`vm/check-core.py:1119-1121` (main: the mutant kill)

```
 1119          else:
 1120              wrong = [j['id'] for j in groups[group] if clean(out[j['id']]) and observed_wrong(j, out[j['id']])]
 1121          require(wrong, f'mutant {name} survives group {group} (crashes: {crashed[:5]})')
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
