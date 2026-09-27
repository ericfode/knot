#!/usr/bin/env node
// Retain check evidence: upstream `perch check` deliberately records nothing.
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadProjectEnv } from './project-env.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const hash = text => createHash('sha256').update(text).digest('hex');

async function ruleIdentity(root) {
  const directory = join(root, '.perch/rules');
  const names = (await readdir(directory, { recursive: true }).catch(() => []))
    .filter(name => /\.ya?ml$/.test(name)).sort();
  const files = ['perch.yaml', ...names.map(name => `.perch/rules/${name}`)];
  const contents = await Promise.all(files.map(async path => [path,
    await readFile(join(root, path), 'utf8').catch(() => '')]));
  return hash(JSON.stringify(contents));
}

function classify(code, result, errors) {
  if (/PERCH_API_KEY is not set/.test(errors)) return 'missing-key';
  if (code === 0 && result?.checked === 0) return 'no-coverage';
  if (code === 3) return 'findings';
  if (code !== 0) return 'failed';
  if (!result) return 'unreadable-result';
  return 'completed';
}

// Exported for offline tests with the real CLI and a stubbed provider.
export async function runPerch(args, {
  root = ROOT, env = process.env,
  stdout = text => process.stdout.write(`${text}\n`),
  stderr = text => process.stderr.write(`${text}\n`),
} = {}) {
  // Upstream Perch reads .env from the Git root of the current checkout; a linked
  // worktree has none, so load the main checkout's file into the real process env.
  if (env === process.env) {
    const found = loadProjectEnv(root);
    if (found?.source === 'shared-checkout') stderr(`Credentials: this worktree has no .env; using the main checkout's ${found.path}`);
  }
  const { main } = await import('../node_modules/@lakeday/perch/dist/cli.mjs');
  const command = args[0];
  const recorded = ['check', 'scan'].includes(command) && !args.includes('--help');
  const actual = recorded && !args.includes('--json') ? [...args, '--json'] : args;
  const previous = process.cwd();
  const originalFetch = globalThis.fetch;
  const transport = { requests: 0, responses: 0, models: new Set(), answers: [], usage: {} };
  if (recorded) globalThis.fetch = async (input, init) => {
    const provider = String(input) === (env.PERCH_BASE_URL || 'https://api.typesafe.ai/v1/systemone');
    if (provider) transport.requests++;
    const response = await originalFetch(input, init);
    if (provider && response.ok) {
      transport.responses++;
      // Clone only structured provider answers; never retain request bodies,
      // headers, URLs, authorization errors, or arbitrary response text.
      const body = await response.clone().json().catch(() => null);
      if (typeof body?.model === 'string') transport.models.add(body.model);
      for (const [rule, answer] of Object.entries(body?.answers ?? {})) {
        if (typeof answer.noul === 'number') transport.answers.push({ rule, probability_true: answer.noul });
      }
      for (const key of ['input_tokens', 'output_tokens', 'total_tokens']) {
        if (typeof body?.usage?.[key] === 'number') transport.usage[key] = (transport.usage[key] ?? 0) + body.usage[key];
      }
    }
    return response;
  };
  process.chdir(root);
  try {
    const started = new Date();
    const startTime = performance.now();
    const rulesHash = recorded ? await ruleIdentity(root) : null;
    // Resolve target from Perch's result when available; this pre-run hash is
    // only for the usual explicit-file check form, not issue-id checks or scans.
    const target = command === 'check' && args[1] && !args[1].startsWith('-')
      ? args[1].split('::')[0] : null;
    const sourceHash = target
      ? await readFile(resolve(root, target)).then(hash).catch(() => null) : null;
    const output = [], errors = [];
    let code = await main(actual, {
      env,
      stdout: text => { if (recorded) output.push(text); stdout(text); },
      stderr: text => { if (recorded) errors.push(text); stderr(text); },
    });
    if (!recorded) return code;
    let result = null;
    try { result = JSON.parse(output.join('\n')); } catch { /* classify below */ }
    let status = classify(code, result, errors.join('\n'));
    if (command === 'scan' && code === 0 && /^Nothing changed since .+\.$/.test(output.join('\n'))) status = 'unchanged';
    if (command === 'scan' && result?.run?.methods === 0 && result.run.checked === 0) status = 'no-coverage';
    if (status === 'completed' && command === 'check' && transport.responses === 0) status = 'no-provider-coverage';
    if (command === 'scan' && result?.parser_coverage?.parse_failures > 0) status = 'partial-parser-coverage';
    if (command === 'scan' && (result?.run?.failed?.length || result?.run?.incomplete?.length)) status = 'partial-provider-coverage';
    const upstreamExit = code;
    if (['no-coverage', 'unreadable-result', 'no-provider-coverage', 'partial-parser-coverage', 'partial-provider-coverage'].includes(status)) {
      code = 1;
      stderr(`Knot: ${status}; this is not a successful lint check.`);
    }
    let revision = null;
    try { revision = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { /* failure recorded */ }
    const requested = actual.indexOf('--rules');
    const ruleList = requested >= 0 ? actual[requested + 1] : actual.find(a => a.startsWith('--rules='))?.slice(8);
    const installed = JSON.parse(await readFile(join(ROOT, 'node_modules/@lakeday/perch/package.json'), 'utf8'));
    // File checks return an array; named checks put the same unit at the top level.
    const units = result?.units ?? (result?.context ? [result] : []);
    const receipt = {
      schema: 1, id: randomUUID(), at: started.toISOString(), command,
      target: result?.path ?? target, revision, source_sha256: sourceHash,
      rules_sha256: rulesHash, selected_rules: ruleList?.split(',') ?? null,
      perch_version: installed.version,
      requested_model: env.PERCH_MODEL_ID || 'jev-latest',
      resolved_model: transport.models.size === 1 ? [...transport.models][0] : null,
      model_resolution: transport.responses ? 'provider-responses-this-run'
        : result?.run?.carried ? 'cached-answers-not-revalidated' : 'unavailable',
      provider_requests: transport.requests, provider_responses: transport.responses,
      models: [...transport.models], answers: transport.answers, usage: transport.usage,
      elapsed_ms: Math.round(performance.now() - startTime),
      upstream_exit: upstreamExit, exit: code, status,
      checked: result?.checked ?? result?.run?.reviewed_checks ?? result?.run?.checked ?? null,
      scan: command === 'scan' ? {
        mode: args.includes('--fresh') ? 'fresh' : args.includes('--incremental') ? 'incremental' : 'default',
        methods: result?.run?.methods ?? null,
        calls: result?.run?.calls ?? null,
        carried: result?.run?.carried ?? null,
        failed: result?.run?.failed?.length ?? null,
        incomplete: result?.run?.incomplete?.length ?? null,
      } : null,
      parser: result?.parser ?? null,
      parser_coverage: result?.parser_coverage ?? null,
      // Parsed units retain attribution and the exact local context identities.
      // Answers carry probabilities only; no source bodies or credentials.
      units: units.map(unit => ({
        path: unit.path, name: unit.name, line: unit.line, end_line: unit.end_line,
        checked: unit.checked,
        asked: unit.asked?.map(({ rule, broken, floor }) => ({ rule, broken, floor })),
        broken: unit.broken?.map(({ rule, broken, floor }) => ({ rule, broken, floor })),
        context: unit.context,
      })),
      // Store structured check findings, never environment, full source, raw
      // provider errors, or arbitrary stdout. Native scans retain their own log.
      findings: (result?.broken ?? []).map(item => ({
        rule: item.rule, probability: item.broken, floor: item.floor,
        name: item.name, line: item.line, end_line: item.end_line,
      })),
      issue_count: result?.issues?.length ?? null,
      adjudication: 'unreviewed',
    };
    const directory = join(root, '.perch/usage');
    try {
      await mkdir(directory, { recursive: true, mode: 0o700 });
      await writeFile(join(directory, `${receipt.at.replaceAll(':', '-')}-${receipt.id}.json`),
        JSON.stringify(receipt, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
    } catch (error) {
      stderr(`Knot: could not record lint usage (${error.code ?? error.name}).`);
      if (code === 0) code = 1;
    }
    return code;
  } finally {
    globalThis.fetch = originalFetch;
    process.chdir(previous);
  }
}

export async function usageSummary(root = ROOT) {
  const directory = join(root, '.perch/usage');
  const names = (await readdir(directory).catch(() => [])).filter(name => name.endsWith('.json')).sort();
  const statuses = {}, findings = {};
  let malformed = 0;
  for (const name of names) {
    try {
      const record = JSON.parse(await readFile(join(directory, name), 'utf8'));
      statuses[record.status] = (statuses[record.status] ?? 0) + 1;
      for (const finding of record.findings ?? []) {
        findings[finding.rule] = (findings[finding.rule] ?? 0) + 1;
      }
    } catch { malformed++; }
  }
  return { receipts: names.length, malformed, statuses, findings,
    note: 'Finding counts are not precision. Adjudicate against docs/perch-review-log.md; inspect native scan logs and older package receipts separately.' };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv[2] === 'history') console.log(JSON.stringify(await usageSummary(), null, 2));
    else process.exitCode = await runPerch(process.argv.slice(2));
  } catch (error) {
    console.error(`Knot Perch workflow failed: ${error.message}`);
    process.exitCode = 1;
  }
}
