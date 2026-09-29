<!-- prechecks packet v1; rule=expectation-independent; increment=vm-core; head=b2aab0f5fb10; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/CORE.md@b2aab0f5 sha256=0bd9a7d443f0dabac61e31216fd5d19d1189776f8c3072a06fef75e17aec4f27; vm/CORE.md@b2aab0f5 sha256=0bd9a7d443f0dabac61e31216fd5d19d1189776f8c3072a06fef75e17aec4f27; vm/check-core.py@b2aab0f5 sha256=1733f864d7665445439ebd280d07a74471d4f2c4a84bde2d691e4ce77991e518; vm/check-core.py@b2aab0f5 sha256=1733f864d7665445439ebd280d07a74471d4f2c4a84bde2d691e4ce77991e518 -->
# Claim
`vm/CORE.md:55-61` (refusal codes)

> loader decodes in `serializer.decode`'s order. The validator follows the order
> of `serializer.validate`'s recursion and stops at the first defect, and the
> canonical check comes last. A refusal therefore names the reference codec's
> first defect. The gate requires this on:
> - the 61 frozen controls, counted against SPEC §4's own figure;
> - 3,640 seeded single mutations of the goldens: 3,336 refused, and 304 admitted
>   and run to a clean outcome.

`vm/CORE.md:241-244` (mutants)

> - **Mutants.** Eighteen, each killed by a wrong observation in a named group:
>   - arm selection, slot off-by-one, Nat bound and x % 0 (goldens);
>   - fuel (fuel boundaries);
>   - validator offset (goldens and controls);

# Evidence
`vm/check-core.py:610-623` (malformed controls: reference and VM runs)

```
  610      rows = []
  611      for i, (label, data, _, _) in enumerate(controls):
  612          (malformed / f'c{i}.kimg').write_bytes(data)
  613          rows.append({'label': label, 'sha256': sha(data), 'reference': spec.rejected(data, reg, digest),
  614                       'argv': argv_for(f'c{i}.kimg', data)})
  615      got = pool(lambda r: host(module, malformed, r['argv']), rows)
  616      dumped = traced(rows, malformed)
  617      refused = []
  618      for r, g in zip(rows, got):
  619          code = expected_reason(r['reference'])
  620          g.update(state=dumped[r['label']]['state'], booted=dumped[r['label']]['booted'])
  621          require(clean(g), f"control {r['label']}: {g}")
  622          require(observed_reason(g) == code, f"control {r['label']}: VM {g['stderr']!r}, reference {r['reference']!r}")
  623          refused.append({'control': r['label'], 'reference': r['reference'], 'vm': code, 'exit': g['exit']})
```

`vm/check-core.py:702-730` (mutant jobs and their wants)

```
  702      # mutants: a changed observation in their group, never a crash. Runs use the test
  703      # build, so a golden also compares the VM's own outcome registers.
  704      source = (HERE / 'vm.wat').read_text()
  705      goldens_jobs = [{'id': f'golden:{n}', 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')}, 'argv': golden_argv(n),
  706                       'want': expected_run(expected['cases'][n]), 'dump': expected_dump(expected['cases'][n])}
  707                      for n in names]
  708      fixture_jobs = [{'id': f"fixture:{r['name']}", 'files': {staged(r['image']): str(sandbox / staged(r['image']))} if r['image'] else {},
  709                       'argv': [staged(r['image']), *r['argv']], 'want': r['expect']} for r in runs]
  710      control_jobs = [{'id': f"control:{r['label']}", 'files': {r['argv'][0]: str(malformed / r['argv'][0])},
  711                       'argv': r['argv'], 'want': {'exit': g['exit'], 'stdout': g['stdout'], 'stderr': g['stderr']}}
  712                      for r, g in zip(rows, got)]
  713      admitted_jobs = [{'id': f"admitted:{r['label']}", 'files': {r['argv'][0]: str(loaded / r['argv'][0])},
  714                        'argv': r['argv'], 'want': frozen[r['label']]['expect']} for r in welcome]
  715      invocation_jobs = [{'id': f'invocation:{label}', 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')},
  716                          'argv': invocation_argv[label], 'want': expected_run(row), 'dump': expected_dump(row)}
  717                         for label, n, row in invoked]
  718      run_jobs = [{'id': r['label'], 'files': {r['argv'][0]: str(loaded / r['argv'][0])}, 'argv': r['argv'],
  719                   'want': r['want'], 'dump': r['dump']} for r in run_rows]
  720      ceiling_mutant_jobs = [{**j, 'id': f"ceiling:{r['name']}", 'want': r['expect'], 'dump': r['dump']}
  721                             for j, r in zip(ceiling_jobs, ceiling)]
  722      groups = {'goldens': goldens_jobs, 'fixtures': fixture_jobs, 'controls': goldens_jobs + control_jobs + admitted_jobs,
  723                'fuel': [j for j in fixture_jobs if 'fuel' in j['id']],
  724                'quantum': [j for j in fixture_jobs if 'quantum' in j['id']], 'ceiling': ceiling_mutant_jobs,
  725                'invocations': invocation_jobs, 'runs': run_jobs}
  726  
  727      def observed_wrong(job, out):
  728          shown = {k: out[k] for k in ('exit', 'stdout', 'stderr')} != job['want']
  729          return shown or any(out['state'][k] != v for k, v in job.get('dump', {}).items())
  730  
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
