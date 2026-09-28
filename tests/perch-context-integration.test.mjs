import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, readdir, realpath, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createBendSourceSnapshot } from '../scripts/perch-bend-context.mjs';
import { prepareStyleTargets, changedStyleSources, runStylePreflight } from '../scripts/perch-style.mjs';

const configText = await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'), config = JSON.parse(configText);
const sha = s => createHash('sha256').update(s).digest('hex');
const body = 'import Base\ndef next(x: U32) -> U32: (x + 1 : U32)\n';
async function fixture(t, files) {
  const root = await mkdtemp(join(tmpdir(), 'perch-context-integration-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const [path, text] of Object.entries({ 'perch-style.json': configText, ...files })) {
    await mkdir(join(root, path, '..'), { recursive: true });
    await writeFile(join(root, path), text);
  }
  return realpath(root);
}
const manifest = { schema: 1, context: 'interfaces-v1', groups: [
  { name: 'caller', files: ['main.bend', 'lib.bend'], selected_files: ['main.bend'] },
  { name: 'library', files: ['lib.bend'] },
] };
const sources = { 'lib.bend': body, 'main.bend': 'import Base\nimport ./lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n' };
async function preflight(root, args) {
  let report;
  const code = await runStylePreflight([...args, '--json'], { root, stdout: text => { report = JSON.parse(text); } });
  return { code, report };
}
test('versioned compiler manifest selects every source and declaration in full somewhere', async () => {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const m = JSON.parse(await readFile(join(root, 'docs/compiler-campaign/manifest.json'), 'utf8'));
  assert.equal(m.context, 'interfaces-v1');
  const selected = new Set(m.groups.flatMap(g => g.selected_files ?? g.files));
  assert.deepEqual([...selected].sort(), (await readdir(join(root, 'src'))).filter(f => f.endsWith('.bend')).map(f => `src/${f}`).sort());
  for (const g of m.groups) for (const f of g.selected_files ?? g.files) assert.ok(g.files.includes(f));
});
test('manifest interface policy preserves complete selected text and remains wholly offline', async t => {
  t.mock.method(process, 'loadEnvFile', () => { throw new Error('environment forbidden'); });
  t.mock.method(globalThis, 'fetch', () => { throw new Error('network forbidden'); });
  const root = await fixture(t, { ...sources, 'manifest.json': JSON.stringify(manifest) });
  const { code, report } = await preflight(root, ['--manifest=manifest.json']);
  assert.equal(code, 0);
  assert.equal(report.provider_requests, 0);
  assert.equal(report.summary.units, 2);
  assert.equal(report.summary.compositions_available, 2);
  assert.deepEqual(report.groups[0].composition.selected_files, ['main.bend']);
  assert.deepEqual(report.groups[0].composition.representations.map(r => r.representation), ['full', 'interface']);
});
test('interface manifests cannot hide unselected files or open local import closures', async t => {
  const root = await fixture(t, sources);
  for (const groups of [[manifest.groups[0]], [{ name: 'x', files: ['main.bend'] }, manifest.groups[1]]]) {
    await writeFile(join(root, 'manifest.json'), JSON.stringify({ ...manifest, groups }));
    await assert.rejects(preflight(root, ['--manifest=manifest.json']), /never selected|local import closure/);
  }
});
test('versioned datatype CLI follows the type closure instead of legacy one-file scope', async t => {
  const root = await fixture(t, { 'main.bend': 'import Base\nimport ./lib.bend as L\ntype Root is Data:\n  Root{value: L.Box}\n',
    'lib.bend': 'import Base\ntype Box is Data:\n  Box{}\n' });
  const { code, report } = await preflight(root, ['--context=interfaces-v1', 'main.bend::Root']);
  assert.equal(code, 0);
  assert.equal(report.summary.truncated_units, 0);
  assert.equal(report.composition.available, true);
});
test('explicit package store works outside workspace and pins all members for freshness', async t => {
  const members = { 'lib.bend': body, LICENSE: 'license\n' };
  const id = '0x' + sha(Object.keys(members).sort().map(p => `${sha(members[p])} ${p}\n`).join('')).slice(0, 32);
  const store = await fixture(t, {});
  // A hash store's membership excludes the fixture's unrelated top-level config.
  await mkdir(join(store, id));
  for (const [p, s] of Object.entries(members)) await writeFile(join(store, id, p), s);
  const root = await fixture(t, { 'main.bend': `import Base\nimport ${id}/lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n` });
  const result = await preflight(root, ['--context=interfaces-v1', `--package-store=${store}`, 'main.bend']);
  assert.equal(result.code, 0);
  assert.deepEqual(result.report.composition.unresolved, []);
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1', packageStore: store });
  const candidates = await prepareStyleTargets(['main.bend'], null, config, root, snapshot);
  assert.deepEqual(await changedStyleSources(candidates, root), []);
  await writeFile(join(store, id, 'LICENSE'), 'tampered unused member\n');
  assert.deepEqual(await changedStyleSources(candidates, root), [`${id}/LICENSE`]);
  const broken = await preflight(root, ['--context=interfaces-v1', `--package-store=${store}`, 'main.bend']);
  assert.equal(broken.code, 3);
  assert.ok(broken.report.composition.unresolved.some(r => r.reason === 'package-hash-mismatch'));
});
test('published relative imports cannot leave the verified package membership', async t => {
  const lib = 'import Base\nimport ../outside.bend as O\ndef next(x: U32) -> U32: O.next(x)\n';
  const id = '0x' + sha(`${sha(lib)} lib.bend\n`).slice(0, 32);
  const root = await fixture(t, { [`store/${id}/lib.bend`]: lib, 'store/outside.bend': body,
    'main.bend': `import Base\nimport ${id}/lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n` });
  const { code, report } = await preflight(root, ['--context=interfaces-v1', '--package-store=store', 'main.bend']);
  assert.equal(code, 3);
  assert.ok(report.composition.unresolved.some(r => r.reason === 'package-member-not-found'));
});
test('signature closure omits unused bodies and includes types from overflow caller signatures', async t => {
  const root = await fixture(t, {
    'main.bend': 'import Base\nimport ./lib.bend as L\ndef target(x: U32) -> U32: x\n'
      + Array.from({ length: 5 }, (_, i) => `def use${i}(x: U32, y: L.Box) -> U32: target(x)\n`).join(''),
    'lib.bend': 'import Base\ntype Box is Data:\n  Box{}\ndef unused(x: U32) -> U32: (x + 31337 : U32)\n',
  });
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  const [c] = await prepareStyleTargets(['main.bend::target'], null, config, root, snapshot);
  assert.ok(c.state.datatypes.some(d => d.name === 'Box'));
  assert.equal(c.context.truncated, false);
  assert.ok(c.context.summarized.some(r => r.reason === 'context-caller-interface'));
  assert.ok(!JSON.stringify(c.state).includes('31337'));
  const actual = ['calls', 'called_by', 'laws', 'datatypes'].reduce((n, k) => n + c.state[k].reduce((s, d) => s + Buffer.byteLength(d.source), 0), Buffer.byteLength(c.state.source));
  assert.equal(c.context.source_bytes, actual);
});
test('encoded-state budget demotes bodies while keeping task and selected source intact', async t => {
  const large = '# ' + 'x'.repeat(22000) + '\n';
  const source = 'import Base\n' + large + 'def first(x: U32) -> U32: x\n' + large
    + 'def second(x: U32) -> U32: x\ndef main(x: U32) -> U32: first(second(x))\n';
  const root = await fixture(t, { 'main.bend': source });
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  const task = 'a'.repeat(16000);
  const [c] = await prepareStyleTargets(['main.bend::main'], task, config, root, snapshot);
  assert.equal(c.state.cohort, task);
  assert.equal(c.state.source.trim(), 'def main(x: U32) -> U32: first(second(x))');
  assert.ok(Buffer.byteLength(JSON.stringify(c.state)) <= 60000);
  assert.ok(c.context.source_bytes <= 48000);
  assert.equal(c.context.truncated, false);
  assert.ok(c.context.summarized.some(r => r.reason === 'context-state-interface'));
});
test('local symlink cycles canonicalize and external symlinks remain unresolved', async t => {
  const root = await fixture(t, { 'main.bend': 'import Base\nimport ./alias.bend as A\ntype Root is Data:\n  Root{value: A.Root}\n' });
  await symlink('main.bend', join(root, 'alias.bend'));
  assert.equal((await preflight(root, ['--context=interfaces-v1', 'main.bend'])).code, 0);
  await rm(join(root, 'alias.bend'));
  const external = await fixture(t, { 'out.bend': body });
  await symlink(join(external, 'out.bend'), join(root, 'alias.bend'));
  const broken = await preflight(root, ['--context=interfaces-v1', 'main.bend']);
  assert.equal(broken.code, 3);
  assert.ok(broken.report.composition.unresolved.some(r => r.reason === 'outside-workspace'));
});
test('missing published packages and missing law contracts stay explicit', async t => {
  const root = await fixture(t, { 'main.bend': 'import Base\nimport ./LAWS.bend as L\ndef L.missing(x): {==}\n', 'LAWS.bend': 'import Base\n' });
  const law = await preflight(root, ['--context=interfaces-v1', 'main.bend']);
  assert.equal(law.code, 3);
  assert.ok(law.report.composition.unresolved.some(r => r.reason === 'imported-law-unavailable'));
  await writeFile(join(root, 'main.bend'), 'import Base\nimport 0x11111111111111111111111111111111/lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n');
  const missing = await preflight(root, ['--context=interfaces-v1', 'main.bend']);
  assert.equal(missing.code, 3);
  assert.ok(missing.report.composition.unresolved.some(r => r.reason === 'package-not-found'));
});

test('default package store follows BEND_LIB or home and still verifies all bytes', async t => {
  const id = '0x' + sha(`${sha(body)} lib.bend\n`).slice(0, 32);
  const store = await fixture(t, { [`${id}/lib.bend`]: body });
  const home = await fixture(t, { [`.bend/lib/${id}/lib.bend`]: body });
  const root = await fixture(t, { 'main.bend': `import Base\nimport ${id}/lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n` });
  const script = `import { runStylePreflight } from ${JSON.stringify(new URL('../scripts/perch-style.mjs', import.meta.url).href)};
    const code = await runStylePreflight(['--context=interfaces-v1', 'main.bend', '--json'], { root: process.cwd() });
    process.stderr.write(String(code));`;
  for (const useEnv of [true, false]) {
    const env = { ...process.env, HOME: home, BEND_NO_TELEMETRY: '1' };
    delete env.NODE_TEST_CONTEXT;
    if (useEnv) env.BEND_LIB = store; else delete env.BEND_LIB;
    const report = JSON.parse(execFileSync(process.execPath, ['--input-type=module', '-e', script],
      { cwd: root, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));
    assert.equal(report.structural_blockers, 0);
    assert.equal(report.composition.available, true);
    const path = useEnv ? join(store, id, 'lib.bend') : join(home, '.bend/lib', id, 'lib.bend');
    await writeFile(path, body + '# tampered\n');
    const broken = JSON.parse(execFileSync(process.execPath, ['--input-type=module', '-e', script],
      { cwd: root, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));
    assert.equal(broken.composition.available, false);
    assert.ok(broken.composition.unresolved.some(r => r.reason === 'package-hash-mismatch'));
  }
});
test('bare relative imports close locally while long hash imports remain explicitly unsupported', async t => {
  const root = await fixture(t, { ...sources,
    'main.bend': sources['main.bend'].replace('./lib.bend', 'lib.bend'), 'manifest.json': JSON.stringify(manifest) });
  assert.equal((await preflight(root, ['--manifest=manifest.json'])).code, 0);
  await writeFile(join(root, 'manifest.json'), JSON.stringify({ ...manifest, groups: [
    { name: 'caller', files: ['main.bend'] }, manifest.groups[1],
  ] }));
  await assert.rejects(preflight(root, ['--manifest=manifest.json']), /local import closure/);
  const long = '0x' + '1'.repeat(64) + '/lib.bend';
  await writeFile(join(root, 'main.bend'), sources['main.bend'].replace('./lib.bend', long));
  const result = await preflight(root, ['--manifest=manifest.json']);
  assert.equal(result.code, 3);
  assert.ok(result.report.groups[0].composition.unresolved.some(r => r.reason === 'unsupported-package-identity'));
});
test('apostrophe parameter types and body punctuation cannot crash manifest preflight', async t => {
  const lib = await readFile(new URL('./perch-context/fixtures/signatures.bend', import.meta.url), 'utf8');
  const root = await fixture(t, { 'lib.bend': lib,
    'main.bend': "import Base\nimport ./lib.bend as L\ndef main() -> U32: L.parameter(L.classify(':'))\n",
    'manifest.json': JSON.stringify(manifest) });
  const result = await preflight(root, ['--manifest=manifest.json']);
  assert.equal(result.code, 0);
  assert.equal(result.report.structural_blockers, 0);
  assert.equal(result.report.summary.supporting_role_impossible, 0);
});
