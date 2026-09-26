import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { main } from '../node_modules/@lakeday/perch/dist/cli.mjs';

test('all source rules select actual Bend declarations; packet rules keep file scope', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'knot-source-rules-'));
  const previous = process.cwd(), realFetch = globalThis.fetch;
  const calls = [];
  try {
    await mkdir(join(dir, '.perch'), { recursive: true });
    await cp(new URL('../.perch/rules', import.meta.url), join(dir, '.perch/rules'), { recursive: true });
    await writeFile(join(dir, 'perch.yaml'), 'rules: []\n');
    await mkdir(join(dir, 'src'));
    await writeFile(join(dir, 'src/probe.bend'), 'import Base\n\ndef helper(x: U32) -> U32:\n  U32.add(x,1)\n\ndef solve(x: U32) -> U32:\n  helper(x)\n');
    process.chdir(dir);
    const git = args => execFileSync('git', args, { stdio: 'ignore' });
    git(['init', '-q', '-b', 'main']); git(['add', '.']);
    git(['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture']);
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); calls.push(body);
      return { ok: true, json: async () => ({ model: 'offline-wiring-only',
        answers: Object.fromEntries(Object.keys(body.questions).map(key => [key, { noul: 1 }])) }) };
    };
    const run = async args => {
      const output = [], errors = [];
      const exit = await main(args, { env: { PERCH_API_KEY: 'offline-wiring-only' },
        stdout: s => output.push(s), stderr: s => errors.push(s) });
      assert.equal(exit, 0, errors.join('\n'));
      return JSON.parse(output.join('\n'));
    };
    const rules = (await run(['rules', 'list', '--json'])).filter(r => r.from !== 'perch');
    const source = rules.filter(r => /^(bend-|compiler-|perf-)/.test(r.name));
    assert.equal(source.length, 13);
    assert.ok(source.every(r => r.each === 'method'));
    assert.ok(rules.filter(r => !source.includes(r)).every(r => r.each === 'file'));
    const result = await run(['check', 'src/probe.bend', '--rules', source.map(r => r.name).join(','), '--json']);
    assert.equal(result.checked, 26);
    assert.deepEqual(result.units.map(u => u.name).sort(), ['helper', 'solve']);
    assert.equal(calls.length, 2);
    assert.ok(calls.every(c => Object.keys(c.questions).length === 13));
    assert.ok(result.units.every(u => u.checked === 13));
    assert.ok(result.units.every(u => u.context.files.length > 0));
    assert.equal(result.broken.length, 0);
    const raw = await readFile(new URL('../.perch/rules/performance.yaml', import.meta.url), 'utf8');
    assert.equal((raw.match(/gate: false/g) ?? []).length, 4);
  } finally {
    globalThis.fetch = realFetch; process.chdir(previous);
    await rm(dir, { recursive: true, force: true });
  }
});
