<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=vm-spec; head=63e63203bb2e; base=454bf3059679; builder=scripts/prechecks/packets@40e325337e4a; sources: tests/compiler-bootstrap/check.py@63e63203 sha256=c1507662a6f30eabd6e661932264ed9515effa3b27461dcec9611802d6cd76d4; tests/compiler-io/host/invoke.mjs@63e63203 sha256=94282fff5cc0d8fdf847e7ade9cc356de2a2682e8f877fd4eacd8c7afcd400ec; tests/compiler-poly/regen.py@63e63203 sha256=0a16988ec448aeae260061af6113a7eff7bdf271361780d7218b733e5e0b89a8; vm/SPEC.md@63e63203 sha256=9d65a6ae4cdd8b78181ff8846add9e6415c935f46dc2362d74aab6459815caed; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511 -->
# Claim
vm/SPEC.md:1098-1100 (section: 12. Frozen evidence and later obligations) - verbatim text:

> `check-spec.py` (gate `vm-spec`) builds both oracle heads with the seed's native
> - the bench sources, guards and recorded outputs unchanged, and `baselines.json`
>   and `parse-cli.json` equal to the digests pinned in `bench/workloads.json`; a
>   re-measurement is refused until a reviewed commit re-pins it (two controls).

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
@@ -50,36 +81,83 @@ def require(condition, detail):
 
 
+def timeout_scale() -> float:
+    value = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE') or 1)
+    require(math.isfinite(value) and value > 0, 'KNOT_GATE_TIMEOUT_SCALE must be a positive number')
+    return value
+
+
+# Wall-clock guards only catch hangs; they scale with host load (FX-08).
+SECONDS = {k: v * timeout_scale() for k, v in
+           {'parse': 60, 'compile': 600, 'host': 600, 'call': 60, 'tool': 60}.items()}
+# Children never inherit Node preload options or a C compiler override: either
+# would silently change the recorded runtime or build identity.
+ENV = {**{k: v for k, v in os.environ.items() if k not in ('NODE_OPTIONS', 'CC')}, 'BEND_NO_TELEMETRY': '1'}
+
+
 def digest(data: bytes) -> str:
     return hashlib.sha256(data).hexdigest()
 
 
+def canonical(value) -> bytes:
+    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
+
+
 def text(data: bytes) -> str:
     return data.decode('utf-8', 'backslashreplace')
 
 
-def run(argv, timeout, stdin=None):
-    """Raw bytes; a timeout is exhaustion, a signal keeps its negative exit."""
+def run(argv, timeout, cwd: Path = ROOT, env=None):
+    """Raw bytes; a timeout is exhaustion, a signal keeps its negative exit.
+    Wall time and peak RSS come from this child's own rusage."""
     argv = [str(x) for x in argv]
-    try:
-        p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, input=stdin)
-        return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
-    except subprocess.TimeoutExpired:
+    start = time.monotonic()
+    child = subprocess.Popen(argv, cwd=cwd, env=env or ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
+                             stderr=subprocess.PIPE)
+    streams = {}
+    readers = [threading.Thread(target=lambda n=n: streams.__setitem__(n, getattr(child, n).read()))
+               for n in ('stdout', 'stderr')]
+    for reader in readers:
+        reader.start()
+    lock, state = threading.Lock(), {'reaped': False, 'expired': False}
+
+    def expire():
+        with lock:
+            if not state['reaped']:
+                state['expired'] = True
+                child.kill()
+    timer = threading.Timer(timeout, expire)
+    timer.start()
+    _, status, usage = os.wait4(child.pid, 0)
+    with lock:
+        state['reaped'] = True
+    timer.cancel()
+    child.returncode = os.waitstatus_to_exitcode(status)
+    for reader in readers:
+        reader.join()
+    if state['expired']:
         return {'argv': argv, 'exit': None, 'outcome': 'Exhausted', 'budget_seconds': timeout,
                 'stdout': b'', 'stderr': b''}
+    return {'argv': argv, 'exit': child.returncode, 'stdout': streams['stdout'], 'stderr': streams['stderr'],
+            'elapsed_seconds': round(time.monotonic() - start, 3),
+            'peak_rss_bytes': usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)}
 
 
 def shown(obs) -> dict:
-    """Receipt form of an observation: text, no host paths."""
+    """Receipt form of an observation: text, no host paths, no timings."""
     row = {'argv': obs['argv'], 'exit': obs['exit'], 'stdout': text(obs['stdout']), 'stderr': text(obs['stderr'])}
-    row.update({k: obs[k] for k in ('outcome', 'budget_seconds') if k in obs})
+    row.update({k: obs[k] for k in ('outcome', 'budget_seconds', 'host', 'host_argv') if k in obs})
     return row
 
 
-def successful(argv, timeout=SECONDS['compile']):
-    obs = run(argv, timeout)
+def successful(argv, timeout=SECONDS['compile'], cwd: Path = ROOT, env=None):
+    obs = run(argv, timeout, cwd, env)
     require(obs['exit'] == 0, shown(obs))
     return obs
 
 
+def relative(path: Path, cwd: Path) -> str:
+    return os.path.relpath(path, cwd)
+
+
 # ---------------------------------------------------------------- the verdict
 

@@ -472,10 +1402,76 @@ def mutants(progress) -> list[dict]:
 # ------------------------------------------------------------------- main
 
+def seed_step(builds) -> dict:
+    """The only seed invocations in the pipeline, each inside its entry's sandbox.
+    C1 is built twice under the same name; the two binaries must be identical."""
+    def build(item):
+        label, (entry, folder, out) = item
+        out.parent.mkdir(parents=True, exist_ok=True)
+        lane = 'bun' if out.suffix == '.js' else 'native'
+        successful([relative(ROOT / SEED, folder), entry, '-o', relative(out, folder)], cwd=folder,
+                   env={**ENV, 'BEND_LIB': str(folder / LIB)})
+        return label, {'entry': entry, 'lane': lane, 'sandbox': folder.name, 'sha256': digest(out.read_bytes())}
+    with ThreadPoolExecutor(max_workers=3) as pool:
+        records = dict(pool.map(build, builds.items()))
+    repeat = records.pop('C1-repeat')
+    records['C1']['repeat_sha256'] = repeat['sha256']
+    return records
+
+
+def audit(contract, manifest, folder: Path, bundle, checker: Path | None) -> dict:
+    """C1's loader closure (--audit-bundle Module lines) against the staged
+    files (FX-21), and the D2 trust inventory of unchecked Base (FX-20)."""
+    if checker is None:
+        return {'status': 'unavailable', 'reason': 'src/CONTRACT.json advertises no --audit-bundle'}
+    argv = ['--audit-bundle', LIB, bundle['entry']]
+    obs = run([relative(checker, folder), *argv], SECONDS['compile'], cwd=folder)
+    verify(folder, bundle, manifest)
+    if obs['exit'] != 0:
+        return {'status': 'blocked', 'args': argv, 'tool': 'seed-built src/check-cli.bend', 'blocker': stopped(obs, 'knot')}
+    fields = [line.split('\t', 1) for line in text(obs['stdout']).splitlines() if '\t' in line]
+    pick = lambda key: [value for k, value in fields if k == key]
+    return {'status': 'recorded', 'args': argv, 'tool': 'seed-built src/check-cli.bend', 'modules': pick('Module'),
+            'trust': {'base_pin': pick('BasePin'), 'base_checked': pick('BaseChecked'),
+                      'base_unchecked': pick('BaseUnchecked')}}
+
+
+# A two-module entry that loads under module loading today: a local module and Base.
+PROBE = {
+    'probe/side.bend': 'import Base\n\ndef yes() -> Bool:\n  True{}\n',
+    'probe/main.bend': ('import ./side.bend as W\n\ntype Light is Type:\n  Dark{}\n  Lit{}\n\n'
+                        'def see(x: Bool) -> Light:\n  match x:\n    case False{}: Dark{}\n    case True{}: Lit{}\n\n'
+                        'def main() -> Light:\n  see(Bool.not(W.yes()))\n'),
+}
+
+
+def audit_control(contract, manifest, checker: Path | None) -> dict:
+    """The FX-21 comparator on a real audit of an entry that loads today. It
+    applies only where the compiler advertises --audit-bundle."""
+    if checker is None:
+        return {'name': 'audit-closure', 'expected': {'status': 'unavailable'}, 'observed': {'status': 'unavailable'}}
+    folder = ROOT / BUILD / 'controls' / 'audit-closure'
+    shutil.rmtree(folder, ignore_errors=True)
+    base = manifest['base']['path']
+    for name, data in ((base, (ROOT / base).read_bytes()), *((n, t.encode()) for n, t in PROBE.items())):
+        (folder / name).parent.mkdir(parents=True, exist_ok=True)
+        (folder / name).write_bytes(data)
+    (folder / LIB).mkdir()
+    bundle = {'entry': 'probe/main.bend', 'root': LIB, 'sandbox': folder.name, 'order': [base, *PROBE],
+              'files': inspect(folder), 'unresolved': []}
+    record = audit(contract, manifest, folder, bundle, checker)
+    return {'name': 'audit-closure',
+            'expected': {'status': 'recorded', 'problems': [], 'modules': list(PROBE)},
+            'observed': {'status': record['status'], 'problems': audit_problems(record, contract, bundle, manifest),
+                         'modules': record.get('modules')}}
+
+
 def main() -> int:
     parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
     parser.add_argument('--judge', metavar='RECEIPT', help='apply the gate verdict to a recorded progress receipt')
+    parser.add_argument('--contract', metavar='CONTRACT', type=Path, default=ROOT / CONTRACT,
+                        help='the src/CONTRACT.json the receipt names by hash (default: this tree\'s)')
     args = parser.parse_args()
     if args.judge:
-        violations = judge(json.loads(Path(args.judge).read_bytes()))
+        violations = judge(json.loads(Path(args.judge).read_bytes()), args.contract)
         print('\n'.join(violations) if violations else 'Judge passed')
         return 1 if violations else 0

`tests/compiler-io/host/invoke.mjs:7-8` (added)
    7  const args = JSON.parse(fs.readFileSync(argumentsPath, 'utf8')).map(a =>
    8    typeof a === 'string' ? a : Buffer.from(a.hex, 'hex'));

`tests/compiler-poly/regen.py:54-54` (added)
   54  REVIEWED_SHA256 = '85ba1897f89bcd79c35c33dcc6cff20db612ebf7cce15afe739f81b491656bbe'

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
