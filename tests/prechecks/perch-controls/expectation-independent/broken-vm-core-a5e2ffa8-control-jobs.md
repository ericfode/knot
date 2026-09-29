<!-- prechecks packet v1; rule=expectation-independent; increment=vm-core; head=a5e2ffa89c4b; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/CORE.md@a5e2ffa8 sha256=ca15177a892cecce5da7239d882bc884a67a87d01a6cc40d723f93461657c280; vm/CORE.md@a5e2ffa8 sha256=ca15177a892cecce5da7239d882bc884a67a87d01a6cc40d723f93461657c280; vm/check-core.py@a5e2ffa8 sha256=f37f03b1005507ca15600c855472fdc948a6ec6ed5f23d7a966139e1a5755b36; vm/check-core.py@a5e2ffa8 sha256=f37f03b1005507ca15600c855472fdc948a6ec6ed5f23d7a966139e1a5755b36 -->
# Claim
`vm/CORE.md:55-61` (refusal codes)

> loader decodes in `serializer.decode`'s order. The validator follows the order
> of `serializer.validate`'s recursion and stops at the first defect, and the
> canonical check comes last. A refusal therefore names the reference codec's
> first defect. The gate requires this on:
> - the 61 frozen controls, counted against SPEC §4's own figure;
> - 3,440 seeded single mutations of the goldens: 3,143 refused, and 297 admitted
>   and run to a clean outcome.

`vm/CORE.md:199-202` (mutants)

> - **Mutants.** Twelve, each killed by a wrong observation in a named group:
>   - arm selection, slot off-by-one, Nat bound and x % 0 (goldens);
>   - fuel (fuel boundaries);
>   - validator offset (goldens and controls);

# Evidence
`vm/check-core.py:543-556` (malformed controls: reference and VM runs)

```
  543      rows = []
  544      for i, (label, data, _, _) in enumerate(controls):
  545          (malformed / f'c{i}.kimg').write_bytes(data)
  546          rows.append({'label': label, 'sha256': sha(data), 'reference': spec.rejected(data, reg, digest),
  547                       'argv': argv_for(f'c{i}.kimg', data)})
  548      got = pool(lambda r: host(module, malformed, r['argv']), rows)
  549      dumped = traced(rows, malformed)
  550      refused = []
  551      for r, g in zip(rows, got):
  552          code = expected_reason(r['reference'])
  553          g.update(state=dumped[r['label']]['state'], booted=dumped[r['label']]['booted'])
  554          require(clean(g), f"control {r['label']}: {g}")
  555          require(observed_reason(g) == code, f"control {r['label']}: VM {g['stderr']!r}, reference {r['reference']!r}")
  556          refused.append({'control': r['label'], 'reference': r['reference'], 'vm': code, 'exit': g['exit']})
```

`vm/check-core.py:605-623` (mutant jobs and their wants)

```
  605      # mutants: a changed observation in their group, never a crash. Runs use the test
  606      # build, so a golden also compares the VM's own outcome registers.
  607      source = (HERE / 'vm.wat').read_text()
  608      goldens_jobs = [{'id': f'golden:{n}', 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')}, 'argv': golden_argv(n),
  609                       'want': expected_run(expected['cases'][n]), 'dump': expected_dump(expected['cases'][n])}
  610                      for n in names]
  611      fixture_jobs = [{'id': f"fixture:{r['name']}", 'files': {staged(r['image']): str(sandbox / staged(r['image']))} if r['image'] else {},
  612                       'argv': [staged(r['image']), *r['argv']], 'want': r['expect']} for r in runs]
  613      control_jobs = [{'id': f"control:{r['label']}", 'files': {r['argv'][0]: str(malformed / r['argv'][0])},
  614                       'argv': r['argv'], 'want': {'exit': g['exit'], 'stdout': g['stdout'], 'stderr': g['stderr']}}
  615                      for r, g in zip(rows, got)]
  616      admitted_jobs = [{'id': f"admitted:{r['label']}", 'files': {r['argv'][0]: str(loaded / r['argv'][0])},
  617                        'argv': r['argv'], 'want': frozen[r['label']]['expect']} for r in welcome]
  618      groups = {'goldens': goldens_jobs, 'fixtures': fixture_jobs, 'controls': goldens_jobs + control_jobs + admitted_jobs,
  619                'fuel': [j for j in fixture_jobs if 'fuel' in j['id']],
  620                'quantum': [j for j in fixture_jobs if 'quantum' in j['id']]}
  621  
  622      def observed_wrong(job, out):
  623          shown = {k: out[k] for k in ('exit', 'stdout', 'stderr')} != job['want']
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
