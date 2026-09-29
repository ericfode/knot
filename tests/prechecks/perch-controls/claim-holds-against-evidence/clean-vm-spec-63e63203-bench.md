<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=vm-spec; head=63e63203bb2e; base=454bf3059679; builder=scripts/prechecks/packets@47dbd98ca1c7; sources: tests/compiler-bootstrap/check.py@63e63203 sha256=c1507662a6f30eabd6e661932264ed9515effa3b27461dcec9611802d6cd76d4; tests/compiler-io/host/invoke.mjs@63e63203 sha256=94282fff5cc0d8fdf847e7ade9cc356de2a2682e8f877fd4eacd8c7afcd400ec; vm/SPEC.md@63e63203 sha256=9d65a6ae4cdd8b78181ff8846add9e6415c935f46dc2362d74aab6459815caed; vm/bench/run.py@63e63203 sha256=ed30fdd7dfa747e1509c6d26da2c47e7df66aa97a3679effd2a3f7b200c59d04; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511 -->
# Claim
vm/SPEC.md:1098-1100 (section: 12. Frozen evidence and later obligations) - verbatim text:

> `check-spec.py` (gate `vm-spec`) builds both oracle heads with the seed's native
> - the bench sources, guards and recorded outputs unchanged, and `baselines.json`
>   and `parse-cli.json` equal to the digests pinned in `bench/workloads.json`; a
>   re-measurement is refused until a reviewed commit re-pins it (two controls).

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
@@ -406,4 +1007,113 @@ def controls(names, native, bun) -> list[dict]:
             'abi': answer and answer['abi'],
             'outcome': outcome(shown(got)) if answer and answer['blocked'] else None}})
+    # A real host stack trap, and the host's memory classification on V8's messages.
+    module = folder / 'host-stack.wasm'
+    module.write_bytes(recursive_module())
+    answer, got = host(module, [{'argv': [str(MANIFEST.relative_to(ROOT))], 'inputs': [], 'outputs': []}], 'host-stack')
+    result.append({'name': 'host-stack-trap', 'expected': {'abi': 'knot-bytes-0', 'resource': 'host-stack'},
+                   'observed': {'abi': answer and answer['abi'],
+                                'resource': exhaustion(shown(got[0])) if answer and not answer['blocked'] else None}})
+    probe = ("import { trap } from './" + HOST + "';"
+             "const see = m => { const r = trap(new RangeError(m)); return { exit: r.exit, host: r.host,"
+             " stderr: Buffer.from(r.stderr, 'base64').toString() }; };"
+             "console.log(JSON.stringify([see('WebAssembly.Instance(): Out of memory: Cannot allocate Wasm memory"
+             " for new instance'), see('WebAssembly.Memory(): could not allocate memory'),"
+             " see('Maximum call stack size exceeded'), see('offset is out of bounds')]));")
+    r = run(['node', '--input-type=module', '-e', probe], SECONDS['tool'])
+    try:
+        seen = [exhaustion(row) or outcome(row) for row in json.loads(r['stdout'])]
+    except ValueError:
+        seen = shown(r)
+    result.append({'name': 'host-trap-classification',
+                   'expected': {'resources': ['host-memory', 'host-memory', 'host-stack', 'HostFailure']},
+                   'observed': {'resources': seen}})
+    return result
+
+
+def sandbox_controls(bundle, manifest, argv) -> list[dict]:
+    """Live refusals: damaged copies of S's sandbox must fail verification before any step."""
+    source = ROOT / BUILD / bundle['sandbox']
+    entry = bundle['entry']
+    package = next((p for p in bundle['order'] if p.startswith(f'{LIB}/')), manifest['base']['path'])
+
+    def symlink(folder):
+        twin = folder.parent / f'{folder.name}-twin.bend'
+        twin.write_bytes((folder / entry).read_bytes())
+        (folder / entry).unlink()
+        (folder / entry).symlink_to(twin)
+
+    def hardlink(folder):
+        os.link(folder / entry, folder.parent / f'{folder.name}-twin.bend')
+
+    def tamper(folder):
+        with (folder / package).open('ab') as f:
+            f.write(b'\n')
+
+    def extra(folder):
+        (folder / LIB / 'extra.bend').write_bytes(b'')
+
+    # Staging itself refuses a package whose bytes differ from its pin: the run
+    # stops there, before any seed invocation.
+    library = ROOT / BUILD / 'controls' / 'tampered-lib'
+    shutil.rmtree(library, ignore_errors=True)
+    for name in manifest['packages']:
+        (library / name).parent.mkdir(parents=True, exist_ok=True)
+        (library / name).write_bytes((library_path() / name).read_bytes() + b'\n')
+    try:
+        stage_sandbox(entry, ROOT / BUILD / 'controls' / 'staging-pin-refused', manifest, library)
+        seen = {'refused': False}
+    except AssertionError as error:
+        seen = {'refused': True, 'reason': 'differs from its pin' if 'differs from its pin' in str(error) else str(error)}
+    result = [{'name': 'staging-pin-refused', 'expected': {'refused': True, 'reason': 'differs from its pin'},
+               'observed': seen}]
+    for label, damage, reason in (
+            ('sandbox-symlink-refused', symlink, 'not a regular single-link file'),
+            ('sandbox-hardlink-refused', hardlink, 'not a regular single-link file'),
+            ('sandbox-pin-refused', tamper, 'differs from its pin'),
+            ('sandbox-extra-file-refused', extra, 'differs from its staged record')):
+        folder = ROOT / BUILD / 'controls' / label
+        for leftover in folder.parent.glob(f'{label}-twin.bend'):
+            leftover.unlink()
+        replica(source, folder, bundle)
+        damage(folder)
+        try:
+            verify(folder, bundle, manifest)
+            seen = {'refused': False}
+        except AssertionError as error:
+            seen = {'refused': True, 'reason': reason if reason in str(error) else str(error)}
+        result.append({'name': label, 'expected': {'refused': True, 'reason': reason}, 'observed': seen})
+    result.append({'name': 'argv-reserved-refused', 'expected': {'reserved': ['--threads']},
+                   'observed': {'reserved': reserved_in([*argv, '--threads', '2'], manifest)}})
+    # Live routing of A2's result on the S that C1 built: a host timeout, a host
+    # stack trap, a Knot rejection, success, a Knot budget, the VM's fuel and
+    # heap budgets (D16, D19), and a harness that cannot run A2 yet.
+    answered = {'abi': 'knot-io', 'blocked': None}
+    pending = {'abi': 'knot-io', 'blocked': {'source': 'harness', 'exit': 3, 'stdout': '',
+                                             'stderr': 'Unsupported\thost\tio-abi-pending\n'}}
+    record = lambda exit, stderr, **more: {'argv': argv, 'exit': exit, 'stdout': b'', 'stderr': stderr, **more}
+    routed = [a3_stopped(a, o, argv) for a, o in (
+        (None, record(None, b'', outcome='Exhausted', budget_seconds=1, source='harness')),
+        (answered, record(4, b'Exhausted\twasm\tcall-stack\n', host=True, files={})),
+        (answered, record(3, b'Unsupported\tlex\tliteral\t0:1:1:1\n', host=False, files={})),
+        (answered, record(0, b'', host=False, files={})),
+        (answered, record(4, b'Exhausted\tparse\tbudget\t12:13:3:4\n', host=False, files={})),
+        (answered, record(4, b'Exhausted\tio\tsteps\n', host=False, files={})),
+        (answered, record(4, b'Exhausted\tio\tmemory\n', host=False, files={})),
+        (pending, record(3, b'Unsupported\thost\tio-abi-pending\n', source='harness')))]
+    result.append({'name': 'a3-routing', 'expected': {
+        'statuses': ['divergent-exhausted', 'divergent-exhausted', 'divergent-unsupported', 'reached',
+                     'divergent-exhausted', 'blocked', 'blocked', 'blocked'],
+        'excuses': [None, None, None, None, None, 'vm-fuel', 'vm-heap', 'harness-io-abi-pending']},
+        'observed': {'statuses': [r['status'] if r else 'reached' for r in routed],
+                     'excuses': [r.get('excuse') if r else None for r in routed]}})
+    # Live: a host that refuses its module before the guest runs still records the
+    # argv the guest was handed, which the judge checks, and the node command apart.
+    module = ROOT / BUILD / 'controls' / 'host-refused.wasm'
+    module.write_bytes(MAGIC + b'\xff')
+    handed = invocation('e2e3.a3', argv)
+    _, got = host(module, [{'argv': handed, 'inputs': [], 'outputs': [OUTPUT]}], 'host-refused')
+    row = shown(got)
+    result.append({'name': 'host-refused-argv', 'expected': {'argv': handed, 'executor': 'node'},
+                   'observed': {'argv': row['argv'], 'executor': (row.get('host_argv') or [None])[0]}})
     return result
 

`tests/compiler-io/host/invoke.mjs:7-8` (added)
    7  const args = JSON.parse(fs.readFileSync(argumentsPath, 'utf8')).map(a =>
    8    typeof a === 'string' ? a : Buffer.from(a.hex, 'hex'));

`vm/bench/run.py:175-187` (added)
  175  def main():
  176      parser = argparse.ArgumentParser()
  177      parser.add_argument('--repeat', type=int, default=5)
  178      parser.add_argument('--only', choices=('workloads', 'parse-cli'))
  179      args = parser.parse_args()
  180      stamp = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': host(),
  181               'seed': '2.0.29 574b6d3 (native lane, clang)'}
  182      if args.only != 'parse-cli':
  183          rows = workloads(args.repeat)
  184          (HERE / 'baselines.json').write_text(json.dumps({**stamp, 'workloads': rows}, indent=1) + '\n')
  185      if args.only != 'workloads':
  186          result = parse_cli(max(1, args.repeat // 2 + 1))
  187          (HERE / 'parse-cli.json').write_text(json.dumps({**stamp, **result}, indent=1) + '\n')

`vm/check-spec.py:152-162` (added)
  152  def lanes(case, built):
  153      got = {'seed': observed(seed_observation(case)),
  154             'eval': observed(run(eval_argv(case, built), 120))}
  155      if 'seed_bun_stderr' in case:
  156          # The seed's Bun lane, recorded beside a native observation; it never classifies.
  157          got['seed_bun'] = observed(run([SEED, case['source']], 120))
  158      if 'invocations' in case:
  159          # The seed runs only `main`; eval-cli is the oracle for every other invocation.
  160          got['invocations'] = [{**reviewed(i), 'eval': observed(run(invoke_argv(case, built, i), 120))}
  161                                for i in case['invocations']]
  162      return got

`vm/check-spec.py:2402-2432` (added)
 2402  def check_bench(built: dict, read=committed) -> dict:
 2403      """The speed freeze: sources and seed-native measurements unchanged, the measurements
 2404      recorded against those exact sources."""
 2405      manifest = json.loads(read('vm/bench/workloads.json'))
 2406      for path, digest in manifest['measurements']['sha256'].items():
 2407          require(sha(read(path)) == digest, f'bench measurement {path} differs from its pin')
 2408      baselines = json.loads(read('vm/bench/baselines.json'))
 2409      require([w['name'] for w in manifest['workloads']] == list(baselines['workloads']), 'bench workload set')
 2410      for w in manifest['workloads']:
 2411          require(sha(read(w['source'])) == w['sha256'], f"bench source {w['name']}")
 2412          row = baselines['workloads'][w['name']]
 2413          require(row['source_sha256'] == w['sha256'], f"bench baseline source {w['name']}")
 2414          require(row['stdout'] == w['expected_stdout'] == 'True{}\n' and row['exit'] == 0, f"bench output {w['name']}")
 2415          require(len(row['samples']) == row['repeat'] >= 3 and row['summary']['instructions']['median'] > 0,
 2416                  f"bench samples {w['name']}")
 2417      parse = json.loads(read('vm/bench/parse-cli.json'))
 2418      snapshot = built['literals']['files']
 2419      library = Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))).expanduser()
 2420      for f in parse['files']:
 2421          if f['origin'] == 'literals-snapshot':
 2422              data = snapshot[f['path']].encode()
 2423          elif f['origin'] == 'base':
 2424              data = (ROOT / f['path']).read_bytes()
 2425          else:
 2426              local = f"tests/compiler-modules/bundle/lib/{f['path']}"
 2427              data = (library / f['path']).read_bytes() if (library / f['path']).exists() else snapshot[local].encode()
 2428          require(sha(data) == f['sha256'], f"parse-cli corpus {f['path']}")
 2429          require(f['summary']['instructions']['median'] > 0, f"parse-cli count {f['path']}")
 2430      require(parse['commit'] == built['literals']['commit'], 'parse-cli subject commit')
 2431      return {'workloads': len(manifest['workloads']), 'parse_cli_files': len(parse['files']),
 2432              'measurements': manifest['measurements']['sha256']}

`vm/check-spec.py:2435-2450` (added)
 2435  def bench_controls(built: dict) -> list:
 2436      """A re-measurement must not pass as the frozen baseline."""
 2437      out = []
 2438      for path, field in [('vm/bench/baselines.json', 'workloads'), ('vm/bench/parse-cli.json', 'files')]:
 2439          data = json.loads(committed(path))
 2440          rows = data[field]
 2441          row = rows[next(iter(rows))] if isinstance(rows, dict) else rows[0]
 2442          row['summary']['instructions']['median'] += 1
 2443          remeasured = (json.dumps(data, indent=1) + '\n').encode()
 2444          try:
 2445              check_bench(built, lambda p: remeasured if p == path else committed(p))
 2446          except AssertionError as refusal:
 2447              out.append({'control': f'bench:remeasured-{Path(path).stem}', 'refused': str(refusal)})
 2448              continue
 2449          raise AssertionError(f'bench control {path} was admitted')
 2450      return out
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
