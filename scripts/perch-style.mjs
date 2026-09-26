#!/usr/bin/env node
// Opt-in ordinal style review using Perch's actual Bend parser/context and Jev Score.
import { createHash, randomUUID } from 'node:crypto';
import { lstat, mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyzeBendSource, BEND_PARSER_PROFILE } from './perch-bend.mjs';
import { bendDeclarationSource, createBendReview } from './perch-bend-context.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const hash = value => createHash('sha256').update(value).digest('hex');
const inside = (root, path) => {
  const rel = relative(root, path);
  return rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel);
};

export function validateScore(answer, levels) {
  if (answer?.type !== 'score' || !Number.isFinite(answer.score)
      || answer.score < 0 || answer.score > levels - 1
      || !Number.isFinite(answer.confidence) || answer.confidence < 0 || answer.confidence > 1) {
    throw new Error('Invalid Score answer');
  }
  const probabilities = answer.probabilities;
  if (!probabilities || Object.keys(probabilities).length !== levels) throw new Error('Incomplete Score distribution');
  let total = 0, weighted = 0;
  for (let i = 0; i < levels; i++) {
    const p = probabilities[i];
    if (!Number.isFinite(p) || p < 0 || p > 1) throw new Error('Invalid Score probability');
    total += p; weighted += i * p;
  }
  // Provider probabilities/means are rounded; tolerate rounding, not arbitrary values.
  if (Math.abs(total - 1) > 0.021 || Math.abs(weighted / total - answer.score) > 0.075) {
    throw new Error('Inconsistent Score distribution');
  }
  return { score: answer.score, confidence: answer.confidence, probabilities };
}

export function rankRows(rows, dimensions, nearTieGap) {
  return dimensions.map(dimension => {
    const ordered = [...rows].sort((a, b) => b.answers[dimension.id].score - a.answers[dimension.id].score
      || a.target.localeCompare(b.target));
    let rank = 0, previousScore;
    return { id: dimension.id, title: dimension.title, entries: ordered.map((row, index) => {
      const answer = row.answers[dimension.id];
      if (answer.score !== previousScore) rank = index + 1;
      const near_tie_above = index > 0 && previousScore - answer.score < nearTieGap;
      previousScore = answer.score;
      return { rank, target: row.target, ...answer, near_tie_above,
        context_truncated: row.context?.truncated ?? false };
    }) };
  });
}

export async function prepareStyleTargets(targets, cohort, config, root = ROOT) {
  if (!cohort?.trim()) throw new Error('Supply --cohort describing the shared task or contract');
  if (!Number.isInteger(config.max_units) || config.max_units < 2 || config.max_units > 50
      || !Number.isFinite(config.near_tie_gap) || config.near_tie_gap < 0
      || !Array.isArray(config.dimensions) || config.dimensions.length !== 2) throw new Error('Invalid style configuration');
  if (new Set(config.dimensions.map(d => d.id)).size !== config.dimensions.length) throw new Error('Duplicate style dimension');
  for (const d of config.dimensions) {
    if (!d.id || !d.title || !d.instructions || !Array.isArray(d.levels)
        || d.levels.length < 2 || d.levels.length > 10 || d.levels.some(x => typeof x !== 'string' || !x.trim())) {
      throw new Error('Style dimensions need named, descriptive ordered levels');
    }
  }
  const realRoot = await realpath(root), files = new Map(), selected = new Set(), candidates = [];
  for (const target of targets) {
    const [input, name, extra] = target.split('::');
    if (!input.endsWith('.bend') || extra !== undefined || name === '') throw new Error(`Expected file.bend or file.bend::name: ${target}`);
    const absolute = await realpath(resolve(root, input));
    if (!inside(realRoot, absolute)) throw new Error('Style targets must be inside this workspace');
    const path = relative(realRoot, absolute).split(sep).join('/');
    if (!files.has(path)) {
      const source = await readFile(absolute, 'utf8');
      const analysis = await analyzeBendSource(source);
      if (analysis.parser_status !== 'parsed') throw new Error(`Bend target does not parse: ${path}`);
      const review = await createBendReview({ root: realRoot, path, source, analysis });
      files.set(path, { source, analysis, review });
    }
    const file = files.get(path);
    const declarations = file.analysis.declarations.filter(d => !name || d.qualified_name === name);
    if (!declarations.length) throw new Error(`No applicable parsed declaration: ${target}`);
    for (const declaration of declarations) {
      const identity = `${path}::${declaration.qualified_name}`;
      if (selected.has(identity)) continue;
      selected.add(identity);
      if (selected.size > config.max_units) throw new Error(`Style comparison limited to ${config.max_units} units; narrow targets`);
      const context = await file.review.forUnit(declaration.qualified_name);
      const state = { cohort, name: declaration.qualified_name,
        source: bendDeclarationSource(file.source, declaration), ...context.seen };
      if (Buffer.byteLength(JSON.stringify(state)) > 60000) throw new Error(`Style context too large: ${identity}`);
      candidates.push({ target: identity, line: declaration.line, end_line: declaration.end_line,
        source_sha256: hash(file.source), state_sha256: hash(JSON.stringify(state)),
        context: context.provenance, state });
    }
  }
  if (candidates.length < 2) throw new Error('Ranking needs at least two distinct parsed units');
  return candidates;
}

export async function evaluateStyle(candidates, config, {
  env = process.env, fetchImpl = globalThis.fetch, transport = { requests: 0, responses: 0 },
} = {}) {
  const key = env.PERCH_API_KEY || env.TYPESAFE_API_KEY;
  if (!key) throw new Error('PERCH_API_KEY is not set');
  const questions = Object.fromEntries(config.dimensions.map(d => [d.id,
    { type: 'score', instructions: d.instructions, criteria: d.levels }]));
  const rows = [];
  for (const candidate of candidates) {
    const started = performance.now();
    transport.requests++;
    const response = await fetchImpl(env.PERCH_BASE_URL || 'https://api.typesafe.ai/v1/systemone', {
      method: 'POST', signal: AbortSignal.timeout(30000),
      headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
      body: JSON.stringify({ model: env.PERCH_MODEL_ID || 'jev-latest', state: candidate.state, questions }),
    }).catch(() => { throw new Error('Style provider transport failed; no ranking produced'); });
    if (!response.ok) throw new Error(`Style provider HTTP ${response.status}; no ranking produced`);
    const body = await response.json().catch(() => { throw new Error('Invalid style provider JSON'); });
    if (typeof body?.model !== 'string' || !body.model) throw new Error('Missing resolved style model');
    const answers = Object.fromEntries(config.dimensions.map(d => [d.id, validateScore(body.answers?.[d.id], d.levels.length)]));
    transport.responses++;
    const { state, ...metadata } = candidate;
    rows.push({ ...metadata, model: body.model, elapsed_ms: Math.round(performance.now() - started),
      usage: Object.fromEntries(['input_tokens', 'output_tokens'].filter(k => Number.isFinite(body.usage?.[k])).map(k => [k, body.usage[k]])), answers });
  }
  if (new Set(rows.map(r => r.model)).size !== 1) throw new Error('Model changed during comparison; rankings are not comparable');
  return rows;
}

export async function runStyleRanking(args, {
  root = ROOT, env = process.env, fetchImpl = globalThis.fetch, loadEnv = false,
  stdout = text => console.log(text), stderr = text => console.error(text),
} = {}) {
  const cohort = args.find(x => x.startsWith('--cohort='))?.slice(9);
  const output = args.find(x => x.startsWith('--output='))?.slice(9);
  const known = x => ['--live', '--json'].includes(x) || x.startsWith('--cohort=') || x.startsWith('--output=');
  if (args.some(x => x.startsWith('--') && !known(x))) throw new Error('Unknown style option');
  if (!args.includes('--live')) throw new Error('Use --live --cohort="shared task" file.bend::name ... for an opt-in style ranking');
  if (args.some(x => x === '--output=') || args.filter(x => x.startsWith('--output=')).length > 1
      || args.filter(x => x.startsWith('--cohort=')).length > 1) throw new Error('Supply one cohort and at most one output path');
  const outputPath = output ? resolve(root, output) : null;
  if (outputPath) {
    // Refuse old evidence before paid requests, including dangling symlinks.
    const exists = await lstat(outputPath).then(() => true).catch(error => {
      if (error.code === 'ENOENT') return false;
      throw error;
    });
    if (exists) throw new Error('Style output already exists; choose a new evidence path');
    await mkdir(dirname(outputPath), { recursive: true });
  }
  const text = await readFile(resolve(root, 'perch-style.json'), 'utf8');
  const config = JSON.parse(text);
  const candidates = await prepareStyleTargets(args.filter(x => !x.startsWith('--')), cohort, config, root);
  if (loadEnv) {
    try { process.loadEnvFile(resolve(root, '.env')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const at = new Date().toISOString(), start = performance.now();
  const transport = { requests: 0, responses: 0 };
  let rows = [], failure = null;
  try { rows = await evaluateStyle(candidates, config, { env, fetchImpl, transport }); }
  catch (error) { failure = error.message; }
  const report = { schema: 1, command: 'style-rank', at, cohort, rubric_sha256: hash(text),
    parser: BEND_PARSER_PROFILE, status: failure ? 'failed' : 'completed', advisory: true,
    typechecked: false, behavioral_equivalence_checked: false,
    requested_model: env.PERCH_MODEL_ID || 'jev-latest', failure,
    provider_requests: transport.requests, provider_responses: transport.responses,
    targets: candidates.map(({ state, ...metadata }) => metadata),
    elapsed_ms: Math.round(performance.now() - start), rows,
    note: 'Relative aesthetic preferences within this cohort. Rank is not a correctness judgment. Confidence describes distribution concentration; near ties are a display convention, not statistical significance.',
    rankings: failure ? [] : rankRows(rows, config.dimensions, config.near_tie_gap) };
  const receipt = resolve(root, '.perch/usage', `${at.replaceAll(':', '-')}-${randomUUID()}.json`);
  await mkdir(dirname(receipt), { recursive: true, mode: 0o700 });
  await writeFile(receipt, JSON.stringify(report, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
  if (outputPath) {
    await writeFile(outputPath, JSON.stringify(report, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
  }
  if (args.includes('--json')) stdout(JSON.stringify(report, null, 2));
  else if (!failure) {
    for (const ranking of report.rankings) {
      stdout(`\n${ranking.title}`);
      for (const row of ranking.entries) stdout(`${row.rank}. ${row.target}${row.near_tie_above ? ' (near tie above)' : ''}${row.context_truncated ? ' [limited context]' : ''}`);
    }
    stdout(`\nAdvisory taste ranking; ${rows.length} parsed units; ${rows[0].model}. Receipt: ${relative(root, receipt)}`);
  }
  if (failure) stderr(`Style ranking failed: ${failure}. Receipt: ${relative(root, receipt)}`);
  return failure ? 1 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runStyleRanking(process.argv.slice(2), { loadEnv: true }).then(code => { process.exitCode = code; }).catch(error => {
    // Do not print arbitrary provider response bodies or transport request details.
    console.error(`Style ranking failed: ${error.message}`); process.exitCode = 1;
  });
}
