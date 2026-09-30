// Invoke the seed and Knot; expectations come only from the frozen contract.
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { ROOT, SEED_COMMAND, observe, run, fileHash, sourceHashes, hash } from './lib/system.mjs';
import { receiptJSON } from './lib/receipt.mjs';

const fixtures = 'bench/fixtures/review-r1';
const manifest = `${fixtures}/expectations.json`;
const local = path.join(ROOT, '.local/bench-2/review-r1');
mkdirSync(local, { recursive: true });
const cases = [
  ...['expr-gap-1', 'expr-gap-3', 'pattern-gap-1', 'pattern-gap-3',
    'field-expr-gap-1', 'field-expr-gap-3', 'field-pattern-gap-1', 'field-pattern-gap-3']
    .map(name => ({ name, family: 'braces', refusal: ['Invalid', 'parse', 'detached-brace'] })),
  ...['expr-adjacent', 'pattern-adjacent', 'field-adjacent', 'declaration-spaced']
    .map(name => ({ name, family: 'braces' })),
  ...['matched-enum-let', 'matched-box-let', 'matched-enum-erased', 'matched-enum-reusable']
    .map(name => ({ name, family: 'inference', refusal: ['Invalid', 'check', 'annotation-required'] })),
  ...['matched-enum-annotated', 'matched-box-annotated', 'unmatched-enum-let',
    'unmatched-box-let', 'matched-field-let'].map(name => ({ name, family: 'inference' })),
  ...['field-shadow', 'field-shadow-erased', 'field-shadow-data']
    .map(name => ({ name, family: 'fields', refusal: ['Unsupported', 'check', 'dependent-field-type'] })),
  ...['field-renamed', 'field-self-name', 'field-later-name'].map(name => ({ name, family: 'fields' })),
  ...['empty-type', 'empty-data', 'empty-last', 'empty-field'].map(name => ({ name, family: 'empty' })),
].map(c => ({ ...c, program: `${fixtures}/${c.name}.bend`,
  fielded: cNameFielded(c.name), expected: c.refusal ? undefined : { ordinal: 1, constructor: 'On{}' } }));

function cNameFielded(name) {
  return name.startsWith('field-') || name.includes('-box-') || name === 'matched-field-let' || name === 'empty-field';
}

// Freeze once. This command never invokes Knot and cannot derive its oracle
// from the implementation under repair.
if (process.argv.includes('--freeze')) {
  assert.ok(!existsSync(path.join(ROOT, manifest)), 'expectations already frozen');
  const directory = mkdtempSync(path.join(local, 'seed-'));
  const frozen = [];
  for (const c of cases) {
    const check = observe([...SEED_COMMAND, c.program, '--check-only']);
    assert.equal(check.error, null, c.name);
    assert.equal(check.exit, c.refusal ? 1 : 0, `${c.name}: ${check.stderr}`);
    if (!c.refusal) assert.equal(check.stdout, 'All terms check.', c.name);
    const execution = c.refusal ? undefined : run([...SEED_COMMAND, c.program]);
    if (execution) assert.equal(execution.stdout, c.expected.constructor, c.name);
    const lanes = {};
    // Emitted seed builds require Base, which reserves Empty. Check and execute
    // the original above, then build an explicitly recorded renamed control.
    const original = readFileSync(path.join(ROOT, c.program), 'utf8');
    const buildSource = c.family === 'empty' ? original.replace(/\bEmpty\b/g, 'Vacant') : original;
    const buildProgram = c.family === 'empty' ? path.join(directory, `${c.name}-Vacant.bend`) : path.join(ROOT, c.program);
    if (c.family === 'empty') writeFileSync(buildProgram, buildSource);
    const wrapper = path.join(directory, `${c.name}.bend`);
    writeFileSync(wrapper, `import Base\nimport ${path.relative(directory, buildProgram)} as F\n\ndef main() -> F.Flag:\n  F.main()\n`);
    for (const lane of ['native', 'bun']) {
      const output = path.join(directory, `${c.name}-${lane}${lane === 'bun' ? '.js' : ''}`);
      const build = observe([...SEED_COMMAND, c.refusal ? c.program : wrapper, '-o', output]);
      assert.equal(build.error, null, c.name);
      assert.equal(build.exit, c.refusal ? 1 : 0, `${c.name}/${lane}: ${build.stderr}`);
      if (c.refusal) {
        assert.equal(existsSync(output), false, c.name);
        lanes[lane] = { build };
      } else {
        const execution = run([...(lane === 'bun' ? ['bun', '--no-env-file'] : []), output]);
        assert.ok(execution.stdout.endsWith(`.${c.expected.constructor}`), `${c.name}/${lane}: ${execution.stdout}`);
        lanes[lane] = { build, execution };
      }
    }
    frozen.push({ ...c, sourceSha256: fileHash(path.join(ROOT, c.program)), seedCheck: check,
      seedExecution: execution, seedBuildControl: c.family === 'empty' ? { reason: 'Base reserves Empty', source: buildSource } : undefined,
      seed: lanes });
    console.log(`Frozen ${c.name}: seed ${c.refusal ? 'rejects' : 'accepts'} in both build lanes`);
  }
  const contract = JSON.parse(readFileSync(path.join(ROOT, 'src/CONTRACT.json')));
  writeFileSync(path.join(ROOT, manifest), receiptJSON({ schemaVersion: 1, status: 'frozen',
    seed: contract.seed, contract: `${fixtures}/CONTRACT.md`,
    contractSha256: fileHash(path.join(ROOT, fixtures, 'CONTRACT.md')), cases: frozen }), { flag: 'wx' });
} else {
  const frozen = JSON.parse(readFileSync(path.join(ROOT, manifest)));
  assert.equal(frozen.status, 'frozen');
  assert.equal(frozen.cases.length, 31);
  assert.equal(fileHash(path.join(ROOT, frozen.contract)), frozen.contractSha256);
  for (const c of frozen.cases) assert.equal(fileHash(path.join(ROOT, c.program)), c.sourceSha256);
  assert.deepEqual(frozen.cases.map(({ sourceSha256, seedCheck, seedExecution, seedBuildControl, seed, ...c }) => c),
    JSON.parse(JSON.stringify(cases)), 'literal contract metadata changed');
  const identity = sourceHashes();
  const harness = { [manifest]: fileHash(path.join(ROOT, manifest)),
    'bench/review-r1.mjs': fileHash(path.join(ROOT, 'bench/review-r1.mjs')) };
  const key = hash(JSON.stringify({ identity, harness, seed: frozen.seed })).slice(0, 16);
  const directory = path.join(local, `build-${key}`);
  mkdirSync(directory, { recursive: true });
  const lanes = process.argv.includes('--lane=bun') ? ['bun'] : ['native', 'bun'];
  const only = process.argv.find(s => s.startsWith('--only='))?.slice(7);
  const selected = frozen.cases.filter(c => !only || c.family === only);
  assert.ok(selected.length > 0, 'empty selection');
  const builds = {};
  for (const lane of lanes) {
    builds[lane] = {};
    for (const [name, entry] of [['check', 'src/check-cli.bend'], ['eval', 'src/eval-cli.bend'],
      ['enum', 'src/compile-cli.bend'], ['fields', 'tests/compiler-fields-wasm/compile.bend']]) {
      const output = path.join(directory, `${name}-${lane}${lane === 'bun' ? '.js' : ''}`);
      const record = `${output}.json`;
      if (!existsSync(record)) {
        const build = run([...SEED_COMMAND, entry, '-o', output]);
        writeFileSync(record, JSON.stringify({ build, sha256: fileHash(output) }));
      }
      const build = JSON.parse(readFileSync(record));
      assert.equal(fileHash(output), build.sha256, 'cached build identity changed');
      builds[lane][name] = { ...build, command: [...(lane === 'bun' ? ['bun', '--no-env-file'] : []), output] };
    }
  }
  const observations = [], failures = [];
  let phaseObservations = 0, absenceGuards = 0, preservationGuards = 0, wasmExecutions = 0, byteIdenticalPairs = 0;
  for (const c of selected) {
    const row = { name: c.name, family: c.family, lanes: {} };
    const binaries = {};
    for (const lane of lanes) {
      const commands = builds[lane];
      const values = {};
      const check = (result, refusal) => {
        assert.equal(result.error, null, JSON.stringify(result));
        assert.equal(result.exit, refusal ? refusal[0] === 'Invalid' ? 2 : 3 : 0, JSON.stringify(result));
        if (refusal) {
          assert.equal(result.stdout, '', JSON.stringify(result));
          assert.ok(result.stderr.startsWith(`${refusal.join('\t')}\t`), JSON.stringify(result));
        } else assert.equal(result.stderr, '', JSON.stringify(result));
      };
      try {
        values.check = observe([...commands.check.command, c.program]); phaseObservations++;
        check(values.check, c.refusal);
        if (!c.refusal) assert.ok(values.check.stdout.startsWith('Checked\n'));
        values.eval = observe([...commands.eval.command, c.program, 'main', '1048576']); phaseObservations++;
        check(values.eval, c.refusal);
        if (!c.refusal) assert.match(values.eval.stdout, /^Evaluated\t\d+\t1\tOn\{\}$/);
        for (const profile of ['enum', 'fields']) {
          const refusal = c.refusal || (profile === 'enum' && c.fielded ? ['Unsupported', 'check', 'constructor-fields'] : undefined);
          const output = path.join(directory, `${c.name}-${lane}-${profile}.wasm`);
          if (refusal) {
            // Distinct never-created output, followed by a pre-existing sentinel.
            const fresh = path.join(mkdtempSync(path.join(directory, 'absence-')), 'output.wasm');
            const absent = observe([...commands[profile].command, c.program, fresh]);
            phaseObservations++; check(absent, refusal);
            assert.equal(existsSync(fresh), false); absenceGuards++;
            const sentinel = Buffer.from('existing artifact must survive refusal\n');
            writeFileSync(output, sentinel);
            const preserved = observe([...commands[profile].command, c.program, output]);
            phaseObservations++; check(preserved, refusal);
            assert.deepEqual(readFileSync(output), sentinel); preservationGuards++;
            values[profile] = { absent, preserved };
          } else {
            const compiled = observe([...commands[profile].command, c.program, output]);
            phaseObservations++; check(compiled);
            assert.match(compiled.stdout, /^Built\t\d+$/);
            const runtime = run(['node', 'scripts/run-wasm.mjs', `--profile=knot-${profile === 'enum' ? 'enum' : 'fields-wasm'}-1`, output, 'main']);
            const result = JSON.parse(runtime.stdout);
            assert.equal(result.validated, true); assert.equal(result.result, c.expected.ordinal);
            assert.equal(result.bytes, readFileSync(output).length); wasmExecutions++;
            binaries[`${lane}/${profile}`] = readFileSync(output);
            values[profile] = { compiled, runtime, sha256: fileHash(output) };
          }
        }
      } catch (error) { failures.push({ name: c.name, lane, message: error.message }); }
      row.lanes[lane] = values;
    }
    for (const profile of ['enum', 'fields']) {
      if (binaries[`native/${profile}`] && binaries[`bun/${profile}`]) {
        assert.deepEqual(binaries[`native/${profile}`], binaries[`bun/${profile}`]); byteIdenticalPairs++;
      }
    }
    observations.push(row);
  }
  assert.deepEqual(sourceHashes(), identity, 'sources changed during verification');
  for (const [file, sha] of Object.entries(harness)) assert.equal(fileHash(path.join(ROOT, file)), sha);
  const receipt = { schemaVersion: 1, status: failures.length ? 'failed' : 'passed',
    command: process.argv.slice(1), seed: frozen.seed, sourceHashes: identity, harnessHashes: harness,
    selection: only || 'all', builds, counts: { programs: selected.length, compilerLanes: lanes.length,
      phaseObservations, absenceGuards, preservationGuards, wasmExecutions, byteIdenticalPairs }, failures, observations };
  const target = process.argv.find(s => s.startsWith('--receipt='))?.slice(10)
    || path.join(local, `verification-${only || 'all'}-${lanes.length}.json`);
  writeFileSync(target, receiptJSON(receipt));
  console.log(JSON.stringify({ status: receipt.status, counts: receipt.counts, failures }, null, 2));
  if (failures.length) process.exitCode = 1;
}
