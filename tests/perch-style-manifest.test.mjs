import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, stat, readdir, symlink } from 'node:fs/promises';
import { gunzipSync } from 'node:zlib';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createBendSourceSnapshot } from '../scripts/perch-bend-context.mjs';
import { config, fixture, legacyEvidence, manifest, provider, run, sources } from './perch-style/manifest-fixture.mjs';

const { runStyleRanking, runStylePreflight } = await import(process.env.KNOT_STYLE_TEST_MODULE ?? '../scripts/perch-style.mjs');

test('compiler manifest covers all source files and closes every local import', async () => {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const compiler = JSON.parse(await readFile(join(root, 'docs/compiler-campaign/manifest.json'), 'utf8'));
  const snapshot = await createBendSourceSnapshot(root);
  const listed = new Set(compiler.groups.flatMap(group => group.files));
  assert.deepEqual([...listed].sort(), (await readdir(join(root, 'src')))
    .filter(file => file.endsWith('.bend')).map(file => `src/${file}`).sort());
  for (const group of compiler.groups) {
    const files = new Set(group.files);
    for (const path of files) {
      const { analysis } = await snapshot.load(path);
      assert.equal(analysis.parser_status, 'parsed');
      for (const ref of analysis.references.filter(ref => ref.kind === 'import'
        && (ref.module.startsWith('./') || ref.module.startsWith('../')))) {
        const dependency = relative(root, resolve(root, dirname(path), ref.module));
        assert.ok(files.has(dependency), `${group.name}: ${path} needs ${dependency}`);
      }
    }
  }
});

test('legacy target and inventory bytes stay pinned without a manifest', async t => {
  const root = await fixture(t);
  const expected = JSON.parse(await readFile(new URL('./perch-style/manifest-legacy.json', import.meta.url), 'utf8'));
  assert.deepEqual(await legacyEvidence(runStyleRanking, root), expected.evidence);
});

test('manifest preflight reports each group and never loads environment or calls a provider', async t => {
  const root = await fixture(t);
  t.mock.method(process, 'loadEnvFile', () => { throw Error('Environment access forbidden'); });
  const p = { requests: [], fetchImpl: async () => { throw Error('Provider access forbidden'); } };
  const { code, report } = await run(runStyleRanking, root, ['--preflight', '--manifest=manifest.json'], p, { loadEnv: true });
  assert.equal(code, 0);
  assert.equal(report.mode, 'manifest');
  assert.equal(report.provider_requests, 0);
  assert.equal(report.summary.groups, 2);
  assert.equal(report.summary.units, 3);
  assert.equal(report.summary.compositions_available, 2);
  assert.equal(report.structural_blockers, 0);
  assert.deepEqual(report.groups.map(g => [g.name, g.summary.units, g.composition.available]),
    [['successor', 2, true], ['primitive', 1, true]]);
  assert.deepEqual(report.groups[0].composition.selected_files, ['z.bend', 'm.bend']);
  await assert.rejects(stat(join(root, '.perch')), { code: 'ENOENT' });
});

test('direct preflight entry stays offline even when manifest flags request live review', async t => {
  const root = await fixture(t), output = [];
  let calls = 0;
  t.mock.method(process, 'loadEnvFile', () => { calls++; throw Error('Environment access forbidden'); });
  t.mock.method(globalThis, 'fetch', async () => { calls++; throw Error('Provider access forbidden'); });
  const options = { root, stdout: text => output.push(text) };
  assert.equal(await runStylePreflight(['--manifest=manifest.json', '--json'], options), 0);
  assert.equal(JSON.parse(output[0]).provider_requests, 0);
  await assert.rejects(runStylePreflight(['--live', '--manifest=manifest.json'], options), /never contacts a provider/);
  assert.equal(calls, 0);
});

test('manifest composition follows reading order then collaborators; declaration requests stay identical', async t => {
  const root = await fixture(t);
  const actual = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--group=successor']);
  assert.equal(actual.code, 0);
  const explicit = await run(runStyleRanking, root, ['--live', '--task=contract.md', 'z.bend', 'm.bend']);
  const decode = result => result.requests.map(text => JSON.parse(text));
  assert.deepEqual(decode(actual).filter(r => r.state.path), decode(explicit).filter(r => r.state.path));
  const composition = decode(actual).filter(r => r.state.files);
  assert.equal(composition.length, 1);
  assert.deepEqual(composition[0].state.files, ['z.bend', 'm.bend', 'a.bend'].map(path => ({ path, source: sources[path] })));
  assert.deepEqual(decode(explicit).find(r => r.state.files).state.files.map(f => f.path), ['a.bend', 'm.bend', 'z.bend']);
  assert.ok(!actual.requests.join('').includes(manifest.groups[0].notes));
});

test('manifest qualification requires every group; passing declarations cannot replace a composition', async t => {
  const root = await fixture(t);
  const good = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json']);
  assert.equal(good.code, 0);
  assert.equal(good.report.qualification.fully_qualified, true);
  assert.equal(good.report.qualification.manifest_fully_qualified, true);
  assert.equal(good.report.summary.groups_qualified, 2);
  assert.equal(good.requests.filter(text => JSON.parse(text).state.files).length, 2);
  const bad = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], provider((request, body) => {
    if (request.state.files?.[0].path === 'a.bend') {
      const answer = body.answers.highly_memetic;
      answer.probabilities[3] = 0; answer.probabilities[0] = 1; answer.score = 0;
    }
  }));
  assert.equal(bad.code, 3);
  assert.equal(bad.report.groups[0].qualification.fully_qualified, true);
  assert.equal(bad.report.groups[1].qualification.fully_qualified, false);
  assert.equal(bad.report.qualification.fully_qualified, false);
});

test('filtered qualification cannot claim the entire manifest', async t => {
  const root = await fixture(t);
  const result = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--group=primitive']);
  assert.equal(result.code, 0);
  assert.deepEqual(result.report.groups.map(g => g.name), ['primitive']);
  assert.equal(result.report.qualification.fully_qualified, true);
  assert.equal(result.report.qualification.manifest_fully_qualified, false);
});

test('later groups cannot hide stale earlier sources', async t => {
  const root = await fixture(t);
  const result = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], provider(async request => {
    if (request.state.files?.[0].path === 'a.bend') await writeFile(join(root, 'z.bend'), sources['z.bend'] + '# changed\n');
  }));
  assert.equal(result.code, 3);
  assert.equal(result.report.qualification.fully_qualified, false);
  assert.deepEqual(result.report.source_freshness.changed_sources, ['z.bend']);
});

test('manifest rejects ambiguous selections and malformed schema before any requests', async t => {
  const root = await fixture(t), p = provider();
  const invoke = args => run(runStyleRanking, root, args, p);
  for (const extra of [['--all'], ['z.bend'], ['--task=contract.md'], ['--cohort=task'],
    ['--manifest=manifest.json'], ['--group='], ['--group=absent'], ['--unknown'],
    ['--group=primitive', '--group=successor'], ['--jobs=0'], ['--incremental', '--fresh']]) {
    await assert.rejects(invoke(['--live', '--manifest=manifest.json', ...extra]));
  }
  await assert.rejects(invoke(['--live', '--group=primitive', 'a.bend']), /Unknown style option/);
  await assert.rejects(invoke(['--live', '--preflight', '--manifest=manifest.json']), /not both/);
  const invalid = [null, [], {}, { schema: 2, groups: manifest.groups }, { schema: 1, groups: [] },
    { ...manifest, typo: true },
    ...[null, { files: ['a.bend'] }, { name: '', files: ['a.bend'] }, { name: 'x', files: [] },
      { name: 'x', files: ['a.bend', './a.bend'] }, { name: 'x', files: ['a.bend::next'] },
      { name: 'x', files: ['a.bend'], notes: {} }, { name: 'x', files: ['a.bend'], task: '' },
      { name: 'x', files: ['a.bend'], contract: 'contract.md' }].map(group => ({ schema: 1, groups: [group] })),
    { schema: 1, groups: [manifest.groups[0], manifest.groups[0]] }];
  for (const value of invalid) {
    await writeFile(join(root, 'manifest.json'), JSON.stringify(value));
    await assert.rejects(invoke(['--live', '--manifest=manifest.json']));
  }
  assert.equal(p.requests.length, 0);
});

test('manifest paths cannot escape the workspace or alias duplicate source files', async t => {
  const outside = await fixture(t), root = await fixture(t), p = provider();
  await symlink(join(outside, 'a.bend'), join(root, 'outside.bend'));
  await symlink(join(root, 'a.bend'), join(root, 'alias.bend'));
  for (const files of [[join(outside, 'a.bend')], ['../outside.bend'], ['outside.bend'], ['a.bend', 'alias.bend']]) {
    await writeFile(join(root, 'manifest.json'), JSON.stringify({ schema: 1, groups: [{ name: 'x', files }] }));
    await assert.rejects(run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], p), /workspace|Duplicate/);
  }
  assert.equal(p.requests.length, 0);
});

test('all selected groups prepare before requests, with a total declaration limit', async t => {
  const root = await fixture(t), p = provider();
  await writeFile(join(root, 'a.bend'), 'import Base\ndef bad( -> U32: 0\n');
  await assert.rejects(run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], p), /does not parse/);
  await writeFile(join(root, 'a.bend'), sources['a.bend']);
  await writeFile(join(root, 'perch-style.json'), JSON.stringify({ ...config, max_units: 2 }));
  await assert.rejects(run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], p), /limited to 2/);
  assert.equal(p.requests.length, 0);
});

test('preflight retains per-group truncation, unresolved imports and composition byte bounds', async t => {
  const popular = ['import Base', 'def core(x: U32) -> U32: x',
    ...[1, 2, 3, 4, 5].map(n => `def use${n}(x: U32) -> U32: core(x)`)].join('\n') + '\n';
  const local = { schema: 1, groups: [
    { name: 'popular', files: ['popular.bend'] }, { name: 'remote', files: ['remote.bend'] },
    { name: 'large', files: ['large.bend'] }] };
  const root = await fixture(t, { 'manifest.json': JSON.stringify(local), 'popular.bend': popular,
    'remote.bend': 'import Base\nimport pkg@1.2.3.4/lib.bend as P\ndef solve(x: U32) -> U32: P.next(x)\n',
    'large.bend': sources['a.bend'] + '# ' + 'x'.repeat(48000) + '\n' });
  const result = await run(runStyleRanking, root, ['--preflight', '--manifest=manifest.json']);
  assert.equal(result.code, 3);
  assert.equal(result.report.structural_blockers, 3);
  assert.deepEqual(result.report.groups.map(g => [g.name, g.summary.truncated_units, g.composition.reasons]),
    [['popular', 1, []], ['remote', 0, ['unresolved_composition_context']], ['large', 0, ['composition_byte_limit']]]);
  assert.equal(result.report.groups[1].summary.supporting_role_impossible, 1);
  assert.deepEqual(result.report.groups[1].composition.unresolved_by_reason, { 'nonlocal-import': 1 });
  assert.ok(result.report.groups.every(g => g.task.reason === 'missing_task_context'));
});

test('notes stay metadata, tasks are group-specific and overlong tasks remain advisory', async t => {
  const root = await fixture(t, { 'second.md': 'Identity on a word.', 'long.md': 'x'.repeat(16001) });
  const groups = structuredClone(manifest.groups);
  groups[1].task = 'second.md';
  await writeFile(join(root, 'manifest.json'), JSON.stringify({ schema: 1, groups }));
  const first = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json']);
  assert.equal(first.code, 0);
  assert.equal(first.report.groups[1].potential_profundity.task.path, 'second.md');
  assert.equal(JSON.parse(first.requests.at(-1)).state.cohort, 'Identity on a word.');
  groups[1].task = 'long.md';
  await writeFile(join(root, 'manifest.json'), JSON.stringify({ schema: 1, groups }));
  const long = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--group=primitive']);
  assert.equal(long.code, 0);
  assert.equal(long.report.groups[0].potential_profundity.task.reason, 'task_byte_limit');
  assert.equal(long.report.groups[0].qualification.potential_advisory, true);
});

test('manifest and task changes invalidate overall qualification', async t => {
  for (const path of ['manifest.json', 'contract.md']) {
    const root = await fixture(t);
    let changed = false;
    const result = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--group=primitive'], provider(async () => {
      if (!changed) {
        changed = true;
        await writeFile(join(root, path), await readFile(join(root, path), 'utf8') + '\n');
      }
    }));
    assert.equal(result.code, 3);
    assert.equal(result.report.qualification.fully_qualified, false);
    assert.ok(result.report.source_freshness.changed_sources.includes(path));
  }
});

test('different resolved models across groups cannot qualify', async t => {
  const root = await fixture(t);
  const result = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], provider((_request, body, count) => {
    if (count > 4) body.model = 'different-model';
  }));
  assert.equal(result.code, 1);
  assert.equal(result.report.failure, 'model_changed_between_groups');
  assert.deepEqual(result.report.groups.map(g => g.qualification.fully_qualified), [true, true]);
  assert.equal(result.report.qualification.fully_qualified, false);
});

test('provider failure stops new groups and persists one aggregate receipt with partial evidence', async t => {
  const root = await fixture(t), p = provider(() => { throw Error('offline transport failure'); });
  const result = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], p);
  assert.equal(result.code, 1);
  assert.equal(result.report.groups.length, 1);
  assert.equal(result.report.groups[0].status, 'failed');
  assert.equal(result.report.summary.groups_completed, 0);
  assert.equal(result.report.failure, 'group_review_failed');
  assert.deepEqual(result.report.skipped_groups, ['primitive']);
  assert.equal(result.requests.length, 1);
  const receipts = await readdir(join(root, '.perch/usage'));
  assert.equal(receipts.length, 1);
  assert.deepEqual(JSON.parse(await readFile(join(root, '.perch/usage', receipts[0]), 'utf8')), result.report);
});

test('pre-dispatch failure in a later group retains earlier evidence', async t => {
  const root = await fixture(t);
  const result = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json'], provider(async request => {
    if (request.state.path === 'm.bend') await writeFile(join(root, 'a.bend'), sources['a.bend'] + '# changed\n');
  }));
  assert.equal(result.code, 1);
  assert.equal(result.report.failure, 'group_dispatch_failed');
  assert.equal(result.report.dispatch_failure.group, 'primitive');
  assert.equal(result.report.groups.length, 1);
  assert.equal(result.report.qualification.fully_qualified, false);
});

test('manifest reuse preserves exact requests and invalidates composition reading order only', async t => {
  const root = await fixture(t);
  const first = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--output=receipt.json.gz']);
  assert.equal(first.code, 0);
  assert.deepEqual(JSON.parse(gunzipSync(await readFile(join(root, 'receipt.json.gz')))), first.report);
  const forbidden = { requests: [], fetchImpl: async () => { throw Error('Unexpected request'); } };
  const warm = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--reuse=receipt.json.gz'], forbidden);
  assert.equal(warm.code, 0);
  assert.equal(warm.report.provider_requests, 0);
  assert.deepEqual(warm.report.groups.map(g => g.reused_units), [2, 1]);
  const reversed = structuredClone(manifest);
  reversed.groups[0].files.reverse();
  await writeFile(join(root, 'manifest.json'), JSON.stringify(reversed));
  const reordered = await run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--reuse=receipt.json.gz']);
  assert.equal(reordered.code, 0);
  assert.equal(reordered.requests.length, 1);
  assert.deepEqual(JSON.parse(reordered.requests[0]).state.files.map(f => f.path), ['m.bend', 'z.bend', 'a.bend']);
});

test('manifest incremental answers remain partitioned by exact task and composition requests', async t => {
  const root = await fixture(t);
  const args = ['--live', '--manifest=manifest.json', '--incremental'];
  assert.equal((await run(runStyleRanking, root, args)).code, 0);
  const warm = await run(runStyleRanking, root, args);
  assert.equal(warm.code, 0);
  assert.equal(warm.report.provider_requests, 0);
  const changed = structuredClone(manifest);
  changed.groups[0].files.reverse();
  await writeFile(join(root, 'manifest.json'), JSON.stringify(changed));
  const reordered = await run(runStyleRanking, root, args);
  assert.equal(reordered.requests.length, 1);
  assert.equal(reordered.code, 0);
});

test('output collisions fail before requests and offline output is reproducible', async t => {
  const root = await fixture(t), p = provider();
  const args = ['--preflight', '--manifest=manifest.json', '--output=preflight.json.gz'];
  const result = await run(runStyleRanking, root, args, p);
  assert.equal(result.code, 0);
  assert.equal(p.requests.length, 0);
  assert.deepEqual(JSON.parse(gunzipSync(await readFile(join(root, 'preflight.json.gz')))), result.report);
  await assert.rejects(run(runStyleRanking, root, ['--live', '--manifest=manifest.json', '--output=preflight.json.gz'], p), /already exists/);
  assert.equal(p.requests.length, 0);
});
