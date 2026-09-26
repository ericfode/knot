import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { runPerch, usageSummary } from '../scripts/perch-workflow.mjs';

test('actual Perch CLI retains useful evidence without treating blockers or zero coverage as passes', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-workflow-'));
  const originalFetch = globalThis.fetch;
  let calls = 0, verdict = 1, denied = false;
  const secret = 'fixture-credential-never-write-to-receipts';
  try {
    await mkdir(join(root, 'src'));
    await writeFile(join(root, 'src/probe.bend'), 'import Base\n\ndef main() -> U32:\n  42\n');
    await writeFile(join(root, 'note.md'), '# No applicable rules\n');
    await writeFile(join(root, 'perch.yaml'), 'rules:\n  - name: probe\n    where: "**/*.bend"\n    each: file\n    min: 80\n    gate: false\n    ensure: This is a wiring fixture.\n');
    const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
    git(['init', '-q', '-b', 'main']);
    git(['add', '.']);
    git(['-c', 'user.name=Workflow test', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture']);
    globalThis.fetch = async (_url, options) => {
      calls++;
      if (denied) return { ok: false, status: 401, text: async () => secret };
      const body = JSON.parse(options.body);
      const reply = { model: 'offline-fixture', usage: { input_tokens: 100, output_tokens: 10 }, answers:
        Object.fromEntries(Object.keys(body.questions).map(name => [name, { noul: verdict }])) };
      return { ok: true, json: async () => reply, clone: () => ({ json: async () => reply }) };
    };
    const run = (args, env = { PERCH_API_KEY: secret }) => runPerch(args, {
      root, env, stdout: () => {}, stderr: () => {},
    });
    const check = ['check', 'src/probe.bend', '--rules', 'probe'];
    assert.equal(await run(check), 0);
    assert.equal(calls, 1);
    verdict = 0;
    assert.equal(await run(check), 3);
    assert.equal(calls, 2);
    assert.equal(await run(['check', 'note.md', '--rules', 'probe']), 1);
    assert.equal(calls, 2, 'zero coverage does not contact the provider');
    assert.equal(await run(check, {}), 1);
    assert.equal(calls, 2, 'missing credentials do not contact the provider');
    denied = true;
    assert.equal(await run(check), 1);
    assert.equal(calls, 3, 'authorization failure does not retry');
    assert.equal(await run(['scan', '--since', 'HEAD']), 0);
    assert.equal(calls, 3, 'an unchanged scan does not contact the provider');
    const names = await readdir(join(root, '.perch/usage'));
    assert.equal(names.length, 6);
    const raw = await Promise.all(names.map(name => readFile(join(root, '.perch/usage', name), 'utf8')));
    assert.ok(raw.every(text => !text.includes(secret)));
    assert.ok(raw.every(text => !text.includes('def main()')));
    const records = raw.map(JSON.parse);
    assert.deepEqual(records.map(r => r.status).sort(), ['completed', 'failed', 'findings', 'missing-key', 'no-coverage', 'unchanged']);
    const reported = records.find(r => r.status === 'findings');
    assert.equal(reported.checked, 1);
    assert.equal(reported.findings[0].rule, 'probe');
    assert.equal(reported.findings[0].probability, 1);
    assert.equal(reported.source_sha256.length, 64);
    assert.equal(reported.rules_sha256.length, 64);
    assert.deepEqual(reported.selected_rules, ['probe']);
    assert.equal(reported.resolved_model, 'offline-fixture');
    assert.equal(reported.provider_requests, 1);
    assert.equal(reported.answers[0].probability_true, 0);
    assert.equal(reported.usage.input_tokens, 100);
    const summary = await usageSummary(root);
    assert.equal(summary.receipts, 6);
    assert.equal(summary.statuses['missing-key'], 1);
    assert.equal(summary.findings.probe, 1);
    assert.equal(summary.malformed, 0);
    denied = false;
    verdict = 'not-a-probability';
    assert.equal(await run(check), 1, 'a malformed noul must not become a clean result');
  } finally {
    globalThis.fetch = originalFetch;
    await rm(root, { recursive: true, force: true });
  }
});
