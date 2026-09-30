import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, readdir, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyzeBendSource } from '../scripts/perch-bend.mjs';
const { createPackageStore, declarationInterface, buildInterface, createInterfaceReview, prepareInterfaceComposition, fitInterfaceContext } =
  await import(process.env.KNOT_CONTEXT_TEST_MODULE ?? '../scripts/perch-context-interfaces.mjs');
import { bendDeclarationSource, createBendSourceSnapshot } from '../scripts/perch-bend-context.mjs';
import { prepareStyleTargets } from '../scripts/perch-style.mjs';
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
    assert.deepEqual(found.provenance.map(f => f.path), [`${id}/LICENSE`, `${id}/lib.bend`]);
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

const reviewExpect = JSON.parse(await readFile(new URL('./perch-context/review-expectations.json', import.meta.url), 'utf8'));
const signatures = await readFile(new URL('./perch-context/fixtures/signatures.bend', import.meta.url), 'utf8');
test('parser-delimited heads preserve chars and dependent binders without body text', async () => {
  const analysis = await analyzeBendSource(signatures);
  assert.equal(analysis.parser_status, 'parsed');
  for (const [name, expected] of Object.entries(reviewExpect.heads)) {
    const decl = analysis.declarations.find(d => d.name === name);
    assert.equal(declarationInterface(signatures, decl), expected + ' # interface: body omitted', name);
    const start = decl.location.start.byte, end = decl.body_start?.byte;
    assert.equal(end, start + Buffer.byteLength(expected), name + ': parser body offset');
  }
});
test('interface heads parse back with holes and retain every declaration name', async t => {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  const pending = (await readdir(join(root, 'src'))).filter(p => p.endsWith('.bend')).map(p => `src/${p}`);
  pending.push('tests/perch-context/fixtures/signatures.bend');
  const seen = new Set();
  let heads = 0;
  const names = analysis => [...analysis.declarations.map(d => d.name), ...analysis.datatype_declarations.map(d => d.name)].sort();
  while (pending.length) {
    const path = pending.shift();
    if (seen.has(path)) continue;
    seen.add(path);
    const file = await snapshot.load(path);
    assert.equal(file.analysis.parser_status, 'parsed', path);
    const text = buildInterface(path, file).replaceAll(' # interface: body omitted', ' ?h');
    const parsed = await analyzeBendSource(text);
    assert.equal(parsed.parser_status, 'parsed', `${path}: ${parsed.parser_message}`);
    assert.deepEqual(names(parsed), names(file.analysis), path);
    heads += file.analysis.declarations.length;
    for (const ref of file.analysis.references.filter(r => r.kind === 'import' && r.module !== 'Base')) {
      const dep = await snapshot.resolveImport(path, ref.module);
      assert.equal(dep.reason, undefined, `${path}: ${ref.module}`);
      pending.push(dep.path);
    }
  }
  t.diagnostic(`parse-back oracle: ${seen.size} files; ${heads} definition/law heads`);
});
test('interface instruction retains the complete legacy anti-anchoring clause', async t => {
  const root = await fixture(t, { 'main.bend': 'import Base\ndef main(x: U32) -> U32: x\n' });
  const { candidate } = await composition(root, ['main.bend']);
  assert.ok(candidate.state.instruction.startsWith(reviewExpect.legacy_instruction));
  assert.ok(candidate.state.instruction.endsWith('Do not infer collaborator implementations or checked proofs from signatures.'));
});
test('dependent signature dependencies enter the interface closure', async t => {
  const root = await fixture(t, { 'lib.bend': signatures,
    'main.bend': 'import Base\nimport ./lib.bend as L\ndef main(+n: U32) -> U32: x = L.pair(n); n\n' });
  const result = await composition(root, ['main.bend']);
  assert.equal(result.available, true);
  const source = result.candidate.state.files.find(f => f.path === 'lib.bend').source;
  assert.ok(source.includes(reviewExpect.heads.pair));
  assert.ok(source.includes('def width(n: U32) -> U32: # interface: body omitted'));
  assert.ok(!source.includes('90210'));
  assert.ok(!source.includes('31337'));
});
test('package identity and composition state are independent of checkout and store location', async t => {
  const first = await packageFixture(t);
  const other = await fixture(t, Object.fromEntries(Object.entries(payload).map(([p, s]) =>
    [`a-much-longer-store-location/${first.id}/${p}`, s])));
  const stores = [join(first.root, 'store'), join(other, 'a-much-longer-store-location')];
  const results = [];
  for (let i = 0; i < stores.length; i++) {
    const root = await fixture(t, { 'main.bend': `import Base\nimport ${first.id}/lib.bend as L\ndef main(x: U32) -> U32: L.next(x)\n` });
    const store = await createPackageStore(root, stores[i]), found = await store.resolve(`${first.id}/lib.bend`);
    assert.equal(found.path, `${first.id}/lib.bend`);
    assert.deepEqual(found.provenance.map(f => f.path), [`${first.id}/LICENSE`, `${first.id}/lib.bend`]);
    const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1', packageStore: stores[i] });
    const result = await prepareInterfaceComposition(['main.bend'], null, config, root, snapshot, new Set(['U32']));
    assert.equal(result.available, true);
    assert.ok(!JSON.stringify(result.candidate).includes(stores[i]));
    const units = await prepareStyleTargets(['main.bend'], null, config, root, snapshot);
    assert.ok(!JSON.stringify(units).includes(stores[i]));
    results.push({ ...result.candidate, units });
  }
  assert.equal(results[0].context.source_bytes, results[1].context.source_bytes);
  assert.equal(results[0].state_sha256, results[1].state_sha256);
  assert.deepEqual(results[0].units.map(u => [u.context.source_bytes, u.state_sha256]),
    results[1].units.map(u => [u.context.source_bytes, u.state_sha256]));
  assert.deepEqual(results[0], results[1]);
});
test('package provenance is the verified membership in either store layout', async t => {
  const found = [];
  for (const mode of ['hash', 'release']) {
    const { root, id } = await packageFixture(t, payload, mode);
    const store = await createPackageStore(root, join(root, 'store'));
    found.push(await store.resolve(`${id}/lib.bend`));
  }
  assert.deepEqual(found[0].provenance, found[1].provenance);
});
test('default candidate store verifies BEND_LIB without an explicit option', async t => {
  const { root, id } = await packageFixture(t);
  const previous = process.env.BEND_LIB;
  try {
    process.env.BEND_LIB = join(root, 'store');
    const store = await createPackageStore(root);
    assert.equal((await store.resolve(`${id}/lib.bend`)).path, `${id}/lib.bend`);
  } finally {
    if (previous === undefined) delete process.env.BEND_LIB; else process.env.BEND_LIB = previous;
  }
});

// Encoded-state fitting: the names-only tier, driven at a small computed cap. Each witness calls the module
// the mutant harness swaps in and fails by assertion, never by a bare thrown Error. The oracle below states
// the contract (tests/perch-context/CONTRACT.md, items 10 to 14) independently of the tool.
const enc = value => Buffer.byteLength(JSON.stringify(value));
const byCode = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const REASON = 'context-state-names-only';
const label = item => `${item.path}::${item.name}`;
const parameters = count => Array.from({ length: count }, (_, i) => `p${i}: U32`).join(', ');
async function reviewed(root, name, limits = {}, cohort = 'the fixed contract') {
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  const file = await snapshot.load('main.bend');
  const context = await (await createInterfaceReview({ root, path: 'main.bend', ...file, snapshot, limits })).forUnit(name);
  const decl = file.analysis.declarations.find(d => d.qualified_name === name);
  const prefix = { cohort, name, path: 'main.bend', declaration_kind: decl.syntax_kind, source: bendDeclarationSource(file.source, decl) };
  return { context, snapshot, prefix };
}
const stateOf = ({ prefix, context }) => ({ ...prefix, ...context.seen });
const collaborators = state => [...state.calls, ...state.called_by];
const supplied = state => ['calls', 'called_by', 'laws', 'datatypes'].reduce((n, list) =>
  n + state[list].reduce((sum, item) => sum + Buffer.byteLength(item.source ?? ''), 0), Buffer.byteLength(state.source));
/** Cuttable entries, largest encoded saving first, then path, then name. */
function ranked(state) {
  const rows = state.context_notes.summarized;
  return collaborators(state).map(item => {
    const cut = { path: item.path, name: item.name, representation: 'names-only' };
    const row = { path: item.path, name: item.name, reason: REASON };
    const old = rows.find(r => r.path === item.path && r.name === item.name);
    return { item, saving: enc(item) - enc(cut) - (old ? enc(row) - enc(old) : enc(row) + 1) };
  }).filter(entry => entry.saving > 0)
    .sort((a, b) => b.saving - a.saving || byCode(a.item.path, b.item.path) || byCode(a.item.name, b.item.name));
}
/** The state after the first `count` cuts, built from a copy taken before fitting. */
function afterCuts(state, order, count, note) {
  const expected = structuredClone(state), notes = expected.context_notes;
  for (const { item } of order.slice(0, count)) {
    const entry = collaborators(expected).find(e => e.path === item.path && e.name === item.name);
    notes.source_bytes -= Buffer.byteLength(entry.source);
    for (const key of ['line', 'end_line', 'source']) delete entry[key];
    entry.representation = 'names-only';
    const row = notes.summarized.find(r => r.path === item.path && r.name === item.name);
    if (row) row.reason = REASON; else notes.summarized.push({ path: item.path, name: item.name, reason: REASON });
  }
  notes.summarized.sort((a, b) => byCode(a.path, b.path) || byCode(a.name, b.name));
  if (count) notes.names_only = { count, note };
  return expected;
}
// Two files, equal-size heads in both (Pa and pa differ only in case), and a main that names them out of size,
// path and name order. Code-point order puts Pa before pa; the collation of most locales puts pa first.
const cutFiles = {
  'a.bend': `import Base\ndef pa(x: U32) -> U32: x\ndef pb(x: U32) -> U32: x\ndef Pa(x: U32) -> U32: x\n`,
  'b.bend': `import Base\ndef pa(x: U32) -> U32: x\ndef big(x: U32, y: U32, z: U32) -> U32: x\n`,
  'main.bend': 'import Base\nimport ./a.bend as A\nimport ./b.bend as B\ndef small(x: U32) -> U32: x\n'
    + 'def main(x: U32) -> U32: A.pb(B.pa(small(A.pa(A.Pa(B.big(x, x, x))))))\n',
};
test('names-only tier fits a state the interface tier cannot and marks every cut', async t => {
  const wide = ['ha', 'hb', 'hc', 'hd', 'he'];
  const root = await fixture(t, { 'main.bend': `import Base\n${wide.map(n => `def ${n}(${parameters(12)}) -> U32: p0\n`).join('')}`
    + 'def main(x: U32) -> U32: ha(hb(hc(hd(he(x)))))\n' });
  const { context, snapshot, prefix } = await reviewed(root, 'main', { helpers: 0 });
  const before = structuredClone(stateOf({ prefix, context })), files = structuredClone(context.provenance.files);
  const cap = enc(before) - 300;
  assert.ok(collaborators(before).every(e => e.representation === 'interface'), 'every collaborator is already an interface summary');
  await assert.doesNotReject(fitInterfaceContext(context, snapshot, prefix, cap));
  const state = stateOf({ prefix, context }), cut = collaborators(state).filter(e => e.representation === 'names-only');
  assert.ok(enc(state) <= cap);
  assert.ok(cut.length >= 1 && cut.length < collaborators(state).length, 'some, not all, collaborators are cut');
  for (const entry of cut) assert.deepEqual(Object.keys(entry), ['path', 'name', 'representation']);
  const marker = state.context_notes.names_only;
  assert.ok(marker, 'the judge-visible state says which context was cut to names');
  assert.equal(marker.count, cut.length);
  assert.match(marker.note, /names-only/);
  const rows = state.context_notes.summarized;
  assert.equal(rows, context.provenance.summarized, 'the judge sees the recorded rows');
  assert.equal(rows.length, before.context_notes.summarized.length, 'one row per summarized declaration');
  for (const entry of collaborators(state)) {
    const own = rows.filter(r => r.path === entry.path && r.name === entry.name);
    assert.equal(own.length, 1);
    if (entry.representation === 'names-only') assert.equal(own[0].reason, REASON);
    else assert.deepEqual(entry, collaborators(before).find(e => e.path === entry.path && e.name === entry.name));
  }
  assert.equal(context.provenance.truncated, false);
  assert.equal(state.context_notes.truncated, false);
  assert.deepEqual(context.provenance.files, files, 'the files behind the names stay hash-pinned');
  assert.equal(prefix.source, before.source);
  assert.equal(prefix.cohort, before.cohort);
  for (const list of ['laws', 'datatypes', 'imports']) assert.deepEqual(state[list], before[list]);
  assert.equal(context.provenance.source_bytes, state.context_notes.source_bytes);
  assert.equal(context.provenance.source_bytes, supplied(state));
});
test('names-only tier never shortens the primary source or the task', async t => {
  const bulk = '# ' + 'x'.repeat(3000) + '\n';
  const root = await fixture(t, { 'main.bend': `import Base\ndef help(x: U32, y: U32) -> U32: x\n${bulk}def main(x: U32) -> U32: help(x, x)\n` });
  const { context, snapshot, prefix } = await reviewed(root, 'main', { helpers: 0 }, 'c'.repeat(500));
  const primary = prefix.source, task = prefix.cohort;
  assert.ok(Buffer.byteLength(primary) > 2000);
  await assert.rejects(fitInterfaceContext(context, snapshot, prefix, 2000),
    /after names-only summaries: \d+ of 2000 bytes remain: primary source \d+, task 502, collaborator list \d+ \(1 of 1 entries names-only\)/);
  assert.equal(prefix.source, primary);
  assert.equal(prefix.cohort, task);
  const alone = await reviewed(root, 'main', { helpers: 0 }, 'c'.repeat(4000));
  await assert.rejects(fitInterfaceContext(alone.context, alone.snapshot, alone.prefix, 5000), /after names-only summaries/);
});
test('names-only cuts follow largest saving, then path, then name', async t => {
  const root = await fixture(t, cutFiles);
  const probe = await reviewed(root, 'main', { helpers: 0 });
  await fitInterfaceContext(probe.context, probe.snapshot, probe.prefix, enc(stateOf(probe)) - 1);
  const { note } = stateOf(probe).context_notes.names_only;
  assert.equal(typeof note, 'string');
  const target = await reviewed(root, 'main', { helpers: 0 });
  const before = structuredClone(stateOf(target)), order = ranked(before);
  assert.deepEqual(order.map(e => label(e.item)), ['b.bend::big', 'main.bend::small', 'a.bend::Pa', 'a.bend::pa', 'a.bend::pb', 'b.bend::pa']);
  assert.deepEqual(before.calls.filter(e => /^p/i.test(e.name)).map(label), ['a.bend::pb', 'b.bend::pa', 'a.bend::pa', 'a.bend::Pa'],
    'the equal-size entries were filled in an order that is neither path nor name order');
  assert.equal(order[2].saving, order[5].saving, 'four equal savings, cut only the first of them');
  const expected = afterCuts(before, order, 3, note), cap = enc(expected);
  assert.ok(enc(afterCuts(before, order, 2, note)) > cap);
  await assert.doesNotReject(fitInterfaceContext(target.context, target.snapshot, target.prefix, cap));
  assert.deepEqual(stateOf(target), expected);
  assert.equal(JSON.stringify(stateOf(target)), JSON.stringify(expected));
});
test('names-only tier also cuts a body the interface tier kept, adding its row', async t => {
  const names = ['ka', 'kb', 'kc'];
  const root = await fixture(t, { 'main.bend': `import Base\n${names.map(n => `def ${n}(${parameters(12)}) -> U32: p0\n`).join('')}`
    + 'def main(x: U32) -> U32: ka(kb(kc(x)))\n' });
  const probe = await reviewed(root, 'main');
  const before = structuredClone(stateOf(probe));
  assert.deepEqual(collaborators(before).map(e => e.representation), ['full', 'full', 'full']);
  assert.equal(before.context_notes.summarized.length, 0, 'a kept body has no summary row yet');
  const order = ranked(before);
  assert.equal(order.length, 3);
  await fitInterfaceContext(probe.context, probe.snapshot, probe.prefix, enc(before) - 1);
  const { note } = stateOf(probe).context_notes.names_only;
  const target = await reviewed(root, 'main'), expected = afterCuts(before, order, 3, note), cap = enc(expected);
  assert.ok(enc(afterCuts(before, order, 2, note)) > cap, 'all three cuts are needed');
  await assert.doesNotReject(fitInterfaceContext(target.context, target.snapshot, target.prefix, cap));
  assert.deepEqual(stateOf(target), expected);
  assert.deepEqual(target.context.provenance.summarized.map(r => r.reason), [REASON, REASON, REASON]);
  assert.equal(target.context.provenance.source_bytes, supplied(stateOf(target)));
});
