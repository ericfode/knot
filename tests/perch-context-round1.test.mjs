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
