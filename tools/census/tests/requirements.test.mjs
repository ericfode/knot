import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { ROOT, acceptedInventory, sha256 } from '../census.mjs';
import { discoverSuites } from '../evidence.mjs';
import { measureClosure, selfhostInventory, meterSummary } from '../meter.mjs';

const read = file => fs.readFileSync(path.join(ROOT, 'tools/census', file), 'utf8');
const control = JSON.parse(read('fixtures/requirements.json'));
const meter = JSON.parse(read('fixtures/meter.json'));
const stages = ['check', 'eval', 'wasm'];
const sets = object => Object.fromEntries(Object.entries(object).map(([s, values]) => [s, new Set(values)]));

function fixture(fn) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'knot-census-requirements-'));
  const write = (name, source) => {
    fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
    fs.writeFileSync(path.join(root, name), typeof source === 'string' ? source : JSON.stringify(source));
  };
  const registry = gates => {
    for (const [, program] of gates) write(program, "raise RuntimeError('inventory must not execute gates')\n");
    write('scripts/gates/run.py', `GATES = (${gates.map(([name, program]) => `Gate('${name}', ('python3', '${program}')),`).join('')})\n`);
  };
  try {
    const source = read('fixtures/' + control.source);
    write(control.directory + '/' + control.fixture, source);
    write(control.directory + '/expectations.json', {
      cases: [{ name: 'lambda', file: control.fixture, knot: control.requirement }],
      observations: { fixtures: [{ case: 'lambda', source_sha256: sha256(source), ...control.reference }] },
    });
    registry([]);
    return fn(root, registry);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
}

function checkUngated(inventory = acceptedInventory) {
  fixture(root => {
    const result = inventory(root);
    for (const stage of stages) {
      assert.deepEqual(result.classes.find(c => c.feature === 'lambdas').stages[stage].evidence, control.expected.ungated_evidence);
      const requirement = result.requirements.classes.find(c => c.feature === 'lambdas').stages[stage];
      assert.equal(requirement.status, 'covered-by-frozen-requirements');
      assert.deepEqual(requirement.fixtures, control.expected.requirement_fixtures);
    }
    assert.equal(result.fixtures.length, 0);
    assert.equal(result.requirements.fixtures.length, 1);
    assert.equal(result.requirements.suites[0].gate, 'closures');
    assert.equal(result.requirements.fixtures[0].sha256, sha256(read('fixtures/' + control.source)));
    const selfhost = selfhostInventory({ files: meter.files }, {
      roots: { compiler: { js: meter.closure }, frontend: { js: meter.closure } },
    }, result);
    assert.deepEqual(selfhost.requirements.classes, result.requirements.classes);
    assert.deepEqual(selfhost.requirements.suites, result.requirements.suites);
  });
}

test('a frozen but ungated suite is a requirement and never accepted evidence', () => checkUngated());

test('admission requires the mapped gate name and the suite program directory', () => fixture((root, registry) => {
  for (const gates of [
    [['closures-trust', control.directory + '/trust.py']],
    [['checker', control.directory + '/check.py']],
    [['closures', 'tests/compiler-checker/check.py']],
  ]) {
    registry(gates);
    const result = acceptedInventory(root);
    assert.deepEqual(result.classes.find(c => c.feature === 'lambdas').stages.wasm.evidence, []);
    assert.equal(result.requirements.fixtures.length, 1);
  }
  registry([['closures', control.directory + '/check.py']]);
  const result = acceptedInventory(root);
  for (const stage of stages) {
    assert.deepEqual(result.classes.find(c => c.feature === 'lambdas').stages[stage].evidence, control.expected.requirement_fixtures);
    assert.deepEqual(result.requirements.classes.find(c => c.feature === 'lambdas').stages[stage].fixtures, []);
  }
  assert.equal(result.fixtures.length, 1);
  assert.deepEqual(result.requirements.suites, []);
}));

test('a removed frontend gate leaves its frozen suite discoverable as a requirement', () => fixture(root => {
  const directory = path.join(root, 'tests/subsets');
  fs.mkdirSync(directory);
  fs.writeFileSync(path.join(directory, 'frontend-cases.json'), JSON.stringify({ cases: [{ file: 'control.bend', tree: 'literal tree' }] }));
  const suite = discoverSuites(root).suites.find(s => s.suite === 'frontend');
  assert.equal(suite.gate, 'frontend');
  assert.equal(suite.admission, 'requirement');
  assert.equal(suite.fixtures, 1);
}));

test('merged frozen suites stay out of evidence, including the baseslice Wasm regression', () => {
  const result = acceptedInventory();
  const registered = suite => result.registry.gates.some(g => g.name === suite
    && g.programs.some(p => path.posix.dirname(p.file) === `tests/compiler-${suite}`));
  for (const suite of control.expected.ungated_suites) {
    if (registered(suite)) continue;
    assert.ok(result.requirements.suites.some(s => s.suite === suite));
    assert.ok(result.requirements.fixtures.some(f => f.suite === suite));
    assert.ok(!result.fixtures.some(f => f.suite === suite));
    for (const c of result.classes) for (const s of Object.values(c.stages)) {
      assert.ok(!s.evidence.some(f => f.startsWith(suite + ':')));
    }
  }
  if (!registered('baseslice')) {
    const fixture = 'baseslice:tests/compiler-baseslice/fixtures/string-reverse-word.bend';
    const requirement = result.requirements.classes.find(c => c.feature === 'recursion').stages.wasm;
    assert.ok(requirement.fixtures.includes(fixture));
    assert.ok(!result.classes.find(c => c.feature === 'recursion').stages.wasm.evidence.includes(fixture));
  }
});

test('literal meter separates evidence from inclusive frozen requirement coverage', () => {
  const result = measureClosure(meter.closure, meter.files, sets(meter.evidence), sets(control.meter.requirements));
  assert.equal(result.totals.declarations, meter.expected.declarations);
  assert.equal(result.totals.check, meter.expected.check);
  assert.equal(result.totals.wasm, meter.expected.wasm);
  assert.deepEqual(result.missing, meter.expected.missing);
  assert.deepEqual(result.totals.covered_by_requirements, control.meter.covered_by_requirements);
  assert.deepEqual(result.missing_requirements, control.meter.missing_requirements);
  assert.deepEqual(Object.fromEntries(result.declarations.map(d => [d.key, d.missing_requirements])), control.meter.per_declaration);
  const summary = meterSummary({ roots: { compiler: result, frontend: result }, suite_reports: [] });
  assert.match(summary, /evidenced now: check 2\/3; Wasm 1\/3/);
  assert.match(summary, /covered by frozen requirements \(including evidenced\): check 3\/3; Wasm 2\/3/);
  assert.ok(summary.split('\n').length <= 14);
});

test('promoting a requirement to evidence preserves coverage without double counting', () => {
  const promoted = Object.fromEntries(Object.entries(meter.evidence).map(([s, values]) => [s, [...values, ...control.meter.requirements[s]]]));
  const result = measureClosure(meter.closure, meter.files, sets(promoted), sets({ check: [], wasm: [] }));
  assert.equal(result.totals.check, control.meter.covered_by_requirements.check);
  assert.equal(result.totals.wasm, control.meter.covered_by_requirements.wasm);
  assert.deepEqual(result.totals.covered_by_requirements, control.meter.covered_by_requirements);
  assert.deepEqual(result.missing_requirements, control.meter.missing_requirements);
});

test('semantic mutant: admitting ungated requirements as evidence is killed', async () => {
  const target = path.join(ROOT, 'tools/census/census.mjs');
  const before = "records.filter(r => r.admission === 'evidence')";
  let source = fs.readFileSync(target, 'utf8');
  assert.equal(source.split(before).length - 1, 1, 'unique mutant anchor');
  source = source.replace(before, 'records').replaceAll('import.meta.url', JSON.stringify(pathToFileURL(target).href));
  source = source.replace(/from '([^']+)'/g, (match, module) => module.startsWith('.')
    ? `from '${pathToFileURL(path.resolve(path.dirname(target), module)).href}'` : match);
  const checked = spawnSync('node', ['--check', '--input-type=module'], { input: source, encoding: 'utf8' });
  assert.equal(checked.status, 0, checked.stderr);
  const mutant = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  checkUngated();
  assert.throws(() => checkUngated(mutant.acceptedInventory), assert.AssertionError);
});
