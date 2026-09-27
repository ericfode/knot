#!/usr/bin/env node
// Judge-agreement runner: score taste-duel renderings through the production
// style path (declarations + composition) under a candidate rubric.
// Usage: node run.mjs RUBRIC.json OUT_DIR TASK[,TASK] [--variants=a,b] [--concurrency=N]
// Loads the credential at runtime from the main checkout's .env (never copied).
import { mkdir, mkdtemp, readFile, writeFile, readdir, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const MAIN = '/Users/ericfode/src/knot';
const REPO = '/Users/ericfode/src/knot/.claude/worktrees/perch-style-framework-c2cdfc';
const EVID = `${REPO}/docs/perch-calibration/taste-duel-2026-09-27`;
const MARKER = '# ---- harness (not shown) ----';
const [rubricPath, outDir, taskArg, ...rest] = process.argv.slice(2);
if (!rubricPath || !outDir || !taskArg) throw new Error('Usage: run.mjs RUBRIC.json OUT_DIR TASK[,TASK] [--variants=a,b] [--concurrency=N]');
const only = rest.find(a => a.startsWith('--variants='))?.slice(11).split(',');
const concurrency = Number(rest.find(a => a.startsWith('--concurrency='))?.slice(14) ?? 4);
process.loadEnvFile(`${MAIN}/.env`);
if (!process.env.PERCH_API_KEY && !process.env.TYPESAFE_API_KEY) throw new Error('No provider credential');
const { runStyleRanking } = await import(`${REPO}/scripts/perch-style.mjs`);
const summaries = JSON.parse(await readFile(`${EVID}/summaries.json`, 'utf8'));
const rubric = await readFile(resolve(rubricPath), 'utf8');
await mkdir(outDir, { recursive: true });

// One isolated workspace per rendering: the shown part only, plus the task contract.
const jobs = [];
for (const task of taskArg.split(',')) {
  const dirs = [`${EVID}/${task}`, `${EVID}/${task}/ablations`];
  for (const dir of dirs) {
    for (const name of (await readdir(dir).catch(() => [])).filter(f => f.endsWith('.bend.snapshot'))) {
      const variant = name.replace('.bend.snapshot', '');
      if (only && !only.includes(variant)) continue;
      jobs.push({ task, variant, source: (await readFile(join(dir, name), 'utf8')).split(MARKER)[0].trimEnd() + '\n' });
    }
  }
}
let cursor = 0, failures = 0;
async function worker() {
  while (cursor < jobs.length) {
    const job = jobs[cursor++];
    const out = resolve(outDir, `${job.task}__${job.variant}.json`);
    if (await access(out).then(() => true, () => false)) { console.error(`skip existing ${job.task}/${job.variant}`); continue; }
    const root = await mkdtemp(join(tmpdir(), 'judgecal-'));
    await writeFile(join(root, 'perch-style.json'), rubric);
    await writeFile(join(root, 'task.md'), `${summaries[job.task].title}\n\n${summaries[job.task].contract}\n`);
    await writeFile(join(root, `${job.variant}.bend`), job.source);
    const lines = [];
    let code;
    try {
      code = await runStyleRanking(['--live', '--json', '--jobs=16', '--task=task.md', `${job.variant}.bend`], {
        root, env: process.env, stdout: text => lines.push(text), stderr: () => {} });
      const report = JSON.parse(lines.join('\n'));
      await writeFile(out, JSON.stringify({ task: job.task, variant: job.variant, exit: code, report }, null, 1));
      console.error(`${job.task}/${job.variant}: exit ${code}, ${report.provider_requests} requests${report.failure ? ' FAILED ' + report.failure : ''}`);
      if (report.failure) failures++;
    } catch (error) { failures++; console.error(`${job.task}/${job.variant}: ERROR ${error.message}`); }
  }
}
await Promise.all(Array.from({ length: Math.min(concurrency, jobs.length) }, worker));
console.error(`done: ${jobs.length} renderings, ${failures} failures`);
process.exitCode = failures ? 1 : 0;
