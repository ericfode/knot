#!/usr/bin/env node
// Offline counterfactual: memoize rules for one immutable check invocation.
// After the throughput fix, both variants should already load rules only once.
// Instrument a disposable copy of the pinned bundle, never the installed CLI.
import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import { readFile, writeFile, unlink } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { performance } from 'node:perf_hooks';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const target = 'packages/source/main.bend';
const rules = 'perf-growing-prefix-copy,perf-loop-invariant-work,perf-linked-list-indexing,perf-amortized-growth';
const output = process.argv[2];
if (!output) throw new Error('Supply a new output JSON path');
await writeFile(resolve(output), '', { flag: 'wx', mode: 0o600 });
const bundle = resolve(root, 'node_modules/@lakeday/perch/dist/cli.mjs');
const scratch = resolve(dirname(bundle), `latency-probe-${randomUUID()}.mjs`);
const source = await readFile(bundle, 'utf8');
const sha = text => createHash('sha256').update(text).digest('hex');
const round = number => Math.round(number * 100) / 100;
assert.ok(source.startsWith('// Knot Bend parser integration v1'));
const appended = `
let probe, memo;
export function beginRuleProbe(cache) {
  memo = new Map();
  probe = { cache, readRules: { calls: 0, loads: 0, ms: 0 }, readRuleFiles: { calls: 0, ms: 0 }, listTree: { calls: 0, ms: 0 } };
  return probe;
}
const actualReadRules = readRules, actualReadRuleFiles = readRuleFiles, actualListTree = listTree;
readRules = async function(root, revision) {
  probe.readRules.calls++;
  const key = JSON.stringify([root, revision]);
  if (probe.cache && memo.has(key)) return memo.get(key);
  const start = performance.now();
  const result = await actualReadRules(root, revision);
  probe.readRules.loads++;
  probe.readRules.ms += performance.now() - start;
  if (probe.cache) memo.set(key, result);
  return result;
};
readRuleFiles = async function(...args) {
  const start = performance.now(); probe.readRuleFiles.calls++;
  try { return await actualReadRuleFiles(...args); }
  finally { probe.readRuleFiles.ms += performance.now() - start; }
};
listTree = async function(...args) {
  const start = performance.now(); probe.listTree.calls++;
  try { return await actualListTree(...args); }
  finally { probe.listTree.ms += performance.now() - start; }
};
`;
const originalFetch = globalThis.fetch, previous = process.cwd();
try {
  await writeFile(scratch, source + appended, { flag: 'wx', mode: 0o600 });
  const { main, beginRuleProbe } = await import(pathToFileURL(scratch));
  process.chdir(root);
  const runs = [];
  for (const cache of [false, true, false, true]) {
    const timing = beginRuleProbe(cache), requests = [];
    let result, diagnostics = 0;
    globalThis.fetch = async (_url, init) => {
      requests.push(sha(init.body));
      const body = JSON.parse(init.body);
      assert.ok(Object.values(body.questions).every(q => q.type === 'noul'));
      return new Response(JSON.stringify({ model: 'offline-rule-loading-probe', answers:
        Object.fromEntries(Object.keys(body.questions).map(key => [key, { noul: 1 }])) }));
    };
    const start = performance.now();
    const exit = await main(['check', target, '--rules', rules, '--parallel', '1', '--json'], {
      env: { PERCH_API_KEY: 'offline-rule-loading-probe' },
      stdout: text => { result = JSON.parse(text); }, stderr: () => { diagnostics++; },
    });
    assert.equal(exit, 0);
    runs.push({ cache, wall_ms: round(performance.now() - start), checked: result.checked,
      units: result.units.length, request_count: requests.length,
      request_sequence_sha256: sha(JSON.stringify(requests)), result_sha256: sha(JSON.stringify(result)),
      diagnostics, timing });
    assert.equal(runs.at(-1).request_sequence_sha256, runs[0].request_sequence_sha256);
    assert.equal(runs.at(-1).result_sha256, runs[0].result_sha256);
    console.log(JSON.stringify(runs.at(-1)));
  }
  await writeFile(resolve(previous, output), JSON.stringify({ schema: 1, at: new Date().toISOString(),
    target, rules, bundle_sha256: sha(source), source_sha256: sha(await readFile(target)),
    script_sha256: sha(await readFile(fileURLToPath(import.meta.url))), runs,
    note: 'Offline fixed responses. A disposable bundle copy wraps rule loading, with command-local memoization as a counterfactual. Alternating runs have identical request sequences and complete results. Function times are nested, not additive. This is not a shipped cache or proof under concurrent rule edits.' }, null, 2) + '\n', { mode: 0o600 });
} finally {
  globalThis.fetch = originalFetch;
  process.chdir(previous);
  await unlink(scratch).catch(error => { if (error.code !== 'ENOENT') throw error; });
}
