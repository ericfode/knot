import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createBendSourceSnapshot, bendDeclarationSource } from '../scripts/perch-bend-context.mjs';
import { prepareStyleTargets, assessStyleRole, runStylePreflight } from '../scripts/perch-style.mjs';

const moduleURL = process.env.KNOT_CONTEXT_TEST_MODULE ?? new URL('../scripts/perch-context-interfaces.mjs', import.meta.url).href;
const { createInterfaceReview, fitInterfaceContext } = await import(moduleURL);
const expect = JSON.parse(await readFile(new URL('./perch-context/round1-expectations.json', import.meta.url), 'utf8'));
const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
const project = fileURLToPath(new URL('../', import.meta.url));
const enc = value => Buffer.byteLength(JSON.stringify(value));
const sha = value => createHash('sha256').update(value).digest('hex');
const stateOf = f => ({ ...f.prefix, ...f.context.seen });
async function fixture(t, source, path = 'main.bend') {
  const root = await mkdtemp(join(tmpdir(), 'perch-cap-round1-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, path), source);
  return root;
}
function seed(root, path = 'main.bend') {
  assert.equal(execFileSync('bun', [join(project, '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'),
    join(root, path), '--check-only'], { env: { ...process.env, BEND_NO_TELEMETRY: '1' }, encoding: 'utf8' }).trim(), 'All terms check.');
}

test(expect.controls[0], async t => {
  const params = Array.from({ length: 30 }, (_, i) => `p${i}: U32`).join(', ');
  const literals = Array(29).fill('(0 : U32)');
  const inner = ['x', ...literals].join(', '), outer = [`pa(${inner})`, ...literals].join(', ');
  const pad = '# ' + 'b'.repeat(1000) + '\n';
  const source = 'import Base\n' + pad + `def Pa(${params}) -> U32: p0\n`
    + pad + `def pa(${params}) -> U32: p0\n` + `def target(x: U32) -> U32: Pa(${outer})\n`;
  const root = await fixture(t, source, 'probe.bend'), cohort = 'x'.repeat(58293);
  seed(root, 'probe.bend');
  const driver = `
    process.loadEnvFile = () => { throw new Error('environment forbidden'); };
    globalThis.fetch = () => { throw new Error('network forbidden'); };
    const { createBendSourceSnapshot, bendDeclarationSource } = await import(${JSON.stringify(new URL('../scripts/perch-bend-context.mjs', import.meta.url).href)});
    const { createInterfaceReview, fitInterfaceContext } = await import(${JSON.stringify(moduleURL)});
    const snapshot = await createBendSourceSnapshot(process.cwd(), { contextPolicy: 'interfaces-v1' });
    const file = await snapshot.load('probe.bend');
    const context = await (await createInterfaceReview({ root: process.cwd(), path: 'probe.bend', ...file, snapshot })).forUnit('target');
    const decl = file.analysis.declarations.find(d => d.qualified_name === 'target');
    const prefix = { cohort: 'x'.repeat(58293), name: 'target', path: 'probe.bend', declaration_kind: decl.syntax_kind,
      source: bendDeclarationSource(file.source, decl) };
    await fitInterfaceContext(context, snapshot, prefix);
    console.log(JSON.stringify({ ...prefix, ...context.seen }));`;
  const states = expect.locales.map(locale => {
    const env = { ...process.env, BEND_NO_TELEMETRY: '1', LANG: locale, LC_ALL: locale };
    delete env.NODE_TEST_CONTEXT;
    const result = spawnSync(process.execPath, ['--input-type=module', '-e', driver], { cwd: root, env, encoding: 'utf8', timeout: 30000 });
    assert.equal(result.error, undefined);
    assert.equal(result.status, 0, result.stderr);
    return JSON.parse(result.stdout);
  });
  assert.equal(enc(states[0]), 59829);
  assert.deepEqual(states[0].context_notes.summarized.map(r => r.name), ['Pa', 'pa']);
  assert.equal(JSON.stringify(states[0]), JSON.stringify(states[1]), 'complete encoded state, not just cut names');
  assert.equal(sha(JSON.stringify(states[0])), 'a3713c8ccedd645eee88edd3620dc032ee1c7b5d3d616d7247c7df46a5dc9d7c');
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: 'interfaces-v1' });
  const [candidate] = await prepareStyleTargets(['probe.bend::target'], cohort, config, root, snapshot);
  assert.equal(candidate.state_sha256, sha(JSON.stringify(states[0])), 'production hashes the same complete state');
});

const noLoad = { load() { throw new Error('interface-only witness must not load a body'); } };
const marker = { count: 1, note: 'Cut to qualified names by the encoded-state cap: an entry marked names-only shows no signature and no body. Do not infer its type, contract or behavior from the name.' };
const item = (path, name, source) => ({ path, name, line: 1, end_line: 3, source, representation: 'interface' });
function assembled(items, source = 'p'.repeat(500), cohort = 'Frozen independent task.') {
  const summarized = items.map(({ path, name }) => ({ path, name, reason: 'context-state-interface' }));
  const source_bytes = Buffer.byteLength(source) + items.reduce((n, entry) => n + Buffer.byteLength(entry.source), 0);
  const unresolved = [], provenance = { summarized, unresolved, source_bytes, truncated: false,
    files: items.map(({ path }) => ({ path, source_sha256: 'a'.repeat(64) })) };
  return { prefix: { path: 'main.bend', name: 'main', declaration_kind: 'bend_definition', source, cohort },
    context: { provenance, seen: { calls: items, called_by: [], laws: [], datatypes: [], imports: [],
      context_notes: { summarized, unresolved, source_bytes, truncated: false } } } };
}
// Independent whole-state projection; savings are measured by serializing the result, not by
// repeating the production formula. Both fields and warning text are fixed by the contract.
function named(f, index) {
  const result = structuredClone(f), entry = result.context.seen.calls[index];
  result.context.provenance.source_bytes -= Buffer.byteLength(entry.source);
  result.context.seen.context_notes.source_bytes = result.context.provenance.source_bytes;
  result.context.seen.calls[index] = { path: entry.path, name: entry.name, representation: 'names-only' };
  result.context.provenance.summarized[index].reason = 'context-state-names-only';
  result.context.seen.context_notes.names_only = marker;
  return result;
}
test(expect.controls[1], async () => {
  const a = 'def a(x:\n  # ' + '"'.repeat(200) + '\n  U32) -> U32: # interface: body omitted';
  const b = 'def b(x:\n  # ' + 'x'.repeat(400) + '\n  U32) -> U32: # interface: body omitted';
  const primary = '# ' + 'p'.repeat(10001 - Buffer.byteLength(b) - 2);
  const f = assembled([item('a.bend', 'a', a), item('b.bend', 'b', b)], primary);
  assert.equal(f.context.provenance.source_bytes - Buffer.byteLength(a), 10001);
  const cutA = enc(stateOf(named(f, 0))), cutB = enc(stateOf(named(f, 1)));
  assert.equal(cutA, cutB + 1, 'only the byte counter makes b the larger saving');
  await assert.doesNotReject(fitInterfaceContext(f.context, noLoad, f.prefix, cutB));
  assert.deepEqual(f.context.seen.calls.filter(e => e.representation === 'names-only').map(e => e.name), ['b']);
  assert.equal(enc(stateOf(f)), cutB, 'one cut fits exactly; a keeps its signature');

  // A first large cut changes 10,xxx source bytes to 1,xxx. Recompute: neither remaining
  // cut now crosses a digit boundary, so the equal savings use the path tie-break.
  const later = assembled([item('0.bend', 'first', 'x'.repeat(8500)), item('a.bend', 'a', a), item('b.bend', 'b', b)],
    'p'.repeat(1501 - Buffer.byteLength(b)));
  assert.equal(enc(stateOf(named(later, 1))), enc(stateOf(named(later, 2))) + 1);
  const afterFirst = named(later, 0);
  assert.equal(enc(stateOf(named(afterFirst, 1))), enc(stateOf(named(afterFirst, 2))), 'rank changes after the first cut');
  const afterBoth = named(afterFirst, 1);
  afterBoth.context.seen.context_notes.names_only = { ...marker, count: 2 };
  const cap = enc(stateOf(afterBoth));
  assert.ok(enc(stateOf(afterFirst)) > cap);
  await assert.doesNotReject(fitInterfaceContext(later.context, noLoad, later.prefix, cap));
  assert.deepEqual(later.context.seen.calls.filter(e => e.representation === 'names-only').map(e => e.name), ['first', 'a']);
});
test(expect.controls[2], async () => {
  const f = assembled([item('\u{10000}.bend', 'one', 'x'.repeat(500)), item('\ue000.bend', 'two', 'x'.repeat(500))]);
  const cap = Math.max(enc(stateOf(named(f, 0))), enc(stateOf(named(f, 1))));
  await assert.doesNotReject(fitInterfaceContext(f.context, noLoad, f.prefix, cap));
  assert.deepEqual(f.context.seen.calls.filter(e => e.representation === 'names-only').map(e => e.path), ['\ue000.bend']);
});
