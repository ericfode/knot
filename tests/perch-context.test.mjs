import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { analyzeBendSource } from '../scripts/perch-bend.mjs';
const { createPackageStore, declarationInterface, buildInterface, createInterfaceReview, prepareInterfaceComposition } =
  await import(process.env.KNOT_CONTEXT_TEST_MODULE ?? '../scripts/perch-context-interfaces.mjs');
import { createBendSourceSnapshot } from '../scripts/perch-bend-context.mjs';
const sha = s => createHash('sha256').update(s).digest('hex');
const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
async function fixture(t, files = {}) {
  const root = await mkdtemp(join(tmpdir(), 'perch-context-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const [path, data] of Object.entries(files)) {
    await mkdir(join(root, path, '..'), { recursive: true });
    await writeFile(join(root, path), data);
  }
  return root;
}
const local = {
  'main.bend': 'import Base\nimport ./box.bend as B\ntype Root is Data:\n  Root{value: B.Box}\n',
  'box.bend': 'import Base\nimport ./leaf.bend as L\ntype Box is Data:\n  Box{value: L.Leaf}\n',
  'leaf.bend': 'import Base\ntype Leaf is Data:\n  Leaf{}\n',
};
async function review(root, name, limits = {}) {
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  const file = await snapshot.load('main.bend');
  return (await createInterfaceReview({ root, path: 'main.bend', ...file, snapshot, limits })).forUnit(name);
}
test('datatype closure follows imports beyond one file and terminates cycles', async t => {
  const root = await fixture(t, local);
  const ctx = await review(root, 'Root');
  assert.deepEqual(ctx.seen.datatypes.map(d => d.name).sort(), ['Box', 'Leaf']);
  assert.equal(ctx.provenance.truncated, false);
  assert.equal(ctx.provenance.files.length, 3);
  await writeFile(join(root, 'leaf.bend'), 'import Base\nimport ./main.bend as M\ntype Leaf is Data:\n  Leaf{value: M.Root}\n');
  const cycle = await review(root, 'Root');
  assert.equal(cycle.provenance.truncated, false);
  assert.equal(cycle.seen.datatypes.length, 2);
});
test('datatype byte exhaustion retains an explicit truncation marker', async t => {
  const root = await fixture(t, local);
  const ctx = await review(root, 'Root', { bytes: 1 });
  assert.equal(ctx.provenance.truncated, true);
  assert.equal(ctx.seen.context_notes.truncated, true);
  assert.ok(ctx.provenance.unresolved.some(r => r.reason === 'context-byte-limit'));
});
const payload = { 'lib.bend': 'import Base\ndef next(x: U32) -> U32: (x + 1 : U32)\n', LICENSE: 'literal license\n' };
// This independent oracle is the literal seed publish formula, not resolver code.
const identity = files => '0x' + sha(Object.keys(files).sort().map(p => sha(files[p]) + ' ' + p + '\n').join('')).slice(0, 32);
async function packageFixture(t, files = payload, mode = 'hash') {
  const id = identity(files), folder = mode === 'hash' ? `store/${id}` : 'packages/example';
  const root = await fixture(t, Object.fromEntries(Object.entries(files).map(([p, s]) => [`${folder}/${p}`, s])));
  if (mode !== 'hash') await writeFile(join(root, folder, 'RELEASE.json'), JSON.stringify({ expected_hash: id,
    closure: Object.keys(files).map(path => ({ path, sha256: sha(files[path]) })) }));
  return { root, id, folder };
}
test('published hash uses actual sorted closure bytes in explicit and repository stores', async t => {
  for (const mode of ['hash', 'release']) {
    const { root, id } = await packageFixture(t, payload, mode);
    const store = await createPackageStore(root, join(root, 'store'));
    const found = await store.resolve(`${id}/lib.bend`);
    assert.equal(found.reason, undefined);
    assert.equal(found.package_hash, id);
    assert.equal(found.source, payload['lib.bend']);
    assert.equal(found.provenance.length, mode === 'hash' ? 2 : 3);
  }
});
test('tampered unused package member cannot be accepted by its directory name', async t => {
  const { root, id, folder } = await packageFixture(t);
  await writeFile(join(root, folder, 'LICENSE'), 'changed\n');
  const result = await (await createPackageStore(root, join(root, 'store'))).resolve(`${id}/lib.bend`);
  assert.equal(result.source, undefined);
  assert.equal(result.reason, 'package-hash-mismatch');
});
test('release hash and member digests are evidence, not authority', async t => {
  const { root, id, folder } = await packageFixture(t, payload, 'release');
  await writeFile(join(root, folder, 'lib.bend'), payload['lib.bend'] + '# changed\n');
  const result = await (await createPackageStore(root)).resolve(`${id}/lib.bend`);
  assert.equal(result.source, undefined);
  assert.equal(result.reason, 'package-member-hash-mismatch');
});
test('package traversal, symlinks and environment members fail closed', async t => {
  const { root, id, folder } = await packageFixture(t);
  let store = await createPackageStore(root, join(root, 'store'));
  assert.equal((await store.resolve(`${id}/../lib.bend`)).reason, 'invalid-package-path');
  await symlink(join(root, folder, 'lib.bend'), join(root, folder, 'alias.bend'));
  store = await createPackageStore(root, join(root, 'store'));
  assert.equal((await store.resolve(`${id}/lib.bend`)).reason, 'package-symlink');
  await rm(join(root, folder, 'alias.bend'));
  await writeFile(join(root, folder, '.env'), 'DO NOT READ');
  store = await createPackageStore(root, join(root, 'store'));
  assert.equal((await store.resolve(`${id}/lib.bend`)).reason, 'package-forbidden-member');
});
test('definition interfaces keep nested and multiline signatures without leaking bodies', async () => {
  const source = 'import Base\ndef f(\n  x: U32,\n  g: (y: U32) -> U32\n) -> U32:\n  # body marker\n  g(x)\n';
  const parsed = await analyzeBendSource(source);
  assert.equal(parsed.parser_status, 'parsed');
  const head = declarationInterface(source, parsed.declarations[0]);
  assert.ok(head.includes('g: (y: U32) -> U32'));
  assert.ok(head.includes('interface: body omitted'));
  assert.ok(!head.includes('g(x)'));
  assert.ok(!head.includes('body marker'));
  const inline = 'import Base\ndef f(x: U32) -> U32: (x + 31337 : U32)\n';
  const a = await analyzeBendSource(inline);
  assert.ok(!declarationInterface(inline, a.declarations[0]).includes('31337'));
});
test('law statements remain signatures while checked proof bodies are omitted', async () => {
  const source = 'import Base\nlaw identity:\n  for x: U32\n  {x == x : U32}\ndef identity(x): {==}\n';
  const analysis = await analyzeBendSource(source);
  assert.equal(analysis.parser_status, 'parsed');
  const text = declarationInterface(source, analysis.declarations[0]);
  assert.ok(text.includes('{x == x : U32}'));
  assert.ok(!text.includes('{==}'));
});
test('interface file pins full source, preserves types and marks omitted implementation', async () => {
  const source = 'import Base\ntype Flag is Data:\n  Off{}\n  On{}\ndef flag() -> Flag: On{}\n';
  const file = { source, analysis: await analyzeBendSource(source), source_sha256: sha(source) };
  const summary = buildInterface('lib.bend', file);
  assert.ok(summary.includes(sha(source)));
  assert.ok(summary.includes('type Flag is Data:\n  Off{}\n  On{}'));
  assert.ok(!summary.includes('-> Flag: On{}'));
});
test('helper and caller overflow is explicitly summarized with signature closure', async t => {
  const source = ['import Base', 'def base(x: U32) -> U32: x',
    ...Array.from({ length: 7 }, (_, i) => `def f${i}(x: U32) -> U32: base(x)`),
    'def main(x: U32) -> U32: f0(f1(f2(f3(f4(f5(f6(x)))))))', ''].join('\n');
  const root = await fixture(t, { 'main.bend': source });
  const helpers = await review(root, 'main', { helpers: 2 });
  assert.equal(helpers.provenance.truncated, false);
  assert.ok(helpers.provenance.summarized.some(r => r.reason === 'context-helper-interface'));
  assert.ok(helpers.seen.calls.some(r => r.representation === 'interface'));
  const callers = await review(root, 'base');
  assert.equal(callers.provenance.truncated, false);
  assert.equal(callers.seen.called_by.filter(r => r.representation === 'full').length, 4);
  assert.equal(callers.seen.called_by.filter(r => r.representation === 'interface').length, 3);
  assert.equal(callers.provenance.summarized.filter(r => r.reason === 'context-caller-interface').length, 3);
});
async function composition(root, selected, cap = 48000) {
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  return prepareInterfaceComposition(selected, null, { ...config, potential_profundity: {
    ...config.potential_profundity, max_composition_bytes: cap } }, root, snapshot, new Set(['U32', 'Data', 'Type']));
}
test('composition preserves full selection and supplies external collaborators as interfaces', async t => {
  const files = { 'main.bend': 'import Base\nimport ./lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n',
    'lib.bend': 'import Base\ndef next(x: U32) -> U32: (x + 31337 : U32)\n' };
  const root = await fixture(t, files), result = await composition(root, ['main.bend']);
  assert.equal(result.available, true);
  assert.equal(result.candidate.state.files[0].source, files['main.bend']);
  assert.ok(!result.candidate.state.files[1].source.includes('31337'));
  assert.equal(result.candidate.context.source_bytes, result.candidate.state.files.reduce((n, f) => n + Buffer.byteLength(f.source), 0));
  const both = await composition(root, ['main.bend', 'lib.bend']);
  assert.equal(both.candidate.state.files[1].source, files['lib.bend']);
});
test('composition exact UTF-8 bound fits; one byte over is unavailable and marked', async t => {
  const source = 'import Base\n# λ held out\ndef main(x: U32) -> U32: x\n';
  const root = await fixture(t, { 'main.bend': source });
  const bytes = Buffer.byteLength(source);
  assert.equal((await composition(root, ['main.bend'], bytes)).available, true);
  const over = await composition(root, ['main.bend'], bytes - 1);
  assert.equal(over.available, false);
  assert.ok(over.reasons.includes('composition_byte_limit'));
  assert.equal(over.candidate.context.truncated, true);
  assert.equal(over.candidate.context.source_bytes, bytes);
  assert.deepEqual(over.candidate.state.files, []);
});
test('unused proof-entry chains stay interfaces with no proof body', async t => {
  const root = await fixture(t, { 'main.bend': 'import Base\nimport ./earlier-PROOF.bend as P\ndef main(x: U32) -> U32: x\n',
    'earlier-PROOF.bend': 'import Base\nimport ./LAWS.bend as L\ndef L.identity(x): {==}\n',
    'LAWS.bend': 'import Base\nlaw identity:\n  for x: U32\n  {x == x : U32}\n' });
  const result = await composition(root, ['main.bend']);
  assert.equal(result.available, true);
  assert.equal(result.candidate.state.files.length, 3);
  assert.ok(!result.candidate.state.files.slice(1).some(f => f.source.includes('{==}')));
});
