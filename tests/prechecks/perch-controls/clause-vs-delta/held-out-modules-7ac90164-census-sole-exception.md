<!-- prechecks packet v1; rule=clause-vs-delta; increment=modules; head=7ac90164a0f1; base=c0bd08d03942; builder=scripts/prechecks/packets@3a2ef420dff1; sources: scripts/gates/run.py@7ac90164 sha256=42c29e0953a244edf39f8e33e0273ee8cfc7a8020ff5f2d3d4c4c4424ec14d5e; src/host/path-identity.js@7ac90164 sha256=6150ae6b016d20f2e380b6f50110e654509d5b1b822bce78c03b4c5c640d7ee2; tests/compiler-modules/check.py@7ac90164 sha256=b4594d98ff225854621e6012133c398f56c91cb3e03c1b3f3d27f6169b238aeb; tools/census/SPEC.md@7ac90164 sha256=bd9efbfb2bb8bc15dd7857cfaae62b55c0e74e82aa81f55dce6b15152e2dcd41; tools/census/census.mjs@7ac90164 sha256=df158a987364e93c7f68acb8f4d09219360478601a8c3473493b4df277c1b751; tools/census/tests/host-boundary.test.mjs@7ac90164 sha256=bdf65f8970109eda66f7d535680c64ffd14048321a3a1f4f987da81c5b60969c -->
# Claim
Invariance clause (tools/census/SPEC.md):

> A reviewed `dependency_feature_exceptions` entry may exempt named features of one exact file SHA-256. The modules path-identity wrapper has the sole `foreign` exception; other files, changed bytes, and other forbidden features retain rejection.

# Evidence
Evidence: the governed diff hunks (base to head).
```
@@ -278,4 +288,18 @@ def counts(root: Path, gate: Gate, stdout: str) -> dict:
             wasm = json.loads((root / f'research/flat-store/receipts/{lane}-wasm.json').read_bytes())
             result[lane] = {k: wasm[k] for k in ('observations', 'instances', 'installed_boundary_states', 'lifecycle_checks')}
+    if gate.name == 'modules':
+        fixtures = record['fixtures']
+        lanes = [lane for fixture in fixtures for lane in fixture['lanes'].values()]
+        result.update(reference_calls=sum(len(fixture['reference']) for fixture in fixtures),
+                      execution_lanes=len(fixtures[0]['lanes']),
+                      check_observations=len(lanes), compile_observations=len(lanes),
+                      eval_observations=sum(len(lane['evaluations']) for lane in lanes),
+                      wasm_observations=sum(len(lane['wasm']) for lane in lanes),
+                      artifact_preservation_probes=sum(lane['artifact_preserved'] for lane in lanes),
+                      byte_identity_pairs=sum(fixture.get('byte_identical', False) for fixture in fixtures),
+                      trust_audits=sum('audit' in lane for lane in lanes),
+                      pin_observations=len(record['pin']),
+                      tampered_base_observations=len(record['tampered_base']),
+                      proof_entries=len(record['proofs']))
     if gate.name == 'io-host':
         for key in ('seed_fixtures', 'seed_runs', 'conformance_runs', 'cli_runs', 'errno', 'stress'):

`src/host/path-identity.js:2-35` (added)
    2  function knot_path_identity(path) {
    3    const bytes = io_bytes(path);
    4    if (bytes.includes(0)) return io_fail(process.platform === "darwin" ? 92 : 84);
    5    const fs = require("fs");
    6    // The compiler's path/source profile is ASCII. Buffer comparison also keeps
    7    // directory-entry case and normalization exact on insensitive filesystems.
    8    const parts = Buffer.from(bytes).toString("utf8").split("/");
    9    let current = path.startsWith("/") ? "/" : process.cwd();
   10    try {
   11      for (const part of parts) {
   12        if (part === "" || part === ".") continue;
   13        if (part === "..") {
   14          current = current.slice(0, current.lastIndexOf("/")) || "/";
   15          continue;
   16        }
   17        const next = current.replace(/\/$/, "") + "/" + part;
   18        const stat = fs.lstatSync(next);
   19        if (stat.isSymbolicLink()) return io_done(false);
   20        const exact = fs.readdirSync(current, { encoding: "buffer" })
   21          .some(name => Buffer.from(name).equals(Buffer.from(part)));
   22        if (!exact) return io_done(false);
   23        current = next;
   24      }
   25      return io_done(true);
   26    } catch (error) {
   27      if (error.code === "ENOENT" || error.code === "ENOTDIR") {
   28        return io_done(true);
   29      }
   30      return io_fail(typeof error.errno === "number" ? -error.errno : 5);
   31    }
   32  }
   33  
   34  io_eff(CID(inspect), knot_path_identity);
   35  

`tests/compiler-modules/check.py:215-220` (added)
  215  def adapter_drift(root, pins, host):
  216      """Files of the foreign path query whose bytes differ from the pins, are missing or unpinned."""
  217      drift = {path for path, identity in pins.items()
  218               if not (root / path).is_file() or digest(root / path) != identity}
  219      present = {p.relative_to(root).as_posix() for p in (root / host).rglob('*') if p.is_file()}
  220      return sorted(drift | (present - set(pins)))

`tests/compiler-modules/check.py:892-967` (added)
  892  def main():
  893      BUILD.mkdir(parents=True, exist_ok=True)
  894      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  895      manifest = json.loads((HERE / 'expectations.json').read_text())
  896      paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
  897               ROOT / 'src/CONTRACT.json', HOST, Path(__file__), HERE / 'expectations.json',
  898               HERE / 'FIXTURES.md', HERE / 'regen.py', HERE / 'regressions.json',
  899               HERE / 'host-check-expectations.json',
  900               HERE / 'probes.json', HERE / 'pin.bend', HERE / 'pin-expectations.json',
  901               HERE / 'review-round2.json', HERE / 'review-round3.json', HERE / 'review-round4.json',
  902               HERE / 'review-round5.json', HERE / 'review-round6.json', HERE / 'review-round7.json',
  903               *sorted((ROOT / 'src/host').glob('*')),
  904               ROOT / 'tests/compiler-io-abi-2/expectations.json',
  905               *sorted((ROOT / 'tests/compiler-io-abi-2/reference').glob('*'))]
  906      paths += [p for folder in ('fixtures', 'calls', 'bundle', 'regressions', 'probes', 'review-round2', 'review-round3',
  907                                 'review-round4', 'review-round5', 'review-round6', 'review-round7')
  908                for p in sorted((HERE / folder).rglob('*')) if p.is_file()]
  909      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  910                'status': 'incomplete', 'seed': manifest['seed'],
  911                'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}}
  912      try:
  913          record['reference_verification'] = successful(['python3', HERE / 'regen.py'])
  914          supplemental, record['supplemental_reference'] = supplemental_reference(manifest)
  915          probes, record['probe_reference'] = probe_reference(manifest)
  916          review, record['review_reference'] = review_reference(manifest, 'review-round2')
  917          round3, record['round3_reference'] = review_reference(manifest, 'review-round3')
  918          round4, record['round4_reference'] = review_reference(manifest, 'review-round4')
  919          round5, record['round5_reference'] = review_reference(manifest, 'review-round5')
  920          round6, record['round6_reference'] = review_reference(manifest, 'review-round6')
  921          round7, record['round7_reference'] = review_reference(manifest, 'review-round7')
  922          review += round3 + round4 + round5 + round6 + round7
  923          record['adapters'] = adapter_pins()
  924          record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
  925                             for tool in ('bun', 'node', 'python3')}
  926          require(record['tools']['node'] == 'v22.22.3', record['tools'])
  927          record['base_reference'] = base_reference(manifest)
  928          record['proofs'] = []
  929          for entry in PROOFS:
  930              result = successful([*SEED, ROOT / entry])
  931              require(result['stdout'].strip() == 'All terms check.', result)
  932              record['proofs'].append({'entry': entry, 'result': result})
  933          lanes = build_lanes(record)
  934          pin_controls(record)
  935          record['tampered_base'] = tampered_base(lanes, json.loads((HERE / 'pin-expectations.json').read_text()))
  936          record['output_guard'] = output_guard(lanes)
  937          record['fixtures'] = []
  938          for fixture in [*manifest['fixtures'], *supplemental, *probes, *review]:
  939              record['fixtures'].append(fixture_observations(fixture, lanes, record['base_reference']))
  940          record['mutants'] = mutants([*manifest['fixtures'], *review])
  941          require(all(digest(ROOT / path) == identity for path, identity in record['inputs'].items()),
  942                  'Inputs changed during modules gate')
  943          seed_dir = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
  944          require(all(digest(seed_dir / name) == identity
  945                      for name, identity in manifest['seed']['sha256'].items()),
  946                  'Pinned seed changed during modules gate')
  947          record['status'] = 'passed'
  948      except Exception as error:
  949          record['failure'] = repr(error)
  950          raise
  951      finally:
  952          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  953      fixtures = record['fixtures']
  954      lane_records = [lane for fixture in fixtures for lane in fixture['lanes'].values()]
  955      calls = sum(len(fixture['reference']) for fixture in fixtures)
  956      evaluations = sum(len(lane['evaluations']) for lane in lane_records)
  957      wasm = sum(len(lane['wasm']) for lane in lane_records)
  958      preserved = sum(lane['artifact_preserved'] for lane in lane_records)
  959      pairs = sum(fixture.get('byte_identical', False) for fixture in fixtures)
  960      audits = sum('audit' in lane for lane in lane_records)
  961      print(f'Modules gate passed: {len(fixtures)} fixtures, {calls} seed calls, '
  962            f'{len(lane_records)} checks, {evaluations} evaluations, {len(lane_records)} compilations, '
  963            f'{wasm} Wasm observations, {pairs} byte-identity pairs, '
  964            f'{preserved} preserved outputs, {audits} trust audits, '
  965            f'{len(record["pin"])} pin observations, {len(record["tampered_base"])} tampered-Base observations, '
  966            f'{len(record["output_guard"])} output-guard observations, '
  967            f'{len(record["mutants"])} semantic mutants')

diff --git a/tools/census/census.mjs b/tools/census/census.mjs
index 37a7e7b4..b68ef53c 100644
--- a/tools/census/census.mjs
+++ b/tools/census/census.mjs
@@ -225,5 +225,12 @@ export function policyViolations(files, policy) {
     if (!entry) { violations.push(`${file}: missing dependency inventory`); return; }
     entry.imports.forEach(i => visit(i.file));
-    for (const feature of entry.features) if (policy.forbidden_dependency_features.includes(feature)) violations.push(`${file}: forbidden dependency feature ${feature}`);
+    const exception = policy.dependency_feature_exceptions?.[file];
+    for (const feature of entry.features) {
+      const pinned = typeof exception?.sha256 === 'string' && exception.sha256 === entry.sha256
+        && exception.features.includes(feature);
+      if (policy.forbidden_dependency_features.includes(feature) && !pinned) {
+        violations.push(`${file}: forbidden dependency feature ${feature}`);
+      }
+    }
   };
   for (const f of files.filter(f => f.file.startsWith('src/'))) {

`tools/census/tests/host-boundary.test.mjs:8-11` (added)
    8  const entry = {
    9    file, sha256: identity, imports: [], features: ['foreign'],
   10    declarations: [{ id: `${file}::inspect:foreign_definition`, features: ['foreign'] }],
   11  };

`tools/census/tests/host-boundary.test.mjs:12-12` (added)
   12  const exception = { [file]: { sha256: identity, features: ['foreign'] } };

`tools/census/tests/host-boundary.test.mjs:13-15` (added)
   13  const policy = {
   14    ...approvedPolicy([entry]), dependency_feature_exceptions: exception,
   15  };

`tools/census/tests/host-boundary.test.mjs:16-39` (added)
   16  const forbidden = files => policyViolations(files, policy).filter(v => v.includes('forbidden dependency feature'));
   17  
   18  test('host foreign query needs an explicit reviewed exception', () => {
   19    assert.deepEqual(policyViolations([entry], approvedPolicy([entry])),
   20      [`${file}: forbidden dependency feature foreign`]);
   21  });
   22  
   23  test('only the exact source hash receives the foreign exception', () => {
   24    assert.deepEqual(forbidden([entry]), []);
   25    assert.deepEqual(forbidden([{ ...entry, sha256: sha256('different host query') }]),
   26      [`${file}: forbidden dependency feature foreign`]);
   27  });
   28  
   29  test('the host exception does not extend to another file', () => {
   30    const other = 'src/other-host.bend';
   31    assert.deepEqual(forbidden([{ ...entry, file: other }]),
   32      [`${other}: forbidden dependency feature foreign`]);
   33  });
   34  
   35  test('the host exception leaves other forbidden features in force', () => {
   36    assert.deepEqual(forbidden([{ ...entry, features: ['foreign', 'unsafe', 'arrays'] }]),
   37      [`${file}: forbidden dependency feature arrays`, `${file}: forbidden dependency feature unsafe`]);
   38  });
   39  
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
