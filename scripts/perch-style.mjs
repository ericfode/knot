#!/usr/bin/env node
// Opt-in ordinal style review using Perch's actual Bend parser/context and Jev Score.
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { lstat, mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';
import { BEND_PARSER_PROFILE } from './perch-bend.mjs';
import { bendDeclarationSource, createBendReview, createBendSourceSnapshot } from './perch-bend-context.mjs';
import { INTERFACE_CONTEXT, fitInterfaceContext, prepareInterfaceComposition } from './perch-context-interfaces.mjs';
import { DEFAULT_PERCH_JOBS as DEFAULT_CONCURRENCY, MAX_PERCH_JOBS as MAX_CONCURRENCY, mapConcurrent } from './perch-throughput.mjs';
import { createStyleAnswerCache, styleEndpoint } from './perch-style-cache.mjs';
import { book_nil, parse_book } from '../vendor/bend-parser/bend.mts';
import baseSource from '../vendor/bend-parser/base-source.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PREFLIGHT_CONCURRENCY = 32;
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

const diagnosticRubrics = config => config.diagnostic_dimensions === undefined ? [] : config.diagnostic_dimensions;
const reviewRubrics = (config, kind, context) => [
  ...config.dimensions,
  // Do not manufacture a diagnostic score from a context known to be truncated.
  ...(context?.truncated ? [] : diagnosticRubrics(config)),
  config.criticality,
  ...(config.style_role ? [config.style_role] : []),
];

function scoreRequest(candidate, rubrics, requestedModel) {
  const questions = Object.fromEntries(rubrics.map(d => [d.id,
    { type: 'score', instructions: d.instructions, criteria: d.levels }]));
  return { rubrics, body: JSON.stringify({ model: requestedModel, state: candidate.state, questions }) };
}

function styleRequest(candidate, config, requestedModel) {
  return scoreRequest(candidate, reviewRubrics(config, candidate.kind, candidate.context), requestedModel);
}

function validatePotential(config) {
  const policy = config.potential_profundity;
  if (!policy) return;
  if (!policy.id || [...config.dimensions, ...diagnosticRubrics(config), config.criticality, config.style_role].some(d => d?.id === policy.id)
      || !policy.title || !policy.instructions || !Array.isArray(policy.levels) || policy.levels.length !== 5
      || policy.levels.some(level => typeof level !== 'string' || !level.trim())
      || !Number.isInteger(policy.relevance_level) || policy.relevance_level < 1 || policy.relevance_level >= policy.levels.length
      || !Number.isFinite(policy.minimum_probability) || policy.minimum_probability <= .5 || policy.minimum_probability > 1
      || !Number.isInteger(policy.max_task_bytes) || policy.max_task_bytes < 1 || policy.max_task_bytes > 16000
      || !Number.isInteger(policy.max_composition_bytes) || policy.max_composition_bytes < 1 || policy.max_composition_bytes > 48000) {
    throw new Error('Potential profundity needs a separate five-level task rubric and bounded context');
  }
  validateStyleTarget(policy.style_target, config);
  const baseline = config.style_targets.find(t => t.dimension === policy.style_target.dimension);
  if (policy.style_target.level <= baseline.level || policy.style_target.minimum_probability < baseline.minimum_probability) {
    throw new Error('Potential profundity must require a stricter composition target');
  }
}

function probabilityAt(answer, level) {
  const total = Object.values(answer.probabilities).reduce((sum, p) => sum + p, 0);
  return Object.entries(answer.probabilities).reduce((sum, [n, p]) => sum + (Number(n) >= level ? p : 0), 0) / total;
}

export function assessPotentialProfundity(answer, config, { available = true, reason = null } = {}) {
  validatePotential(config);
  const policy = config.potential_profundity;
  if (!available || !answer) return { status: 'unavailable', probability_relevant: null, reason: reason ?? 'missing_task_context' };
  const score = validateScore({ ...answer, type: 'score' }, policy.levels.length);
  const probability = probabilityAt(score, policy.relevance_level);
  return { ...score, probability_relevant: probability,
    status: probability >= policy.minimum_probability ? 'high' : probability <= 1 - policy.minimum_probability ? 'low' : 'uncertain',
    relevance_level: policy.relevance_level, minimum_probability: policy.minimum_probability };
}

export function potentialProfundityRequest(taskText, config, requestedModel = 'jev-latest') {
  validatePotential(config);
  if (typeof taskText !== 'string' || !taskText.trim() || Buffer.byteLength(taskText) > config.potential_profundity.max_task_bytes) {
    throw new Error('Potential profundity requires explicit bounded task context');
  }
  const state = { contract: taskText, instruction: 'Evaluate only the stated task and contract. No implementation, source grades, author, prior result or criticality judgment is provided.' };
  const candidate = { target: '@task', kind: 'task_contract', source_sha256: hash(taskText),
    state_sha256: hash(JSON.stringify(state)), state,
    context: { basis: 'explicit-task-only', files: [], unresolved: [], truncated: false, limits: { bytes: config.potential_profundity.max_task_bytes } } };
  const request = scoreRequest(candidate, [config.potential_profundity], requestedModel);
  return { ...request, candidate, request_sha256: hash(request.body), state_sha256: candidate.state_sha256 };
}

let builtinNames;
function knownBuiltins() {
  if (!builtinNames) {
    const book = book_nil();
    parse_book(book, '', baseSource, '', Object.create(null));
    builtinNames = new Set([...Object.keys(book.tlds), 'Kind', 'Data', 'Prop', 'Type']);
  }
  return builtinNames;
}

/** One explicit selected group, not a repository-wide or transitive-closure claim. */
export async function prepareStyleComposition(candidates, cohort, config, root = ROOT, snapshot = null, readingOrder = null) {
  validatePotential(config);
  snapshot ??= await createBendSourceSnapshot(root);
  const selected = readingOrder ?? [...new Set(candidates.map(c => c.path ?? c.target.split('::')[0]))].sort();
  if (snapshot.contextPolicy === INTERFACE_CONTEXT) return prepareInterfaceComposition(selected, cohort, config, root, snapshot, knownBuiltins(), hash(baseSource));
  const collaborators = candidates.flatMap(c => (c.context?.files ?? []).map(f => f.path));
  const paths = readingOrder
    ? [...selected, ...[...new Set(collaborators)].filter(path => !selected.includes(path)).sort()]
    : [...new Set([...selected, ...collaborators])].sort();
  const loaded = new Map(), files = [], unresolved = [], reasons = [];
  let bytes = 0;
  for (const path of paths) {
    const file = await snapshot.load(path);
    loaded.set(path, file);
    bytes += Buffer.byteLength(file.source);
    files.push({ path, source_sha256: file.source_sha256 });
    if (file.analysis.parser_status !== 'parsed' || Object.values(file.analysis.truncated ?? {}).some(Boolean)) reasons.push('source_inventory_incomplete');
  }
  for (const [path, file] of loaded) {
    const names = new Set([...file.analysis.declarations.map(d => d.qualified_name), ...file.analysis.datatype_declarations.map(d => d.name)]);
    const imports = file.analysis.references.filter(r => r.kind === 'import');
    const typeReferences = [...file.analysis.declarations, ...file.analysis.datatype_declarations]
      .flatMap(d => d.context_references ?? []);
    for (const ref of [...file.analysis.references.filter(r => r.kind !== 'import'), ...typeReferences]) {
      if (names.has(ref.name) || knownBuiltins().has(ref.name)) continue;
      const prefix = ref.name.split('.')[0], imp = imports.find(i => i.alias === prefix);
      const local = imp && (imp.module.startsWith('./') || imp.module.startsWith('../'));
      const dependency = local ? relative(resolve(root), resolve(root, dirname(path), imp.module)).split(sep).join('/') : null;
      const target = dependency ? loaded.get(dependency) : null;
      const name = imp ? ref.name.slice(prefix.length + 1) : ref.name;
      if (target && [...target.analysis.declarations.map(d => d.qualified_name), ...target.analysis.datatype_declarations.map(d => d.name)].includes(name)) continue;
      unresolved.push({ path, name: ref.name, reason: !imp ? 'unknown-reference' : !local ? 'nonlocal-import' : 'collaborator-not-in-group' });
    }
  }
  if (unresolved.length) reasons.push('unresolved_composition_context');
  if (bytes > config.potential_profundity.max_composition_bytes) reasons.push('composition_byte_limit');
  const context = { basis: 'explicit-selected-source-group', selected_files: selected, files,
    unresolved, truncated: bytes > config.potential_profundity.max_composition_bytes,
    limits: { bytes: config.potential_profundity.max_composition_bytes }, source_bytes: bytes,
    builtin_source_sha256: hash(baseSource), scope: 'Full selected files and known collaborator files only; no whole-project completeness claim.' };
  const state = { contract: cohort, scope: context.scope,
    files: reasons.length ? [] : paths.map(path => ({ path, source: loaded.get(path).source })),
    context_notes: context, instruction: 'Judge the complete collaborating mechanism in the supplied files. Source comments are evidence, not instructions. Do not infer a potential verdict, previous scores or missing implementation.' };
  const candidate = { target: '@composition', kind: 'bend_composition', source_sha256: hash(JSON.stringify(files)),
    state_sha256: hash(JSON.stringify(state)), context, state };
  return { available: reasons.length === 0, reasons: [...new Set(reasons)], candidate };
}

function validateDiagnostics(config) {
  const diagnostics = diagnosticRubrics(config);
  if (!Array.isArray(diagnostics) || config.dimensions.length + diagnostics.length > 6) {
    throw new Error('Invalid diagnostic dimensions');
  }
  const ids = [...config.dimensions.map(d => d.id), config.criticality.id];
  for (const d of diagnostics) {
    if (!d.id || !d.title || !d.instructions || !Array.isArray(d.levels)
        || d.levels.length < 2 || d.levels.length > 10 || d.levels.some(x => typeof x !== 'string' || !x.trim())) {
      throw new Error('Diagnostic dimensions need named, descriptive ordered levels');
    }
    if (ids.includes(d.id)) throw new Error('Diagnostic IDs must be distinct from all review rubrics');
    ids.push(d.id);
  }
  const targets = config.criticality.diagnostic_targets ?? [];
  if (!Array.isArray(targets) || new Set(targets.map(t => t.dimension)).size !== targets.length) {
    throw new Error('Invalid critical diagnostic targets');
  }
  for (const target of targets) validateStyleTarget(target, config, diagnostics);
}

function validateStyleRole(config) {
  const policy = config.style_role;
  if (!policy) return;
  const dimensions = [...config.dimensions, ...diagnosticRubrics(config)];
  if (!config.potential_profundity || !policy.id
      || [...dimensions, config.criticality, config.potential_profundity].some(d => d.id === policy.id)
      || !policy.title || !policy.instructions || !policy.composition_instructions
      || !Array.isArray(policy.levels) || policy.levels.length !== 2
      || policy.levels.some(level => typeof level !== 'string' || !level.trim())
      || !Number.isFinite(policy.minimum_probability) || policy.minimum_probability <= .5 || policy.minimum_probability > 1) {
    throw new Error('Expressive role needs a separate binary rubric and composition policy');
  }
  const scaled = ['highly_memetic', 'anticipation', 'payoff'];
  for (const targets of [policy.supporting_targets, policy.composition_targets]) {
    if (!Array.isArray(targets) || targets.length !== scaled.length
        || new Set(targets.map(t => t.dimension)).size !== scaled.length
        || targets.some(t => !scaled.includes(t.dimension))) throw new Error('Role targets must cover memetic identity, anticipation and payoff');
    for (const target of targets) validateStyleTarget(target, config, dimensions);
  }
  // Optional per-axis wording for whole-mechanism questions; absent keeps the generic form.
  const axisText = policy.composition_axis_instructions;
  if (axisText !== undefined && (!axisText || typeof axisText !== 'object' || Array.isArray(axisText)
      || Object.entries(axisText).some(([id, text]) => !scaled.includes(id) || typeof text !== 'string' || !text.trim()))) {
    throw new Error('Composition axis instructions must be nonempty text for memetic identity, anticipation or payoff');
  }
  for (const support of policy.supporting_targets) {
    const leading = [...config.style_targets, ...config.criticality.diagnostic_targets].find(t => t.dimension === support.dimension);
    const composition = policy.composition_targets.find(t => t.dimension === support.dimension);
    if (!leading || support.level >= leading.level || support.minimum_probability !== leading.minimum_probability
        || composition.level !== leading.level || composition.minimum_probability !== leading.minimum_probability) {
      throw new Error('Role scaling changes supporting levels, preserving leading and composition probability bars');
    }
  }
}

/** Context gaps that forbid the supporting exemption; shared by scoring and preflight. */
export function roleContextLimits(context) {
  const unknown = (context?.unresolved ?? []).filter(ref =>
    ref.reason !== 'unresolved-or-builtin' || !knownBuiltins().has(ref.name));
  return { limited: !context || !!context.truncated || unknown.length > 0, unknown };
}

export function assessStyleRole(row, config) {
  validateStyleRole(config);
  if (!config.style_role) return null;
  const policy = config.style_role;
  const answer = validateScore({ ...row.answers?.[policy.id], type: 'score' }, policy.levels.length);
  const probability = probabilityAt(answer, 1);
  const { limited, unknown } = roleContextLimits(row.context);
  return { target: row.target, status: probability >= policy.minimum_probability ? 'leading'
    : !limited && probability <= 1 - policy.minimum_probability ? 'supporting' : 'uncertain',
    probability_leading: probability, context_limited: limited, unresolved_role_context: unknown,
    probabilities: answer.probabilities };
}

export function diagnoseStyle(rows, config) {
  validateDiagnostics(config);
  return rows.flatMap(row => diagnosticRubrics(config).map(d => {
    const required = !!config.style_role || criticalityFor(row, config).status !== 'noncritical'
      && (config.criticality.diagnostic_targets ?? []).some(t => t.dimension === d.id);
    const metadata = { target: row.target, dimension: d.id, required, advisory: !required,
      context_truncated: row.context?.truncated ?? false,
      unresolved_references: row.context?.unresolved?.length ?? 0 };
    if (metadata.context_truncated) return { ...metadata, status: 'unavailable', reason: 'context_truncated' };
    return { ...metadata, status: metadata.unresolved_references ? 'limited_context' : 'rated',
      ...validateScore({ ...row.answers?.[d.id], type: 'score' }, d.levels.length) };
  }));
}

function validateStyleTarget(target, config, dimensions = config.dimensions) {
  const dimension = dimensions.find(d => d.id === target?.dimension);
  if (!dimension || !Number.isInteger(target.level) || target.level < 1 || target.level >= dimension.levels.length
      || !Number.isFinite(target.minimum_probability) || target.minimum_probability <= 0.5 || target.minimum_probability > 1) {
    throw new Error('Invalid style target');
  }
}

function criticalityFor(row, config) {
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
  if (config.potential_profundity) validatePotential(config);
  else {
    validateStyleTarget(policy.style_target, config);
    const ordinary = config.style_targets.find(t => t.dimension === policy.style_target.dimension);
    if (policy.style_target.level <= ordinary.level || policy.style_target.minimum_probability < ordinary.minimum_probability) {
      throw new Error('Criticality must require a stricter style target');
    }
  }
  validateDiagnostics(config);
  validateStyleRole(config);
  return rows.flatMap(row => {
    const criticality = criticalityFor(row, config);
    const role = assessStyleRole(row, config);
    const strict = ['critical', 'uncertain'].includes(criticality.status);
    const diagnostics = role || strict ? policy.diagnostic_targets ?? [] : [];
    return [...config.style_targets, ...diagnostics].map(base => {
      // Preserve v3 receipts. V4 applies Galaxy brain to a separate composition.
      const support = role?.status === 'supporting' && config.style_role.supporting_targets.find(t => t.dimension === base.dimension);
      const scaled = role && config.style_role.supporting_targets.some(t => t.dimension === base.dimension);
      const target = support || (!config.potential_profundity && strict && row.kind !== 'bend_datatype'
        && base.dimension === policy.style_target.dimension ? policy.style_target : base);
      const metadata = { target: row.target, dimension: target.dimension, target_level: target.level,
        minimum_probability: target.minimum_probability, criticality_status: criticality.status,
        target_basis: scaled ? `${role.status}_role` : target !== base || diagnostics.includes(base) ? 'criticality' : 'default',
        ...(role ? { style_role: role.status } : {}),
        context_truncated: row.context?.truncated ?? false };
      if (diagnostics.includes(base) && row.context?.truncated) {
        return { ...metadata, probability_at_target: null, status: 'unavailable' };
      }
      const answer = row.answers[target.dimension];
      const rubric = [...config.dimensions, ...diagnosticRubrics(config)].find(d => d.id === target.dimension);
      validateScore({ ...answer, type: 'score' }, rubric.levels.length);
      const total = Object.values(answer.probabilities).reduce((a, b) => a + b, 0);
      const probability = Object.entries(answer.probabilities).reduce((sum, [level, p]) => sum + (Number(level) >= target.level ? p : 0), 0) / total;
      return { ...metadata,
        probability_at_target: probability, status: probability >= target.minimum_probability ? 'meets_target'
          : probability <= 1 - target.minimum_probability ? 'below_target' : 'uncertain' };
    });
  });
}

async function datatypeContext(file, path, declaration, root, snapshot) {
  if (snapshot.contextPolicy === INTERFACE_CONTEXT) return file.review.forUnit(declaration.name);
  // Retain the existing one-file datatype budget. Actual type dependencies now
  // resolve locally or produce explicit limits, rather than a blanket warning.
  file.datatypeReview ??= await createBendReview({ root, path, source: file.source,
    analysis: file.analysis, snapshot, limits: { callers: 4, files: 1, bytes: 48000 } });
  return file.datatypeReview.forUnit(declaration.name);
}

export async function prepareStyleTargets(targets, cohort, config, root = ROOT, snapshot = null) {
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
  snapshot ??= await createBendSourceSnapshot(root);
  const realRoot = await realpath(root), files = new Map(), selected = new Set(), candidates = [];
  if (snapshot.root !== realRoot) throw new Error('Bend source snapshot belongs to another workspace');
  for (const target of targets) {
    const [input, name, extra] = target.split('::');
    if (!input.endsWith('.bend') || extra !== undefined || name === '') throw new Error(`Expected file.bend or file.bend::name: ${target}`);
    const absolute = await realpath(resolve(root, input));
    if (!inside(realRoot, absolute)) throw new Error('Style targets must be inside this workspace');
    const path = relative(realRoot, absolute).split(sep).join('/');
    if (!files.has(path)) {
      const { source, analysis, source_sha256 } = await snapshot.load(path);
      if (analysis.parser_status !== 'parsed') throw new Error(`Bend target does not parse: ${path}`);
      const review = await createBendReview({ root: realRoot, path, source, analysis, snapshot });
      files.set(path, { source, source_sha256, analysis, review });
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
      const context = declaration.syntax_kind === 'bend_datatype' ? await datatypeContext(file, path, declaration, realRoot, snapshot)
        : await file.review.forUnit(declaration.qualified_name);
      const prefix = { cohort: cohort?.trim() || DEFAULT_SCOPE, name: declaration.qualified_name,
        path, declaration_kind: declaration.syntax_kind,
        source: bendDeclarationSource(file.source, declaration) };
      if (snapshot.contextPolicy === INTERFACE_CONTEXT) await fitInterfaceContext(context, snapshot, prefix);
      const state = { ...prefix, ...context.seen };
      const encodedState = JSON.stringify(state);
      if (Buffer.byteLength(encodedState) > 60000) throw new Error(`Style context too large: ${identity}`);
      candidates.push({ target: identity, path, kind: declaration.syntax_kind,
        line: declaration.line, end_line: declaration.end_line,
        source_sha256: file.source_sha256, state_sha256: hash(encodedState),
        context: context.provenance, state });
    }
  }
  if (!candidates.length) throw new Error('Ranking needs at least one parsed unit');
  return candidates;
}

export async function prepareStyleInventory(cohort, config, root = ROOT, snapshot = null) {
  const paths = [...new Set(execFileSync('git', ['ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', '*.bend'],
    { cwd: root, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }).split('\0').filter(Boolean))].sort();
  if (!paths.length) throw new Error('No project Bend files found');
  snapshot ??= await createBendSourceSnapshot(root);
  const prepared = new Array(paths.length);
  let cursor = 0, selected = 0, overLimit = false;
  async function worker() {
    while (!overLimit && cursor < paths.length) {
      const index = cursor++, path = paths[index];
      try {
        const units = await prepareStyleTargets([path], cohort, config, root, snapshot);
        prepared[index] = { units };
        selected += units.length;
        overLimit ||= selected > config.max_units;
      } catch (error) { prepared[index] = { reason: error.message }; }
    }
  }
  // Overlap independent file reads, then assemble in discovery order. Every
  // parser/context preflight still finishes before the first provider request.
  await Promise.all(Array.from({ length: Math.min(PREFLIGHT_CONCURRENCY, paths.length) }, worker));
  if (overLimit) throw new Error(`Style run limited to ${config.max_units} units; raise max_units for this inventory`);
  const candidates = [], unranked = [], empty_files = [];
  for (const [index, result] of prepared.entries()) {
    const path = paths[index];
    if (result.units) candidates.push(...result.units);
    else if (result.reason.startsWith('No applicable parsed declaration:')) empty_files.push(path);
    else unranked.push({ path, reason: result.reason });
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

const tally = items => Object.fromEntries([...items.reduce((counts, item) =>
  counts.set(item, (counts.get(item) ?? 0) + 1), new Map())].sort(([a], [b]) => a.localeCompare(b)));

function compositionPreflight(prepared) {
  const { context } = prepared.candidate;
  return { available: prepared.available, reasons: prepared.reasons, selected_files: context.selected_files,
    context_files: context.files.length, source_bytes: context.source_bytes, byte_limit: context.limits.bytes,
    unresolved_by_reason: tally(context.unresolved.map(ref => ref.reason)), unresolved: context.unresolved,
    ...(context.profile ? { context_policy: context.profile, representations: context.representations } : {}) };
}

async function readStyleReport(path) {
  const bytes = await readFile(path);
  return JSON.parse((path.endsWith('.gz') ? gunzipSync(bytes) : bytes).toString('utf8'));
}

async function prepareStyleSelection({ all = false, targets, taskPath, cohort, contextPolicy = null, packageStore = null }, root, snapshot = null, policy = null) {
  const text = policy?.text ?? await readFile(resolve(root, 'perch-style.json'), 'utf8');
  const config = policy?.config ?? JSON.parse(text);
  assessStyle([], config);
  const taskText = taskPath !== undefined ? await readFile(resolve(root, taskPath), 'utf8') : cohort;
  const taskAvailable = !!taskText?.trim() && (!config.potential_profundity || Buffer.byteLength(taskText) <= config.potential_profundity.max_task_bytes);
  const task = { origin: taskPath !== undefined ? 'task-file' : cohort !== undefined ? 'explicit-cohort' : 'missing',
    path: taskPath ?? null, sha256: taskText === undefined ? null : hash(taskText), bytes: Buffer.byteLength(taskText ?? ''),
    available: taskAvailable, reason: !taskText?.trim() ? 'missing_task_context' : !taskAvailable ? 'task_byte_limit' : null };
  const effectiveCohort = taskAvailable ? taskText : config.potential_profundity ? undefined : cohort;
  snapshot ??= await createBendSourceSnapshot(root, { contextPolicy, packageStore });
  const { candidates, inventory } = all ? await prepareStyleInventory(effectiveCohort, config, root, snapshot)
    : { candidates: await prepareStyleTargets(targets, effectiveCohort, config, root, snapshot), inventory: null };
  return { text, config, taskText, taskAvailable, task, snapshot, candidates, inventory };
}

async function readStyleManifest(path, root) {
  const realRoot = await realpath(root);
  const workspacePath = async (value, label) => {
    if (typeof value !== 'string' || !value.trim() || isAbsolute(value) || !inside(realRoot, resolve(realRoot, value))) {
      throw new Error(`Manifest ${label} must be a workspace-relative path`);
    }
    const actual = await realpath(resolve(realRoot, value));
    if (!inside(realRoot, actual)) throw new Error(`Manifest ${label} must stay inside this workspace`);
    return relative(realRoot, actual).split(sep).join('/');
  };
  path = await workspacePath(path, 'path');
  const text = await readFile(resolve(realRoot, path), 'utf8');
  const manifest = JSON.parse(text);
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  if (!object(manifest) || manifest.schema !== 1 || !Array.isArray(manifest.groups) || !manifest.groups.length
      || Object.keys(manifest).some(key => !['schema', 'groups', 'context'].includes(key))) throw new Error('Expected manifest schema 1 with nonempty groups');
  if (manifest.context !== undefined && manifest.context !== INTERFACE_CONTEXT) throw new Error('Unknown manifest context policy');
  const names = new Set(), groups = [];
  for (const group of manifest.groups) {
    if (!object(group) || typeof group.name !== 'string' || !group.name.trim() || names.has(group.name)
        || !Array.isArray(group.files) || !group.files.length
        || group.notes !== undefined && typeof group.notes !== 'string'
        || Object.keys(group).some(key => !['name', 'files', 'task', 'notes', 'selected_files'].includes(key))) {
      throw new Error('Manifest groups need unique nonempty names, nonempty files, optional task and string notes');
    }
    names.add(group.name);
    const files = [];
    for (const file of group.files) {
      if (typeof file !== 'string' || !file.endsWith('.bend') || file.includes('::')) throw new Error('Manifest files must be whole .bend files');
      const canonical = await workspacePath(file, 'file');
      if (files.includes(canonical)) throw new Error(`Duplicate manifest file in ${group.name}: ${file}`);
      files.push(canonical);
    }
    let selectedFiles;
    if (group.selected_files !== undefined) {
      if (manifest.context !== INTERFACE_CONTEXT || !Array.isArray(group.selected_files) || !group.selected_files.length) {
        throw new Error('Selected files need the interfaces-v1 context policy and a nonempty selection');
      }
      selectedFiles = [];
      for (const input of group.selected_files) {
        const file = await workspacePath(input, 'selected file');
        if (!files.includes(file) || selectedFiles.includes(file)) throw new Error('Selected files must be distinct members of the group inventory');
        selectedFiles.push(file);
      }
    }
    groups.push({ name: group.name, files,
      ...(selectedFiles ? { selected_files: selectedFiles } : {}),
      ...(group.task === undefined ? {} : { task: await workspacePath(group.task, 'task') }),
      ...(group.notes === undefined ? {} : { notes: group.notes }) });
  }
  if (manifest.context === INTERFACE_CONTEXT) {
    const covered = new Set(groups.flatMap(g => g.selected_files ?? g.files));
    if (groups.flatMap(g => g.files).some(file => !covered.has(file))) throw new Error('Manifest context inventory contains a file never selected in full');
  }
  return { path, sha256: hash(text), groups, contextPolicy: manifest.context ?? null };
}

/** Manifest groups reuse the explicit-target gate; only their composition order differs. */
async function runStyleManifest(args, {
  root = ROOT, env = process.env, fetchImpl = globalThis.fetch, loadEnv = false,
  stdout = text => console.log(text), stderr = text => console.error(text),
} = {}) {
  const offline = args.includes('--preflight');
  if (offline === args.includes('--live')) throw new Error('Choose --preflight (offline) or --live (provider review), not both');
  const switches = offline ? ['--preflight', '--json'] : ['--live', '--json', '--incremental', '--fresh'];
  const prefixes = ['--manifest=', '--group=', '--output=', '--package-store=', ...(offline ? [] : ['--jobs=', '--reuse='])];
  if (args.some(x => !switches.includes(x) && !prefixes.some(prefix => x.startsWith(prefix)))) {
    throw new Error('Manifest mode accepts named groups, not --all, explicit targets or task/cohort overrides; unknown option');
  }
  const single = prefix => {
    const values = args.filter(x => x.startsWith(prefix)).map(x => x.slice(prefix.length));
    if (values.length > 1 || values.includes('')) throw new Error(`Supply at most one nonempty ${prefix.slice(0, -1)}`);
    return values[0];
  };
  const manifestPath = single('--manifest='), groupName = single('--group='), output = single('--output='), reuse = single('--reuse=');
  const packageStore = single('--package-store=');
  const jobs = single('--jobs=');
  if (Number(args.includes('--incremental')) + Number(args.includes('--fresh')) + Number(reuse !== undefined) > 1) {
    throw new Error('Choose only one of --incremental, --fresh, or --reuse');
  }
  if (!offline && (!Number.isInteger(Number(jobs ?? env.PERCH_JOBS ?? DEFAULT_CONCURRENCY))
      || Number(jobs ?? env.PERCH_JOBS ?? DEFAULT_CONCURRENCY) < 1 || Number(jobs ?? env.PERCH_JOBS ?? DEFAULT_CONCURRENCY) > MAX_CONCURRENCY)) {
    throw new Error(`Concurrency must be 1..${MAX_CONCURRENCY}`);
  }
  const outputPath = output ? resolve(root, output) : null;
  if (outputPath && await lstat(outputPath).then(() => true, error => { if (error.code === 'ENOENT') return false; throw error; })) {
    throw new Error('Style output already exists; choose a new evidence path');
  }
  const manifest = await readStyleManifest(manifestPath, root);
  const selected = manifest.groups.filter(group => groupName === undefined || group.name === groupName);
  if (!selected.length) throw new Error(`Unknown manifest group: ${groupName}`);
  const text = await readFile(resolve(root, 'perch-style.json'), 'utf8'), config = JSON.parse(text);
  assessStyle([], config);
  if (!config.style_role) throw new Error('Manifest qualification requires a rubric with composition targets');
  if (packageStore && manifest.contextPolicy !== INTERFACE_CONTEXT) throw new Error('Package stores require interfaces-v1 context');
  const snapshot = await createBendSourceSnapshot(root, { contextPolicy: manifest.contextPolicy, packageStore }), prepared = [];
  let selectedUnits = 0;
  for (const group of selected) {
    if (manifest.contextPolicy === INTERFACE_CONTEXT) {
      for (const path of group.files) {
        const file = await snapshot.load(path);
        for (const ref of file.analysis.references.filter(r => r.kind === 'import'
          && (r.module.startsWith('./') || r.module.startsWith('../')))) {
          const dependency = await snapshot.resolveImport(path, ref.module);
          if (!group.files.includes(dependency.path)) throw new Error(`Manifest local import closure: ${group.name}: ${path} needs ${ref.module}`);
        }
      }
    }
    const selectedFiles = group.selected_files ?? group.files;
    const selection = await prepareStyleSelection({ targets: selectedFiles, taskPath: group.task }, root, snapshot, { text, config });
    selectedUnits += selection.candidates.length;
    if (selectedUnits > config.max_units) throw new Error(`Style run limited to ${config.max_units} units; narrow groups or raise max_units`);
    selection.composition = await prepareStyleComposition(selection.candidates, selection.taskAvailable ? selection.taskText : null,
      config, root, snapshot, selectedFiles);
    prepared.push({ group, selection });
  }
  const fileIdentity = (path, source_sha256) => ({ path, source_sha256, context: { files: [] } });
  const watched = [fileIdentity(manifest.path, manifest.sha256), fileIdentity('perch-style.json', hash(text)),
    ...prepared.flatMap(({ selection }) => [...selection.candidates,
      ...selection.composition.candidate.context.files.map(file => fileIdentity(file.path, file.source_sha256)),
      ...(selection.task.path ? [fileIdentity(selection.task.path, selection.task.sha256)] : [])])];
  const sourceFiles = new Map(watched.flatMap(candidate => [candidate, ...candidate.context.files])
    .map(file => [file.path, file.source_sha256]));
  const preflightChanged = await changedStyleSources(watched, root);
  if (preflightChanged.length) throw new Error(`Source changed during style preflight: ${preflightChanged.join(', ')}`);
  if (!offline && loadEnv) {
    try { process.loadEnvFile(resolve(root, '.env')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const prior = reuse ? await readStyleReport(resolve(root, reuse)) : null;
  if (prior && (prior.schema !== 1 || prior.command !== 'style-manifest' || prior.mode !== 'manifest'
      || prior.rubric_sha256 !== hash(text) || prior.parser !== BEND_PARSER_PROFILE
      || prior.requested_model !== (env.PERCH_MODEL_ID || 'jev-latest')
      || prior.endpoint_sha256 !== styleEndpoint(env.PERCH_BASE_URL || undefined).sha256 || !Array.isArray(prior.groups))) {
    throw new Error('Manifest reuse requires the same rubric, parser, requested model and endpoint identity');
  }
  const groups = [];
  let dispatchFailure = null;
  for (const { group, selection } of prepared) {
    const old = prior?.groups.find(item => item.name === group.name);
    const childArgs = [offline ? '--preflight' : '--live', '--json', ...(group.selected_files ?? group.files),
      ...(group.task ? [`--task=${group.task}`] : []),
      ...args.filter(x => ['--incremental', '--fresh'].includes(x) || x.startsWith('--jobs=')),
      ...(old ? [`--reuse=${reuse}`] : [])];
    let report;
    let code;
    try {
      code = await runStyleRanking(childArgs, { root, env, fetchImpl, selection, reuseReport: old,
        stdout: value => { report = JSON.parse(value); }, stderr: value => stderr(`[${group.name}] ${value}`) });
    } catch (error) {
      if (offline) throw error;
      dispatchFailure = { group: group.name, reason: error.message };
      break;
    }
    groups.push({ name: group.name, files: group.files, notes: group.notes ?? null,
      ...(group.selected_files ? { selected_files: group.selected_files } : {}), ...report });
    if (!offline && code === 1) break;
  }
  const changed_sources = await changedStyleSources(watched, root);
  const models = [...new Set(groups.flatMap(group => group.model_resolution?.resolved_models ?? []))];
  const failures = groups.filter(group => ['failed', 'incomplete'].includes(group.status));
  const skipped = selected.slice(groups.length).map(group => group.name);
  const failure = dispatchFailure ? 'group_dispatch_failed' : failures.length ? 'group_review_failed'
    : models.length > 1 ? 'model_changed_between_groups' : null;
  const sum = field => groups.reduce((total, group) => total + field(group), 0);
  const qualified = !offline && !failure && !skipped.length && !changed_sources.length
    && groups.every(group => group.qualification.fully_qualified);
  const summary = { groups: selected.length, groups_completed: offline ? groups.length : groups.filter(group => group.status === 'completed').length,
    units: selectedUnits, files: new Set(selected.flatMap(group => group.files)).size,
    ...(offline ? {
      truncated_units: sum(group => group.summary.truncated_units),
      supporting_role_impossible: sum(group => group.summary.supporting_role_impossible),
      compositions_available: sum(group => Number(group.composition.available)),
    } : {
      groups_qualified: sum(group => Number(group.qualification.fully_qualified)),
      ranked: sum(group => group.coverage.ranked),
      declarations_meeting_targets: sum(group => group.style_summary.meets_all),
      compositions_meeting_targets: sum(group => Number(group.qualification.composition_requirement_met)),
    }) };
  const blockers = offline ? sum(group => group.structural_blockers) + changed_sources.length : null;
  const report = { schema: 1, command: offline ? 'style-preflight' : 'style-manifest', mode: 'manifest',
    manifest: { path: manifest.path, sha256: manifest.sha256, groups: manifest.groups.map(group => group.name),
      selected_groups: selected.map(group => group.name), scope: groupName === undefined ? 'entire-manifest' : 'selected-group' },
    rubric_sha256: hash(text), rubric_version: config.version, parser: BEND_PARSER_PROFILE,
    preflight_snapshot: snapshot.stats,
    source_snapshot: [...sourceFiles].sort(([a], [b]) => a.localeCompare(b)).map(([path, source_sha256]) => ({ path, source_sha256 })), summary,
    ...(offline ? { structural_blockers: blockers } : { at: new Date().toISOString(), status: failure ? 'failed' : 'completed', advisory: true,
      qualification: { status: qualified ? 'meets_target' : 'attention', fully_qualified: qualified,
        manifest_fully_qualified: qualified && groupName === undefined },
      requested_model: env.PERCH_MODEL_ID || 'jev-latest', endpoint_sha256: styleEndpoint(env.PERCH_BASE_URL || undefined).sha256,
      model_resolution: { resolved_models: models }, failure, dispatch_failure: dispatchFailure, skipped_groups: skipped }),
    provider_requests: sum(group => group.provider_requests), provider_responses: sum(group => group.provider_responses ?? 0),
    source_freshness: { status: changed_sources.length ? 'changed-since-preflight' : 'current', changed_sources },
    groups, note: 'Qualification covers exactly the selected manifest groups, each with its own declaration and composition obligations. Shared declarations count once per group. Local collaborators retain the existing bounded context and closure checks. Structural preflight is not a style rating or semantic acceptance.' };
  const encoded = JSON.stringify(report, null, 2) + '\n';
  if (!offline) {
    const receipt = resolve(root, '.perch/usage', `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID()}.json`);
    await mkdir(dirname(receipt), { recursive: true, mode: 0o700 });
    await writeFile(receipt, encoded, { mode: 0o600, flag: 'wx' });
  }
  if (outputPath) {
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, outputPath.endsWith('.gz') ? gzipSync(encoded) : encoded, { mode: 0o600, flag: 'wx' });
  }
  if (args.includes('--json')) stdout(encoded.slice(0, -1));
  else {
    for (const group of groups) stdout(offline
      ? `${group.name}: ${group.summary.units} declarations; ${group.summary.truncated_units} truncated; ${group.summary.supporting_role_impossible} role-limited; composition ${group.composition.available ? 'available' : group.composition.reasons.join(',')} (${group.composition.source_bytes}/${group.composition.byte_limit} bytes).`
      : `${group.name}: ${group.style_summary.meets_all}/${group.coverage.selected} declarations meet targets; composition ${group.composition.assessment.status}; qualification ${group.qualification.status}.`);
    stdout(offline ? `Manifest preflight: ${summary.groups} groups; ${blockers} structural blockers; 0 provider requests.`
      : `Manifest qualification (${report.manifest.scope}): ${report.qualification.status}; ${summary.groups_qualified}/${summary.groups} groups; ${report.provider_requests} provider requests.`);
    if (failure) stderr(`Manifest review failed: ${failure}; skipped groups: ${skipped.join(', ') || 'none'}.`);
    if (changed_sources.length) stderr(`Changed since preflight: ${changed_sources.join(', ')}.`);
  }
  return offline ? blockers ? 3 : 0 : failure ? 1 : qualified ? 0 : 3;
}

/**
 * Offline structural preflight. It prepares the same candidate states, contexts
 * and composition groups as a live run (request bodies are not built), then
 * reports what can never pass regardless of any rating:
 * truncated contexts (Anticipation/Payoff unavailable), context gaps that
 * forbid the supporting role, unavailable compositions and unranked files.
 * No credentials, environment file, cache or provider are touched.
 */
export async function runStylePreflight(args, { root = ROOT, stdout = text => console.log(text), selection = null } = {}) {
  if (args.some(x => x.startsWith('--manifest='))) {
    if (args.includes('--live')) throw new Error('Preflight never contacts a provider; --live is not allowed');
    return runStyleManifest(['--preflight', ...args], { root, stdout });
  }
  const known = x => ['--preflight', '--json', '--all'].includes(x) || ['--cohort=', '--task=', '--output=', '--context=', '--package-store='].some(p => x.startsWith(p));
  if (args.some(x => x.startsWith('--') && !known(x))) throw new Error('Unknown preflight option; --preflight never contacts a provider');
  const all = args.includes('--all'), targets = args.filter(x => !x.startsWith('--'));
  if (all === targets.length > 0) throw new Error('Use --preflight with either --all or explicit targets');
  // Same option rules as a live run: one value each; only --task= and --output= must be nonempty.
  const single = (prefix, allowEmpty = false) => {
    const values = args.filter(x => x.startsWith(prefix)).map(x => x.slice(prefix.length));
    if (values.length > 1) throw new Error(`Supply at most one ${prefix.slice(0, -1)}`);
    if (!allowEmpty && values.includes('')) throw new Error(`Supply a nonempty ${prefix.slice(0, -1)}`);
    return values[0];
  };
  const cohort = single('--cohort=', true), taskPath = single('--task='), output = single('--output=');
  const contextPolicy = single('--context='), packageStore = single('--package-store=');
  if (packageStore && contextPolicy !== INTERFACE_CONTEXT) throw new Error('Package stores require interfaces-v1 context');
  const outputPath = output ? resolve(root, output) : null;
  if (outputPath && await lstat(outputPath).then(() => true, error => { if (error.code === 'ENOENT') return false; throw error; })) {
    throw new Error('Preflight output already exists; choose a new path');
  }
  const { text, config, taskText, taskAvailable, task, snapshot, candidates, inventory } = selection
    ?? await prepareStyleSelection({ all, targets, taskPath, cohort, contextPolicy, packageStore }, root);
  if (!candidates.length) throw new Error('No rankable parsed declarations');

  const units = candidates.map(candidate => {
    const { limited, unknown } = roleContextLimits(candidate.context);
    const notes = candidate.context?.unresolved ?? [];
    return { target: candidate.target, kind: candidate.kind, line: candidate.line,
      state_bytes: Buffer.byteLength(JSON.stringify(candidate.state)),
      truncated: !!candidate.context?.truncated,
      // Caller (or datatype-consumer) and byte limits truncate without an unresolved note.
      limit_reasons: [...new Set(notes.filter(ref => ref.reason.endsWith('-limit')).map(ref => ref.reason))],
      diagnostics_available: !candidate.context?.truncated,
      supporting_role_possible: !limited,
      role_context_gaps: unknown.map(({ path, name, reason }) => ({ path, name, reason })),
      ...(candidate.context?.profile === INTERFACE_CONTEXT ? { context_policy: INTERFACE_CONTEXT,
        summarized: candidate.context.summarized, source_bytes: candidate.context.source_bytes } : {}) };
  });
  const byFile = new Map();
  for (const candidate of candidates) {
    const path = candidate.path ?? candidate.target.split('::')[0];
    if (!byFile.has(path)) byFile.set(path, []);
    byFile.get(path).push(candidate);
  }
  const compositionTask = taskAvailable ? taskText : null;
  // A role policy requires composition whatever the ratings; otherwise only high potential does.
  const compositionRequired = config.style_role ? 'always' : config.potential_profundity ? 'if_high_potential' : null;
  // Project mode has no declared group, exactly as in a live run; each file is
  // additionally reported as its own candidate group.
  const composition = !compositionRequired ? null
    : all ? { required: compositionRequired, available: false, reasons: ['explicit_selected_group_required'] }
    : { required: compositionRequired, ...compositionPreflight(selection?.composition
      ?? await prepareStyleComposition(candidates, compositionTask, config, root, snapshot)) };
  const fileGroups = config.potential_profundity && all ? await mapConcurrent([...byFile], PREFLIGHT_CONCURRENCY, async ([path, group]) =>
    ({ path, units: group.length, ...compositionPreflight(await prepareStyleComposition(group, compositionTask, config, root, snapshot)) })) : null;

  const truncated = units.filter(unit => unit.truncated);
  const roleLimited = units.filter(unit => !unit.supporting_role_possible);
  const summary = {
    units: units.length, files: byFile.size,
    unranked_files: inventory?.unranked.length ?? 0, empty_files: inventory?.empty_files.length ?? 0,
    truncated_units: truncated.length,
    truncated_by_limit: tally(truncated.flatMap(unit => unit.limit_reasons.length ? unit.limit_reasons : ['caller-or-byte-limit'])),
    supporting_role_impossible: roleLimited.length,
    role_gap_units_by_reason: tally(roleLimited.flatMap(unit => [...new Set([
      ...(unit.truncated ? ['truncated-context'] : []), ...unit.role_context_gaps.map(gap => gap.reason)])])),
    max_state_bytes: Math.max(0, ...units.map(unit => unit.state_bytes)),
    ...(composition ? { composition_available: composition.available, composition_reasons: composition.reasons } : {}),
    ...(fileGroups ? { single_file_groups_available: fileGroups.filter(group => group.available).length,
      single_file_groups_by_reason: tally(fileGroups.flatMap(group => group.reasons)) } : {}),
  };
  const blockers = summary.truncated_units + summary.unranked_files
    + (composition?.required === 'always' && !composition.available ? 1 : 0);
  const report = { schema: 1, command: 'style-preflight', mode: all ? 'project' : 'targets',
    provider_requests: 0, rubric_sha256: hash(text), rubric_version: config.version, parser: BEND_PARSER_PROFILE,
    task, summary, structural_blockers: blockers, inventory, composition, file_groups: fileGroups, units,
    note: 'Structural preflight only: no ratings or request bodies. A truncated unit cannot pass (Anticipation/Payoff unavailable); a unit without complete role context is held to the leading targets; an unavailable required composition prevents qualification. Project mode has no declared group, as in a live run; single-file groups are reported for planning explicit groups.' };
  const encoded = JSON.stringify(report, null, 2) + '\n';
  if (outputPath) {
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, outputPath.endsWith('.gz') ? gzipSync(encoded) : encoded, { flag: 'wx' });
  }
  if (args.includes('--json')) stdout(encoded.slice(0, -1));
  else {
    stdout(`Style preflight (offline, 0 provider requests): ${summary.units} declarations in ${summary.files} files; parser ${BEND_PARSER_PROFILE}.`);
    stdout(`Task: ${task.available ? `${task.origin} (${task.bytes} bytes)` : `unavailable (${task.reason})`}.`);
    if (inventory) stdout(`Unranked files: ${summary.unranked_files}; files without declarations: ${summary.empty_files}.`);
    stdout(`Truncated contexts (Anticipation/Payoff unavailable, cannot pass): ${summary.truncated_units} ${JSON.stringify(summary.truncated_by_limit)}.`);
    stdout(`Supporting role impossible (incomplete role context): ${summary.supporting_role_impossible} ${JSON.stringify(summary.role_gap_units_by_reason)}.`);
    if (composition) stdout(`Composition (required ${composition.required}): ${composition.available ? 'available' : `unavailable [${composition.reasons.join(', ')}]`}${
      composition.source_bytes === undefined ? '' : `; ${composition.source_bytes}/${composition.byte_limit} bytes; unresolved ${JSON.stringify(composition.unresolved_by_reason)}`}.`);
    if (fileGroups) stdout(`Single-file composition groups available: ${summary.single_file_groups_available}/${fileGroups.length} ${JSON.stringify(summary.single_file_groups_by_reason)}.`);
    for (const unit of truncated) stdout(`truncated: ${unit.target} ${unit.limit_reasons.join(',') || 'caller-or-byte-limit'}`);
    for (const file of inventory?.unranked ?? []) stdout(`unranked: ${file.path} (${file.reason})`);
  }
  return blockers ? 3 : 0;
}

export async function evaluateStyle(candidates, config, {
  env = process.env, fetchImpl = globalThis.fetch, transport = { requests: 0, responses: 0 },
  concurrency = DEFAULT_CONCURRENCY, expectedModel = null, onProgress = () => {}, onRow = () => {},
  rubrics: rubricOverride = null,
} = {}) {
  const key = env.PERCH_API_KEY || env.TYPESAFE_API_KEY;
  if (!key) throw new Error('PERCH_API_KEY is not set');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > MAX_CONCURRENCY) throw new Error(`Concurrency must be 1..${MAX_CONCURRENCY}`);
  assessStyle([], config);
  const rows = new Array(candidates.length);
  let cursor = 0, failure = null, inFlight = 0, model = expectedModel, completed = 0;
  const endpoint = styleEndpoint(env.PERCH_BASE_URL || undefined), requestedModel = env.PERCH_MODEL_ID || 'jev-latest';
  async function evaluate(candidate) {
    const { rubrics, body: requestBody } = rubricOverride ? scoreRequest(candidate, rubricOverride, requestedModel)
      : styleRequest(candidate, config, requestedModel);
    const started = performance.now();
    transport.requests++;
    const response = await fetchImpl(endpoint.url, {
      method: 'POST', signal: AbortSignal.timeout(30000),
      headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
      body: requestBody,
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
      transport.peak_in_flight = Math.max(transport.peak_in_flight ?? 0, ++inFlight);
      try {
        rows[index] = await evaluate(candidates[index]);
        onRow(rows[index]);
        if (model && rows[index].model !== model) throw new Error('Model changed during comparison; rankings are not comparable');
        model ??= rows[index].model;
        onProgress(++completed, candidates.length);
      } catch (error) { failure ??= error; }
      finally { inFlight--; }
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, candidates.length) }, worker));
  if (failure) throw failure;
  return rows;
}

export async function runStyleRanking(args, {
  root = ROOT, env = process.env, fetchImpl = globalThis.fetch, loadEnv = false,
  stdout = text => console.log(text), stderr = text => console.error(text),
  selection = null, reuseReport = null,
} = {}) {
  if (args.some(x => x.startsWith('--manifest='))) return runStyleManifest(args, { root, env, fetchImpl, loadEnv, stdout, stderr });
  // Structural preflight is offline: dispatch before any environment or provider setup.
  if (args.includes('--preflight')) {
    if (args.includes('--live')) throw new Error('Choose --preflight (offline) or --live (provider review), not both');
    return runStylePreflight(args, { root, stdout, selection });
  }
  const invoked = performance.now();
  const cohort = args.find(x => x.startsWith('--cohort='))?.slice(9);
  const taskPath = args.find(x => x.startsWith('--task='))?.slice(7);
  const output = args.find(x => x.startsWith('--output='))?.slice(9);
  const reuse = args.find(x => x.startsWith('--reuse='))?.slice(8);
  const contextPolicy = args.find(x => x.startsWith('--context='))?.slice(10);
  const packageStore = args.find(x => x.startsWith('--package-store='))?.slice(16);
  const incremental = args.includes('--incremental'), fresh = args.includes('--fresh');
  const all = args.includes('--all');
  const concurrency = Number(args.find(x => x.startsWith('--jobs='))?.slice(7) ?? env.PERCH_JOBS ?? DEFAULT_CONCURRENCY);
  const known = x => ['--live', '--json', '--all', '--incremental', '--fresh'].includes(x) || ['--cohort=', '--task=', '--output=', '--jobs=', '--reuse=', '--context=', '--package-store='].some(p => x.startsWith(p));
  if (args.some(x => x.startsWith('--') && !known(x))) throw new Error('Unknown style option');
  if (packageStore && contextPolicy !== INTERFACE_CONTEXT) throw new Error('Package stores require interfaces-v1 context');
  for (const key of ['--context=', '--package-store=']) if (args.includes(key) || args.filter(x => x.startsWith(key)).length > 1) {
    throw new Error(`Supply at most one nonempty ${key.slice(0, -1)}`);
  }
  if (!args.includes('--live')) throw new Error('Use --live file.bend::name, file.bend, or --live --all to rank project Bend declarations (or --preflight for the offline structural check)');
  if (Number(incremental) + Number(fresh) + Number(reuse !== undefined) > 1) throw new Error('Choose only one of --incremental, --fresh, or --reuse');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > MAX_CONCURRENCY) throw new Error(`Concurrency must be 1..${MAX_CONCURRENCY}`);
  const targets = args.filter(x => !x.startsWith('--'));
  if (all && targets.length) throw new Error('Use --all or explicit targets, not both');
  if (args.some(x => x === '--output=') || args.filter(x => x.startsWith('--output=')).length > 1
      || args.filter(x => x.startsWith('--cohort=')).length > 1 || args.filter(x => x.startsWith('--task=')).length > 1
      || taskPath === '') throw new Error('Supply one cohort, at most one task file and at most one output path');
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
  const { text, config, taskText, taskAvailable, task, snapshot: sourceSnapshot, candidates, inventory } = selection
    ?? await prepareStyleSelection({ all, targets, taskPath, cohort, contextPolicy, packageStore }, root);
  if (!candidates.length) throw new Error('No rankable parsed declarations');
  const composition = selection?.composition ?? (config.potential_profundity && !all ? await prepareStyleComposition(candidates, taskAvailable ? taskText : null, config, root, sourceSnapshot)
    : { available: false, reasons: ['explicit_selected_group_required'], candidate: null });
  const preflightChanged = await changedStyleSources(candidates, root);
  if (preflightChanged.length) throw new Error(`Source changed during style preflight: ${preflightChanged.join(', ')}`);
  if (loadEnv) {
    try { process.loadEnvFile(resolve(root, '.env')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const at = new Date().toISOString(), start = performance.now();
  const requestedModel = env.PERCH_MODEL_ID || 'jev-latest', endpoint = styleEndpoint(env.PERCH_BASE_URL || undefined);
  const providerEnv = { ...env, PERCH_MODEL_ID: requestedModel, PERCH_BASE_URL: endpoint.url };
  const transport = { requests: 0, responses: 0, peak_in_flight: 0 };
  const reused = new Map(), completed_rows = new Map();
  const cacheIdentity = {
    parser: BEND_PARSER_PROFILE, rubric_sha256: hash(text), requested_model: requestedModel, endpoint_sha256: endpoint.sha256,
    context_contract_sha256: hash(await readFile(new URL('./perch-bend-context.mjs', import.meta.url))),
  };
  const cache = incremental || fresh ? createStyleAnswerCache(root, cacheIdentity) : null;
  const auxiliary = {}, auxiliaryCaches = [];
  let prior = null;
  const requestHashes = cache ? new Map(candidates.map(candidate => [candidate.target, hash(styleRequest(candidate, config, requestedModel).body)])) : null;
  if (incremental) {
    const saved = await mapConcurrent(candidates, PREFLIGHT_CONCURRENCY, candidate => cache.read(candidate, requestHashes.get(candidate.target), answers =>
      Object.fromEntries(reviewRubrics(config, candidate.kind, candidate.context).map(d =>
        [d.id, validateScore({ ...answers?.[d.id], type: 'score' }, d.levels.length)]))));
    for (const row of saved) if (row) reused.set(row.target, row);
  }
  if (reuse) {
    prior = reuseReport ?? await readStyleReport(resolve(root, reuse));
    if (prior.command !== 'style-rank' || prior.schema !== 2 || prior.rubric_sha256 !== hash(text)
        || prior.parser !== BEND_PARSER_PROFILE || prior.requested_model !== requestedModel || prior.endpoint_sha256 !== endpoint.sha256) {
      throw new Error('Style reuse requires the same rubric, parser, requested model and endpoint identity');
    }
    const saved = new Map([...(prior.rows ?? []), ...(prior.completed_rows ?? [])].map(r => [r.target, r]));
    for (const candidate of candidates) {
      const row = saved.get(candidate.target);
      if (!row || row.kind !== candidate.kind || row.state_sha256 !== candidate.state_sha256 || row.source_sha256 !== candidate.source_sha256
          || JSON.stringify(row.context) !== JSON.stringify(candidate.context)) continue;
      for (const d of reviewRubrics(config, candidate.kind, candidate.context)) validateScore({ ...row.answers?.[d.id], type: 'score' }, d.levels.length);
      if (typeof row.model !== 'string' || !row.model) throw new Error('Missing resolved model in reused row');
      reused.set(row.target, row);
    }
  }
  const pending = candidates.filter(c => !reused.has(c.target));
  const prepared = performance.now();
  let rows = [], failure = null;
  let potential = config.potential_profundity ? assessPotentialProfundity(null, config, { available: false, reason: task.reason }) : null;
  let compositionAssessment = { status: 'unavailable', reason: 'potential_not_established', probability_at_target: null };
  let compositionTargets = config.style_role?.composition_targets ?? [];
  const auxiliaryModels = () => Object.values(auxiliary).flatMap(value => value.row?.model ? [value.row.model] : []);
  async function reviewAuxiliary(phase, candidate, rubrics) {
    const request = scoreRequest(candidate, rubrics, requestedModel), requestHash = hash(request.body);
    const phaseCache = incremental || fresh ? createStyleAnswerCache(root, { ...cacheIdentity, phase,
      scoring_contract_sha256: hash(await readFile(fileURLToPath(import.meta.url))) }) : null;
    const validate = answers => Object.fromEntries(rubrics.map(d => [d.id, validateScore({ ...answers?.[d.id], type: 'score' }, d.levels.length)]));
    let row = incremental ? await phaseCache.read(candidate, requestHash, validate) : null;
    const old = prior?.[phase === 'potential' ? 'potential_profundity' : 'composition']?.review;
    if (!row && old?.row && old.request_sha256 === requestHash && old.row.state_sha256 === candidate.state_sha256
        && old.row.source_sha256 === candidate.source_sha256 && JSON.stringify(old.row.context) === JSON.stringify(candidate.context)) {
      if (typeof old.row.model !== 'string' || !old.row.model) throw new Error('Missing resolved model in reused task/composition judgment');
      row = { ...old.row, answers: validate(old.row.answers) };
    }
    const reusedAnswer = !!row;
    auxiliary[phase] = { request: JSON.parse(request.body), request_sha256: requestHash,
      state_sha256: candidate.state_sha256, requested_model: requestedModel, endpoint_sha256: endpoint.sha256,
      reused: reusedAnswer, row, cache: phaseCache?.stats ?? null };
    if (!row) {
      const expected = [...auxiliaryModels(), ...reused.values()].map(value => typeof value === 'string' ? value : value.model);
      [row] = await evaluateStyle([candidate], config, { env: providerEnv, fetchImpl, transport, concurrency: 1,
        rubrics, expectedModel: expected[0] ?? null, onRow: value => { auxiliary[phase].row = value; } });
      auxiliary[phase].row = row;
      if (phaseCache) auxiliaryCaches.push({ cache: phaseCache, candidate, requestHash, row });
    }
    return row;
  }
  try {
    if (config.potential_profundity && taskAvailable) {
      const { candidate } = potentialProfundityRequest(taskText, config, requestedModel);
      const row = await reviewAuxiliary('potential', candidate, [config.potential_profundity]);
      potential = assessPotentialProfundity(row.answers[config.potential_profundity.id], config);
      if (potential.status === 'low') compositionAssessment = { status: 'not_required', reason: 'low_task_potential', probability_at_target: null };
    }
    compositionTargets = [...(config.style_role?.composition_targets ?? []),
      ...(potential?.status === 'high' ? [config.potential_profundity.style_target] : [])];
    if (compositionTargets.length) {
      if (!composition.available) compositionAssessment = { status: 'unavailable', reason: composition.reasons.join(','), probability_at_target: null };
      else {
        const rubrics = compositionTargets.map(target => {
          const rubric = [...config.dimensions, ...diagnosticRubrics(config)].find(d => d.id === target.dimension);
          return { ...rubric, instructions: target.dimension === config.potential_profundity.style_target.dimension
            ? 'Rate the COMPLETE collaborating mechanism in the supplied source group, using the contract. '
              + 'Apply the ordered conceptual-compression levels to the composition, not to isolated helpers or an average of their scores. '
              + 'Trace what the actual mechanism explains; no missing implementation or claimed brilliance earns credit.'
            : [config.style_role.composition_instructions, config.style_role.composition_axis_instructions?.[target.dimension],
              `Apply the ${rubric.title} levels below to the entire mechanism as a leading expression.`].filter(Boolean).join(' ') };
        });
        const composed = await reviewAuxiliary('composition', composition.candidate, rubrics);
        const assessments = compositionTargets.map(target => {
          const probability = probabilityAt(composed.answers[target.dimension], target.level);
          return { dimension: target.dimension, target_level: target.level, minimum_probability: target.minimum_probability,
            probability_at_target: probability, status: probability >= target.minimum_probability ? 'meets_target'
              : probability <= 1 - target.minimum_probability ? 'below_target' : 'uncertain' };
        });
        compositionAssessment = config.style_role ? { assessments,
          status: assessments.every(a => a.status === 'meets_target') ? 'meets_target'
            : assessments.some(a => a.status === 'below_target') ? 'below_target' : 'uncertain' } : assessments[0];
      }
    }
    const models = new Set([...reused.values()].map(row => row.model));
    auxiliaryModels().forEach(model => models.add(model));
    if (models.size > 1) throw new Error('Model changed during review; ratings are not comparable');
    const fresh = pending.length ? await evaluateStyle(pending, config, { env: providerEnv, fetchImpl, transport, concurrency, expectedModel: models.values().next().value,
    onProgress: (done, total) => { if (all && (done % 100 === 0 || done === total)) stderr(`Style review: ${done}/${total} declarations`); },
    onRow: row => completed_rows.set(row.target, row),
    }) : [];
    const byTarget = new Map([...reused, ...fresh.map(row => [row.target, row])]);
    rows = candidates.map(c => byTarget.get(c.target));
    if (new Set(rows.map(r => r.model)).size !== 1) throw new Error('Model changed during review; ratings are not comparable');
  }
  catch (error) { failure = error.message; }
  if (failure) rows = [];
  const evaluated = performance.now();
  const compositionFiles = (composition.candidate?.context.files ?? []).map(file => ({ ...file, context: { files: [] } }));
  const changed_sources = await changedStyleSources([...candidates, ...compositionFiles], root);
  if (taskPath !== undefined && await readFile(resolve(root, taskPath)).then(hash).catch(() => null) !== task.sha256) changed_sources.push(taskPath);
  const freshnessChecked = performance.now();
  const resolvedModels = new Set([...reused.values(), ...completed_rows.values()].map(row => row.model));
  auxiliaryModels().forEach(model => resolvedModels.add(model));
  const cachePersistence = changed_sources.length ? 'source-stale' : resolvedModels.size > 1 ? 'model-drift' : 'eligible';
  if (cache && cachePersistence === 'eligible') {
    await mapConcurrent(candidates.filter(candidate => completed_rows.has(candidate.target)), PREFLIGHT_CONCURRENCY,
      candidate => cache.write(candidate, requestHashes.get(candidate.target), completed_rows.get(candidate.target), at));
  }
  if (cachePersistence === 'eligible') for (const item of auxiliaryCaches) await item.cache.write(item.candidate, item.requestHash, item.row, at);
  const persisted = performance.now();
  const assessments = failure ? [] : assessStyle(rows, config);
  const criticality = failure ? [] : rows.map(row => criticalityFor(row, config));
  const roles = failure || !config.style_role ? [] : rows.map(row => assessStyleRole(row, config));
  const diagnostics = failure ? [] : diagnoseStyle(rows, config);
  const counts = { meets_target: 0, below_target: 0, uncertain: 0, unavailable: 0 };
  const targetedDiagnostics = diagnosticRubrics(config).filter(d => (config.criticality.diagnostic_targets ?? []).some(t => t.dimension === d.id));
  const by_axis = [...config.dimensions, ...targetedDiagnostics].map(d => ({ id: d.id, title: d.title,
    required_for: config.dimensions.includes(d) ? 'all' : config.style_role ? 'all_by_role' : 'critical_or_uncertain', ...counts }));
  const axes = new Map(by_axis.map(axis => [axis.id, axis])), needsReview = new Set(), requiredByTarget = new Map();
  for (const assessment of assessments) {
    counts[assessment.status]++;
    axes.get(assessment.dimension)[assessment.status]++;
    if (assessment.status !== 'meets_target') needsReview.add(assessment.target);
    if (assessment.target_basis === 'criticality' || assessment.target_basis.endsWith('_role')) {
      if (!requiredByTarget.has(assessment.target)) requiredByTarget.set(assessment.target, []);
      requiredByTarget.get(assessment.target).push(assessment);
    }
  }
  const meets_all = rows.length - needsReview.size;
  const potentialResolved = potential && ['low', 'high'].includes(potential.status);
  // User preference: only confidently high task potential adds a requirement.
  // Missing/uncertain potential stays visible as advisory context.
  const compositionRequired = !!config.style_role || potential?.status === 'high';
  const compositionMet = !compositionRequired || composition.available && compositionAssessment.status === 'meets_target';
  const qualified = !failure && !inventory?.unranked.length && !changed_sources.length && rows.length === candidates.length
    && meets_all === rows.length && (!config.potential_profundity || compositionMet);
  const qualification = { status: qualified ? 'meets_target' : 'attention', declarations_meet_targets: rows.length > 0 && meets_all === rows.length,
    potential_resolved: !!potentialResolved, composition_context_complete: composition.available,
    potential_advisory: !potentialResolved, composition_required: compositionRequired,
    composition_requirement_met: !!compositionMet, fully_qualified: qualified };
  const report = { schema: 2, command: 'style-rank', at, cohort: cohort || null,
    mode: all ? 'project' : 'targets', inventory, rubric_sha256: hash(text), rubric_version: config.version,
    preflight_snapshot: sourceSnapshot.stats,
    parser: BEND_PARSER_PROFILE, status: failure ? 'failed' : inventory?.unranked.length ? 'incomplete' : 'completed', advisory: true,
    coverage: { selected: candidates.length, ranked: rows.length, unranked_files: inventory?.unranked.length ?? 0 },
    reused_from: reuse || null, reused_units: reused.size,
    incremental_cache: cache ? { mode: fresh ? 'fresh' : 'incremental', ...cache.stats, persistence: cachePersistence } : null,
    completed_rows: failure ? candidates.flatMap(candidate => {
      const row = reused.get(candidate.target) ?? completed_rows.get(candidate.target);
      return row ? [row] : [];
    }) : [],
    style_targets: config.style_targets, style_summary: { ...counts, meets_all, needs_review: rows.length - meets_all, by_axis }, assessments,
    ...(config.potential_profundity ? { potential_profundity: { policy: config.potential_profundity, task, assessment: potential, review: auxiliary.potential ?? null },
      composition: { available: composition.available, reasons: composition.reasons, context: composition.candidate?.context ?? null,
        required: compositionRequired, galaxy_required: potential.status === 'high', targets: compositionTargets,
        assessment: compositionAssessment, review: auxiliary.composition ?? null }, qualification } : {}),
    ...(config.style_role ? { style_role: { policy: config.style_role, assessments: roles } } : {}),
    criticality: { policy: config.criticality, assessments: criticality },
    diagnostics: { required_for: config.style_role ? 'all_by_role' : 'critical_or_uncertain', targets: config.criticality.diagnostic_targets ?? [],
      dimensions: diagnosticRubrics(config).map(({ id, title, levels }) => ({ id, title, levels })),
      assessments: diagnostics },
    source_freshness: { status: changed_sources.length ? 'changed-since-preflight' : 'current', changed_sources },
    typechecked: false, behavioral_equivalence_checked: false,
    requested_model: requestedModel, endpoint_sha256: endpoint.sha256, failure,
    model_resolution: { resolved_models: [...resolvedModels], cached_answers: reused.size + Object.values(auxiliary).filter(value => value.reused).length, current_responses: transport.responses,
      verification: reused.size || Object.values(auxiliary).some(value => value.reused) ? 'cached-answers-unverified' : transport.responses ? 'provider-response-observed' : 'unavailable',
      note: 'Cache entries are partitioned by requested model and endpoint. Reused resolved model IDs do not verify the current version of a moving alias. Use --fresh to refresh selected answers.' },
    concurrency, provider_peak_in_flight: transport.peak_in_flight,
    provider_requests: transport.requests, provider_responses: transport.responses,
    targets: candidates.map(({ state, ...metadata }) => metadata),
    elapsed_ms: Math.round(performance.now() - start), rows,
    note: 'Each parsed declaration is rated against its own task, then sorted on each rubric. Alternatives and a shared contract are not required. Rank is advisory taste, not correctness or task difficulty. Confidence describes distribution concentration; near ties are not statistical significance. Rankings describe the recorded source snapshot.',
    rankings: failure ? [] : rankRows(rows, config.dimensions, config.near_tie_gap) };
  const aggregated = performance.now();
  report.timings = {
    preflight_ms: Math.round(start - invoked), reuse_ms: Math.round(prepared - start),
    evaluation_ms: Math.round(evaluated - prepared), freshness_ms: Math.round(freshnessChecked - evaluated),
    cache_write_ms: Math.round(persisted - freshnessChecked), aggregation_ms: Math.round(aggregated - persisted), total_ms: Math.round(aggregated - invoked),
    scope: 'Invocation through report assembly; excludes serialization, receipt writes and output. elapsed_ms retains its post-preflight scope before rankings.',
  };
  const encoded = JSON.stringify(report, null, 2) + '\n';
  // Manifest orchestration writes one aggregate receipt containing every group.
  const receipt = selection ? null : resolve(root, '.perch/usage', `${at.replaceAll(':', '-')}-${randomUUID()}.json`);
  if (receipt) {
    await mkdir(dirname(receipt), { recursive: true, mode: 0o700 });
    await writeFile(receipt, encoded, { mode: 0o600, flag: 'wx' });
  }
  const receiptNote = receipt ? ` Receipt: ${relative(root, receipt)}` : '';
  if (outputPath) {
    await writeFile(outputPath, outputPath.endsWith('.gz') ? gzipSync(encoded) : encoded, { mode: 0o600, flag: 'wx' });
  }
  if (args.includes('--json')) stdout(encoded.slice(0, -1));
  else if (!failure) {
    stdout(`${meets_all}/${rows.length} declarations meet all required style targets.`);
    if (config.potential_profundity) {
      stdout(`Potential profundity: ${potential.status}${potential.probability_relevant === null ? '' : ` (${Math.round(100 * potential.probability_relevant)}% relevant)`}.`);
      stdout(`Composition: ${compositionAssessment.status}${composition.available ? '' : ` [${composition.reasons.join(', ')}]`}. Overall qualification: ${qualification.status}.`);
    }
    for (const item of (config.style_role ? roles : criticality.filter(c => ['critical', 'uncertain'].includes(c.status)))) {
      const required = (requiredByTarget.get(item.target) ?? [])
        .map(a => `level ${a.target_level} on ${a.dimension}`).join(', ');
      stdout(config.style_role ? `Expressive role ${item.status}: ${item.target} requires ${required}.`
        : `Criticality ${item.status}: ${item.target} (${Math.round(100 * item.probability_critical)}% critical) requires ${required}.`);
    }
    for (const item of compositionAssessment.assessments ?? []) {
      stdout(`Composition ${item.dimension}: ${item.status} (${Math.round(100 * item.probability_at_target)}% at level ${item.target_level}+).`);
    }
    for (const axis of by_axis) stdout(`${axis.title}: ${axis.meets_target} meet target; ${axis.below_target} below target; ${axis.uncertain} uncertain; ${axis.unavailable} unavailable.`);
    for (const assessment of assessments.filter(a => a.status !== 'meets_target')) {
      stdout(`${assessment.status}: ${assessment.target} / ${assessment.dimension} (${assessment.probability_at_target === null ? 'no rating' : `${Math.round(100 * assessment.probability_at_target)}%`} at level ${assessment.target_level}+)${assessment.context_truncated ? ' [limited context]' : ''}`);
    }
    for (const ranking of report.rankings) {
      stdout(`\n${ranking.title}`);
      for (const row of ranking.entries) stdout(`${row.rank}. ${row.target}${row.near_tie_above ? ' (near tie above)' : ''}${row.context_truncated ? ' [limited context]' : ''}`);
    }
    for (const diagnostic of report.diagnostics.dimensions) {
      const conditionalTarget = report.diagnostics.targets.find(t => t.dimension === diagnostic.id);
      stdout(`\n${diagnostic.title} (${config.style_role ? 'required at the expressive-role target' : conditionalTarget ? 'required for critical or uncertain declarations' : 'diagnostic; no pass target'})`);
      for (const row of diagnostics.filter(d => d.dimension === diagnostic.id)) {
        stdout(`${row.target}: ${row.status === 'unavailable' ? 'unavailable [truncated context]'
          : `${row.score.toFixed(2)}/${diagnostic.levels.length - 1}${row.status === 'limited_context' ? ' [limited context]' : ''}`}${row.required ? ' [required]' : ' [advisory]'}`);
      }
    }
    stdout(`\nAdvisory taste ranking; ${rows.length} parsed units; ${rows[0].model}.${receiptNote}`);
  }
  if (failure) stderr(`Style ranking failed: ${failure}.${receiptNote}`);
  if (inventory?.unranked.length) stderr(`${inventory.unranked.length} file(s) could not be ranked; see inventory.unranked in the receipt`);
  if (changed_sources.length) stderr(`${changed_sources.length} source/context file(s) changed during review; rankings refer to the recorded snapshot`);
  if (cache?.stats.write_failures) stderr(`${cache.stats.write_failures} style answer(s) could not be saved to the incremental cache`);
  return failure || inventory?.unranked.length ? 1 : counts.below_target || counts.uncertain || counts.unavailable || changed_sources.length
    || config.potential_profundity && !qualified ? 3 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runStyleRanking(process.argv.slice(2), { loadEnv: true }).then(code => { process.exitCode = code; }).catch(error => {
    // Do not print arbitrary provider response bodies or transport request details.
    console.error(`Style ranking failed: ${error.message}`); process.exitCode = 1;
  });
}
