#!/usr/bin/env node
// Opt-in ordinal style review using Perch's actual Bend parser/context and Jev Score.
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { lstat, mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';
import { analyzeBendSource, BEND_PARSER_PROFILE } from './perch-bend.mjs';
import { bendDeclarationSource, createBendReview } from './perch-bend-context.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const hash = value => createHash('sha256').update(value).digest('hex');
const DEFAULT_SCOPE = 'Existing project code. Rate each declaration against its own purpose and supplied contract. No alternative implementation is required. Judge the quality of its representation and reading experience, not the difficulty of an unrelated task.';
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

const reviewRubrics = (config, kind) => kind === 'bend_datatype' ? config.dimensions : [...config.dimensions, config.criticality];

function validateStyleTarget(target, config) {
  const dimension = config.dimensions.find(d => d.id === target?.dimension);
  if (!dimension || !Number.isInteger(target.level) || target.level < 1 || target.level >= dimension.levels.length
      || !Number.isFinite(target.minimum_probability) || target.minimum_probability <= 0.5 || target.minimum_probability > 1) {
    throw new Error('Invalid style target');
  }
}

function criticalityFor(row, config) {
  if (row.kind === 'bend_datatype') return { target: row.target, status: 'not_applicable', probability_critical: null };
  const policy = config.criticality;
  const answer = validateScore({ ...row.answers?.[policy.id], type: 'score' }, policy.levels.length);
  const probability = answer.probabilities[1] / (answer.probabilities[0] + answer.probabilities[1]);
  // Limited context cannot establish that a declaration deserves the lower bar.
  const status = probability >= policy.minimum_probability ? 'critical'
    : !row.context?.truncated && probability <= 1 - policy.minimum_probability ? 'noncritical' : 'uncertain';
  return { target: row.target, status, probability_critical: probability, context_truncated: row.context?.truncated ?? false };
}

export function assessStyle(rows, config) {
  if (!Array.isArray(config.style_targets) || config.style_targets.length !== config.dimensions.length
      || new Set(config.style_targets.map(t => t.dimension)).size !== config.dimensions.length) throw new Error('Each style dimension needs one target');
  for (const target of config.style_targets) validateStyleTarget(target, config);
  const policy = config.criticality;
  if (!policy?.id || config.dimensions.some(d => d.id === policy.id) || !policy.title || !policy.instructions
      || !Array.isArray(policy.levels) || policy.levels.length !== 2 || policy.levels.some(x => typeof x !== 'string' || !x.trim())
      || !Number.isFinite(policy.minimum_probability) || policy.minimum_probability <= 0.5 || policy.minimum_probability > 1) {
    throw new Error('Criticality needs a separate binary Score rubric');
  }
  validateStyleTarget(policy.style_target, config);
  const ordinary = config.style_targets.find(t => t.dimension === policy.style_target.dimension);
  if (policy.style_target.level <= ordinary.level || policy.style_target.minimum_probability < ordinary.minimum_probability) {
    throw new Error('Criticality must require a stricter style target');
  }
  return rows.flatMap(row => {
    const criticality = criticalityFor(row, config);
    const strict = ['critical', 'uncertain'].includes(criticality.status);
    return config.style_targets.map(base => {
      const target = strict && base.dimension === policy.style_target.dimension ? policy.style_target : base;
      const answer = row.answers[target.dimension];
      const total = Object.values(answer.probabilities).reduce((a, b) => a + b, 0);
      const probability = Object.entries(answer.probabilities).reduce((sum, [level, p]) => sum + (Number(level) >= target.level ? p : 0), 0) / total;
      return { target: row.target, dimension: target.dimension, target_level: target.level,
        minimum_probability: target.minimum_probability, criticality_status: criticality.status,
        target_basis: target === base ? 'default' : 'criticality',
        probability_at_target: probability, status: probability >= target.minimum_probability ? 'meets_target'
          : probability <= 1 - target.minimum_probability ? 'below_target' : 'uncertain',
        context_truncated: row.context?.truncated ?? false };
    });
  });
}

function datatypeContext(file, path, declaration) {
  const referencedBy = new Set(file.analysis.references.filter(r => r.name === declaration.name || r.name.startsWith(`${declaration.name}.`)).map(r => r.source));
  const consumers = file.analysis.declarations.filter(d => referencedBy.has(d.id));
  const types = file.analysis.datatype_declarations.filter(d => d.name !== declaration.name);
  const limits = { callers: 4, files: 1, bytes: 48000 };
  let bytes = 0, truncated = consumers.length > limits.callers;
  const entries = declarations => declarations.flatMap(d => {
    const source = bendDeclarationSource(file.source, d);
    bytes += Buffer.byteLength(source);
    if (bytes > limits.bytes) { truncated = true; return []; }
    return [{ name: d.qualified_name ?? d.name, path, line: d.line, end_line: d.end_line, source }];
  });
  const called_by = entries(consumers.slice(0, limits.callers)), datatypes = entries(types);
  const unresolved = [{ path, name: declaration.name, reason: 'datatype-context-is-same-file-only; imported and transitive dependencies are not resolved' }];
  const provenance = { basis: 'working-tree', files: [{ path, source_sha256: hash(file.source) }], unresolved, truncated, limits };
  return { seen: { calls: [], called_by, laws: [], datatypes,
    imports: file.analysis.references.filter(r => r.kind === 'import').map(({ module, alias }) => ({ module, alias })),
    context_notes: { basis: provenance.basis, unresolved, truncated } }, provenance };
}

export async function prepareStyleTargets(targets, cohort, config, root = ROOT) {
  if (!Number.isInteger(config.max_units) || config.max_units < 1 || config.max_units > 10000
      || !Number.isFinite(config.near_tie_gap) || config.near_tie_gap < 0
      || !Array.isArray(config.dimensions) || config.dimensions.length < 1 || config.dimensions.length > 6) throw new Error('Invalid style configuration');
  if (new Set(config.dimensions.map(d => d.id)).size !== config.dimensions.length) throw new Error('Duplicate style dimension');
  for (const d of config.dimensions) {
    if (!d.id || !d.title || !d.instructions || !Array.isArray(d.levels)
        || d.levels.length < 2 || d.levels.length > 10 || d.levels.some(x => typeof x !== 'string' || !x.trim())) {
      throw new Error('Style dimensions need named, descriptive ordered levels');
    }
  }
  assessStyle([], config);
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
    const declarations = [...file.analysis.declarations, ...file.analysis.datatype_declarations.map(d => ({
      ...d, qualified_name: d.name, syntax_kind: 'bend_datatype',
    }))].filter(d => !name || d.qualified_name === name).sort((a, b) => a.line - b.line);
    if (!declarations.length) throw new Error(`No applicable parsed declaration: ${target}`);
    for (const declaration of declarations) {
      const identity = `${path}::${declaration.qualified_name}`;
      if (selected.has(identity)) continue;
      selected.add(identity);
      if (selected.size > config.max_units) throw new Error(`Style run limited to ${config.max_units} units; narrow targets or raise max_units`);
      const context = declaration.syntax_kind === 'bend_datatype' ? datatypeContext(file, path, declaration)
        : await file.review.forUnit(declaration.qualified_name);
      const state = { cohort: cohort?.trim() || DEFAULT_SCOPE, name: declaration.qualified_name,
        path, declaration_kind: declaration.syntax_kind,
        source: bendDeclarationSource(file.source, declaration), ...context.seen };
      if (Buffer.byteLength(JSON.stringify(state)) > 60000) throw new Error(`Style context too large: ${identity}`);
      candidates.push({ target: identity, path, kind: declaration.syntax_kind,
        line: declaration.line, end_line: declaration.end_line,
        source_sha256: hash(file.source), state_sha256: hash(JSON.stringify(state)),
        context: context.provenance, state });
    }
  }
  if (!candidates.length) throw new Error('Ranking needs at least one parsed unit');
  return candidates;
}

export async function prepareStyleInventory(cohort, config, root = ROOT) {
  const paths = [...new Set(execFileSync('git', ['ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', '*.bend'],
    { cwd: root, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }).split('\0').filter(Boolean))].sort();
  if (!paths.length) throw new Error('No project Bend files found');
  const candidates = [], unranked = [], empty_files = [];
  for (const path of paths) {
    try { candidates.push(...await prepareStyleTargets([path], cohort, config, root)); }
    catch (error) {
      if (error.message.startsWith('No applicable parsed declaration:')) empty_files.push(path);
      else unranked.push({ path, reason: error.message });
    }
    if (candidates.length > config.max_units) throw new Error(`Style run limited to ${config.max_units} units; raise max_units for this inventory`);
  }
  return { candidates, inventory: { discovered_files: paths, empty_files, unranked } };
}

export async function changedStyleSources(candidates, root = ROOT) {
  const files = new Map();
  const remember = (path, expected) => {
    if (files.has(path) && files.get(path) !== expected) throw new Error(`Source changed during style preflight: ${path}`);
    files.set(path, expected);
  };
  for (const candidate of candidates) {
    remember(candidate.path ?? candidate.target.split('::')[0], candidate.source_sha256);
    for (const file of candidate.context?.files ?? []) {
      remember(file.path, file.source_sha256);
    }
  }
  const changed = [];
  for (const [path, expected] of files) {
    const actual = await readFile(resolve(root, path)).then(hash).catch(() => null);
    if (actual !== expected) changed.push(path);
  }
  return changed;
}

export async function evaluateStyle(candidates, config, {
  env = process.env, fetchImpl = globalThis.fetch, transport = { requests: 0, responses: 0 },
  concurrency = 1, onProgress = () => {}, onRow = () => {},
} = {}) {
  const key = env.PERCH_API_KEY || env.TYPESAFE_API_KEY;
  if (!key) throw new Error('PERCH_API_KEY is not set');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 16) throw new Error('Concurrency must be 1..16');
  const rows = new Array(candidates.length);
  let cursor = 0, failure = null;
  async function evaluate(candidate) {
    const rubrics = reviewRubrics(config, candidate.kind);
    const questions = Object.fromEntries(rubrics.map(d => [d.id,
      { type: 'score', instructions: d.instructions, criteria: d.levels }]));
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
    const answers = Object.fromEntries(rubrics.map(d => [d.id, validateScore(body.answers?.[d.id], d.levels.length)]));
    transport.responses++;
    const { state, ...metadata } = candidate;
    return { ...metadata, model: body.model, elapsed_ms: Math.round(performance.now() - started),
      usage: Object.fromEntries(['input_tokens', 'output_tokens'].filter(k => Number.isFinite(body.usage?.[k])).map(k => [k, body.usage[k]])), answers };
  }
  async function worker() {
    while (!failure && cursor < candidates.length) {
      const index = cursor++;
      try {
        rows[index] = await evaluate(candidates[index]);
        onRow(rows[index]);
        onProgress(transport.responses, candidates.length);
      } catch (error) { failure ??= error; }
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, candidates.length) }, worker));
  if (failure) throw failure;
  if (new Set(rows.map(r => r.model)).size !== 1) throw new Error('Model changed during comparison; rankings are not comparable');
  return rows;
}

export async function runStyleRanking(args, {
  root = ROOT, env = process.env, fetchImpl = globalThis.fetch, loadEnv = false,
  stdout = text => console.log(text), stderr = text => console.error(text),
} = {}) {
  const cohort = args.find(x => x.startsWith('--cohort='))?.slice(9);
  const output = args.find(x => x.startsWith('--output='))?.slice(9);
  const reuse = args.find(x => x.startsWith('--reuse='))?.slice(8);
  const all = args.includes('--all');
  const concurrency = Number(args.find(x => x.startsWith('--jobs='))?.slice(7) ?? (all ? 8 : 1));
  const known = x => ['--live', '--json', '--all'].includes(x) || ['--cohort=', '--output=', '--jobs=', '--reuse='].some(p => x.startsWith(p));
  if (args.some(x => x.startsWith('--') && !known(x))) throw new Error('Unknown style option');
  if (!args.includes('--live')) throw new Error('Use --live file.bend::name, file.bend, or --live --all to rank project Bend declarations');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 16) throw new Error('Concurrency must be 1..16');
  const targets = args.filter(x => !x.startsWith('--'));
  if (all && targets.length) throw new Error('Use --all or explicit targets, not both');
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
  const { candidates, inventory } = all ? await prepareStyleInventory(cohort, config, root)
    : { candidates: await prepareStyleTargets(targets, cohort, config, root), inventory: null };
  if (!candidates.length) throw new Error('No rankable parsed declarations');
  const preflightChanged = await changedStyleSources(candidates, root);
  if (preflightChanged.length) throw new Error(`Source changed during style preflight: ${preflightChanged.join(', ')}`);
  if (loadEnv) {
    try { process.loadEnvFile(resolve(root, '.env')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const at = new Date().toISOString(), start = performance.now();
  const transport = { requests: 0, responses: 0 };
  const reused = new Map(), completed_rows = [];
  if (reuse) {
    const bytes = await readFile(resolve(root, reuse));
    const prior = JSON.parse((reuse.endsWith('.gz') ? gunzipSync(bytes) : bytes).toString('utf8'));
    if (prior.command !== 'style-rank' || prior.schema !== 2 || prior.rubric_sha256 !== hash(text)
        || prior.parser !== BEND_PARSER_PROFILE || prior.requested_model !== (env.PERCH_MODEL_ID || 'jev-latest')) {
      throw new Error('Style reuse requires the same rubric, parser and requested model');
    }
    const saved = new Map([...(prior.rows ?? []), ...(prior.completed_rows ?? [])].map(r => [r.target, r]));
    for (const candidate of candidates) {
      const row = saved.get(candidate.target);
      if (!row || row.kind !== candidate.kind || row.state_sha256 !== candidate.state_sha256 || row.source_sha256 !== candidate.source_sha256
          || JSON.stringify(row.context) !== JSON.stringify(candidate.context)) continue;
      for (const d of reviewRubrics(config, candidate.kind)) validateScore({ ...row.answers?.[d.id], type: 'score' }, d.levels.length);
      if (typeof row.model !== 'string' || !row.model) throw new Error('Missing resolved model in reused row');
      reused.set(row.target, row);
    }
  }
  const pending = candidates.filter(c => !reused.has(c.target));
  let rows = [], failure = null;
  try {
    const fresh = pending.length ? await evaluateStyle(pending, config, { env, fetchImpl, transport, concurrency,
    onProgress: (done, total) => { if (all && (done % 100 === 0 || done === total)) stderr(`Style review: ${done}/${total} declarations`); },
    onRow: row => completed_rows.push(row),
    }) : [];
    const byTarget = new Map([...reused, ...fresh.map(row => [row.target, row])]);
    rows = candidates.map(c => byTarget.get(c.target));
    if (new Set(rows.map(r => r.model)).size !== 1) throw new Error('Model changed during review; ratings are not comparable');
  }
  catch (error) { failure = error.message; }
  if (failure) rows = [];
  const changed_sources = await changedStyleSources(candidates, root);
  const assessments = failure ? [] : assessStyle(rows, config);
  const criticality = failure ? [] : rows.map(row => criticalityFor(row, config));
  const counts = Object.fromEntries(['meets_target', 'below_target', 'uncertain'].map(status => [status, assessments.filter(a => a.status === status).length]));
  const meets_all = rows.filter(row => assessments.filter(a => a.target === row.target).every(a => a.status === 'meets_target')).length;
  const by_axis = config.dimensions.map(d => ({ id: d.id, title: d.title,
    ...Object.fromEntries(['meets_target', 'below_target', 'uncertain'].map(status => [status, assessments.filter(a => a.dimension === d.id && a.status === status).length])) }));
  const report = { schema: 2, command: 'style-rank', at, cohort: cohort || null,
    mode: all ? 'project' : 'targets', inventory, rubric_sha256: hash(text),
    parser: BEND_PARSER_PROFILE, status: failure ? 'failed' : inventory?.unranked.length ? 'incomplete' : 'completed', advisory: true,
    coverage: { selected: candidates.length, ranked: rows.length, unranked_files: inventory?.unranked.length ?? 0 },
    reused_from: reuse || null, reused_units: reused.size,
    completed_rows: failure ? [...reused.values(), ...completed_rows] : [],
    style_targets: config.style_targets, style_summary: { ...counts, meets_all, needs_review: rows.length - meets_all, by_axis }, assessments,
    criticality: { policy: config.criticality, assessments: criticality },
    source_freshness: { status: changed_sources.length ? 'changed-since-preflight' : 'current', changed_sources },
    typechecked: false, behavioral_equivalence_checked: false,
    requested_model: env.PERCH_MODEL_ID || 'jev-latest', failure,
    provider_requests: transport.requests, provider_responses: transport.responses,
    targets: candidates.map(({ state, ...metadata }) => metadata),
    elapsed_ms: Math.round(performance.now() - start), rows,
    note: 'Each parsed declaration is rated against its own task, then sorted on each rubric. Alternatives and a shared contract are not required. Rank is advisory taste, not correctness or task difficulty. Confidence describes distribution concentration; near ties are not statistical significance. Rankings describe the recorded source snapshot.',
    rankings: failure ? [] : rankRows(rows, config.dimensions, config.near_tie_gap) };
  const receipt = resolve(root, '.perch/usage', `${at.replaceAll(':', '-')}-${randomUUID()}.json`);
  await mkdir(dirname(receipt), { recursive: true, mode: 0o700 });
  await writeFile(receipt, JSON.stringify(report, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
  if (outputPath) {
    const encoded = JSON.stringify(report, null, 2) + '\n';
    await writeFile(outputPath, outputPath.endsWith('.gz') ? gzipSync(encoded) : encoded, { mode: 0o600, flag: 'wx' });
  }
  if (args.includes('--json')) stdout(JSON.stringify(report, null, 2));
  else if (!failure) {
    stdout(`${meets_all}/${rows.length} declarations meet all ${config.dimensions.length} style targets.`);
    for (const item of criticality.filter(c => ['critical', 'uncertain'].includes(c.status))) {
      stdout(`Criticality ${item.status}: ${item.target} (${Math.round(100 * item.probability_critical)}% critical) requires level ${config.criticality.style_target.level} on ${config.criticality.style_target.dimension}.`);
    }
    for (const axis of by_axis) stdout(`${axis.title}: ${axis.meets_target} meet target; ${axis.below_target} below target; ${axis.uncertain} uncertain.`);
    for (const assessment of assessments.filter(a => a.status !== 'meets_target')) {
      stdout(`${assessment.status}: ${assessment.target} / ${assessment.dimension} (${Math.round(100 * assessment.probability_at_target)}% at level ${assessment.target_level}+)${assessment.context_truncated ? ' [limited context]' : ''}`);
    }
    for (const ranking of report.rankings) {
      stdout(`\n${ranking.title}`);
      for (const row of ranking.entries) stdout(`${row.rank}. ${row.target}${row.near_tie_above ? ' (near tie above)' : ''}${row.context_truncated ? ' [limited context]' : ''}`);
    }
    stdout(`\nAdvisory taste ranking; ${rows.length} parsed units; ${rows[0].model}. Receipt: ${relative(root, receipt)}`);
  }
  if (failure) stderr(`Style ranking failed: ${failure}. Receipt: ${relative(root, receipt)}`);
  if (inventory?.unranked.length) stderr(`${inventory.unranked.length} file(s) could not be ranked; see inventory.unranked in the receipt`);
  if (changed_sources.length) stderr(`${changed_sources.length} source/context file(s) changed during review; rankings refer to the recorded snapshot`);
  return failure || inventory?.unranked.length ? 1 : counts.below_target || counts.uncertain || changed_sources.length ? 3 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runStyleRanking(process.argv.slice(2), { loadEnv: true }).then(code => { process.exitCode = code; }).catch(error => {
    // Do not print arbitrary provider response bodies or transport request details.
    console.error(`Style ranking failed: ${error.message}`); process.exitCode = 1;
  });
}
