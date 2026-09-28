import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';

export const STAGES = { parse: 'Parsed', catalog: 'Catalogued', check: 'Checked', eval: 'Evaluated', wasm: 'Built' };
const SUCCESS = { ...STAGES, compile: 'Built' };
const FAILURES = { 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure' };
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
class FormatError extends Error {}
const requireFormat = (condition, message) => { if (!condition) throw new FormatError(message); };
const rows = (data, key) => {
  requireFormat(Array.isArray(data?.[key]) && data[key].every(v => v && typeof v === 'object' && !Array.isArray(v)), `Expected ${key} object array`);
  return data[key];
};

export function outcome(expected, success) {
  if (expected?.exit === 0) return success;
  const value = FAILURES[expected?.exit];
  if (!value) throw new FormatError(`Unknown expected outcome ${expected?.exit}`);
  return value;
}
function stage(expected, name) {
  const result = outcome(expected, SUCCESS[name]);
  if (expected.outcome !== undefined) {
    const allowed = expected.exit === 0 ? [SUCCESS[name], 'Accepted', 'agree'] : [result];
    requireFormat(allowed.includes(expected.outcome), 'Contradictory expected outcome and exit');
  }
  return { outcome: result, expectation: expected };
}
const phases = (entry, names) => Object.fromEntries(names.map(([name, key]) => [name, stage(entry[key], name)]));
const pipeline = expected => Object.fromEntries(['check', 'eval', 'wasm'].map(s => [s, stage(expected, s)]));
function callsSucceeded(calls, tag = c => c.tag, exit = c => c.exit) {
  requireFormat(Array.isArray(calls) && calls.length > 0, 'Success requires frozen calls');
  requireFormat(calls.every(c => c && typeof c === 'object' && exit(c) === 0 && Number.isInteger(tag(c))), 'Expected successful calls with literal result tags');
}
function agreement(expected, calls, tag, exit) {
  if (expected?.exit === 0) callsSucceeded(calls, tag, exit);
  return pipeline(expected);
}
function pathFor(directory, file, prefix) {
  requireFormat(typeof file === 'string' && file.endsWith('.bend') && !file.startsWith('/')
    && !file.split('/').some(p => p === '..' || p.startsWith('.env')), 'Expected a local Bend fixture path');
  return prefix ? `${directory}/${file}` : file;
}
const phaseAdapter = (suite, gate, names, prefix = true) => ({ suite, gate, manifests: ['cases.json'], prefix,
  read: data => rows(data['cases.json'], 'cases').map(c => ({ ...c, stages: phases(c, names) })) });
function successfulCalls(entry) {
  requireFormat(!['knot', 'check', 'eval', 'wasm', 'compile', 'exit'].some(k => Object.hasOwn(entry, k)), 'Wasm call manifest has unexpected stage outcomes');
  return agreement({ exit: 0 }, entry.calls, undefined, c => c.exit ?? 0);
}

function requirements(data) {
  const observations = rows(data?.observations, 'fixtures');
  const cases = rows(data, 'cases');
  requireFormat(new Set(observations.map(o => o.case)).size === observations.length
    && new Set(cases.map(c => c.name)).size === cases.length
    && observations.length === cases.length, 'Expected one observation per named case');
  return cases.map(c => {
    const reference = observations.find(o => o.case === c.name), expected = c.knot;
    requireFormat(reference && typeof reference.source_sha256 === 'string', `Missing observation for ${c.name}`);
    let stages;
    if (expected?.require === 'agree') {
      requireFormat(expected.exit === undefined || expected.exit === 0, 'Agreement contradicts the explicit failure exit');
      requireFormat(reference.check_only?.exit === 0, 'Agreement requires a successful seed check');
      stages = agreement({ ...expected, exit: 0 }, reference.calls, c => c.result?.tag);
    } else if (expected?.require === 'agree-or-unsupported' || (expected?.require === 'reject' && expected.exit === undefined)) {
      const alternatives = expected.require === 'reject' ? ['Invalid', 'Unsupported'] : ['success', 'Unsupported'];
      stages = Object.fromEntries(['check', 'eval', 'wasm'].map(s => [s, {
        outcome: 'Unfixed', alternatives: alternatives.map(x => x === 'success' ? SUCCESS[s] : x), expectation: expected,
      }]));
    } else {
      requireFormat(['reject', 'unsupported'].includes(expected?.require) && expected.exit !== 0, 'Unrecognized Knot requirement');
      requireFormat(expected.require !== 'unsupported' || expected.exit === 3, 'Unsupported requires exit 3');
      stages = pipeline(expected);
    }
    return { ...c, stages, reference, frozen_sha256: reference.source_sha256 };
  });
}

// A path owns the interpretation. A lookalike shape in an unknown suite is not authority.
export const ADAPTERS = {
  'tests/subsets': { suite: 'frontend', gate: 'frontend', manifests: ['frontend-cases.json'], prefix: true,
    read: data => rows(data['frontend-cases.json'], 'cases').map(c => {
      requireFormat(typeof c.tree === 'string', 'Expected frozen parser tree');
      return { ...c, stages: { parse: { outcome: 'Parsed', expectation: c.tree } } };
    }) },
  'tests/compiler-checker': phaseAdapter('checker', 'checker', [['check', 'knot']], false),
  'tests/compiler-structural': phaseAdapter('catalog', 'structural', [['catalog', 'catalog'], ['compile', 'compiler']]),
  'tests/compiler-fields': phaseAdapter('fields', 'fields', [['check', 'check'], ['eval', 'eval'], ['compile', 'compile']]),
  'tests/compiler-recursion': phaseAdapter('recursion', 'recursion', [['check', 'check'], ['eval', 'eval'], ['compile', 'compile']]),
  'tests/compiler-wasm': { suite: 'wasm', gate: 'wasm', manifests: ['cases.json'], prefix: false,
    read: data => rows(data['cases.json'], 'cases').map(c => ({ ...c,
      stages: successfulCalls(c), reference: { observations: c.calls } })) },
  'tests/compiler-fields-wasm': { suite: 'fields-wasm', gate: 'fields-wasm', manifests: ['cases.json', 'expectations.json'], prefix: true,
    read: data => {
      const cases = rows(data['cases.json'], 'cases'), observations = rows(data['expectations.json'], 'observations');
      const calls = cases.flatMap(c => rows(c, 'calls').map(call => ({ case: c.name, call })));
      requireFormat(isDeepStrictEqual(calls, observations.map(o => ({ case: o.case, call: o.call }))), 'Frozen fields-Wasm call join differs');
      return cases.map(c => {
        const reference = observations.filter(o => o.case === c.name);
        requireFormat(reference.length > 0 && reference.every(o => typeof o.seed_stdout === 'string'
          && typeof o.source_sha256 === 'string' && o.source_sha256 === reference[0].source_sha256), 'Missing fields-Wasm source/seed observations');
        const stages = successfulCalls(c);
        if (c.eval_exhausted !== undefined) {
          requireFormat(typeof c.eval_exhausted === 'string', 'Expected evaluator exhaustion diagnostic');
          stages.eval = stage({ exit: 4, diagnostic: c.eval_exhausted }, 'eval');
        }
        if (c.name === 'arena-overflow') {
          requireFormat(typeof data['cases.json'].arena?.diagnostic === 'string', 'Missing arena diagnostic');
          stages.wasm = stage({ exit: 4, diagnostic: data['cases.json'].arena.diagnostic }, 'wasm');
        }
        return { ...c, stages, reference, frozen_sha256: reference[0].source_sha256 };
      });
    } },
  'tests/compiler-nest': { suite: 'nest', gate: 'nest', manifests: ['expectations.json'], prefix: false,
    read: data => rows(data['expectations.json'], 'fixtures').map(c => ({ ...c,
      stages: agreement(c.knot, c.observed && [...(c.observed.main ? [c.observed.main] : []), ...rows(c.observed, 'calls')]),
      reference: c.observed, frozen_sha256: c.sha256 })) },
  'tests/compiler-modules': { suite: 'modules', gate: 'modules', manifests: ['expectations.json'], prefix: true,
    read: data => rows(data['expectations.json'], 'fixtures').map(c => {
      const obligation = c.knot?.obligation;
      requireFormat(['match-seed', 'reject', 'knot_expected'].includes(obligation), 'Unrecognized module obligation');
      requireFormat(obligation !== 'match-seed' || c.knot.exit === undefined || c.knot.exit === 0, 'Agreement contradicts the explicit failure exit');
      const expected = obligation === 'match-seed' ? { ...c.knot, exit: 0 }
        : obligation === 'knot_expected' ? c.knot_expected : c.knot;
      requireFormat(obligation !== 'reject' || expected.exit !== 0, 'Reject cannot succeed');
      return { ...c, stages: agreement(expected, c.calls), reference: { observations: c.calls },
        frozen_sha256: data['expectations.json'].sources?.[c.file] };
    }) },
  'tests/compiler-literals': { suite: 'literals', gate: 'literals', manifests: ['expectations.json'], prefix: false,
    read: data => rows(data['expectations.json'], 'fixtures').map(c => ({ ...c,
      stages: agreement(c.knot_expected ?? c.knot, c.calls, undefined, c => c.seed?.exit),
      reference: { check: c.seed_check, run: c.seed_run, observations: c.calls }, frozen_sha256: c.sha256 })) },
  ...Object.fromEntries(['generics', 'closures', 'baseslice'].map(suite => [`tests/compiler-${suite}`, {
    suite, gate: suite, manifests: ['expectations.json'], prefix: true, read: data => requirements(data['expectations.json']),
  }])),
};

export function adaptSuite(directory, documents) {
  const adapter = ADAPTERS[directory];
  if (!adapter) return { status: 'unrecognized-suite', fixtures: [], detail: 'No reviewed adapter for this suite path' };
  try {
    requireFormat(adapter.manifests.every(m => Object.hasOwn(documents, m)), `Required manifests: ${adapter.manifests.join(', ')}`);
    const fixtures = adapter.read(documents).map(c => ({ file: pathFor(directory, c.file, adapter.prefix),
      stages: c.stages, reference: c.reference, ...(c.frozen_sha256 === undefined ? {} : { frozen_sha256: c.frozen_sha256 }) }));
    requireFormat(new Set(fixtures.map(c => c.file)).size === fixtures.length, 'Duplicate fixture file');
    return { status: 'recognized', suite: adapter.suite, fixtures };
  } catch (error) {
    if (!(error instanceof FormatError)) throw error;
    return { status: 'unrecognized-format', suite: adapter.suite, fixtures: [], detail: error.message };
  }
}

function readLocal(root, file) {
  if (path.isAbsolute(file) || file.split('/').some(p => p === '..' || p.startsWith('.env'))) throw new Error(`Not a local evidence path: ${file}`);
  const resolved = fs.realpathSync(path.join(root, file));
  if (!resolved.startsWith(fs.realpathSync(root) + path.sep) || resolved.split(path.sep).some(p => p.startsWith('.env'))) throw new Error(`Evidence path escapes repository: ${file}`);
  return fs.readFileSync(resolved, 'utf8');
}
export function readRegistry(root) {
  const file = 'scripts/gates/run.py', source = readLocal(root, file);
  const helper = fileURLToPath(new URL('./gates.py', import.meta.url));
  const result = spawnSync('python3', ['-B', helper], { input: source, encoding: 'utf8', timeout: 10000 });
  if (result.status !== 0) throw Object.assign(new Error(`Cannot read gate registry: ${result.stderr || result.error}`), { outcome: 'Unsupported' });
  return { file, sha256: sha(source), gates: JSON.parse(result.stdout).map(g => ({ ...g,
    programs: g.argv.filter(a => /\.(py|mjs|ts)$/.test(a)).map(file => ({ file, sha256: sha(readLocal(root, file)) })),
  })) };
}

export function discoverSuites(root) {
  const registry = readRegistry(root), directories = new Set();
  for (const gate of registry.gates) for (const p of gate.programs) directories.add(path.posix.dirname(p.file));
  for (const directory of Object.keys(ADAPTERS)) if (fs.existsSync(path.join(root, directory))) directories.add(directory);
  for (const d of fs.readdirSync(path.join(root, 'tests'), { withFileTypes: true })) {
    if (d.isDirectory() && d.name.startsWith('compiler-')) directories.add('tests/' + d.name);
  }
  const suites = [], fixtures = [], reports = [];
  for (const directory of [...directories].sort()) {
    const files = fs.readdirSync(path.join(root, directory));
    const names = [...new Set(['cases.json', 'expectations.json', ...(ADAPTERS[directory]?.manifests ?? [])])].filter(f => files.includes(f)).sort();
    const gates = registry.gates.filter(g => g.programs.some(p => path.posix.dirname(p.file) === directory)).map(g => g.name);
    const manifests = names.map(name => {
      const file = directory + '/' + name, bytes = readLocal(root, file);
      return { file, sha256: sha(bytes), name, bytes };
    });
    let adapted;
    try {
      adapted = names.length ? adaptSuite(directory, Object.fromEntries(manifests.map(m => [m.name, JSON.parse(m.bytes)])))
        : { status: 'no-fixture-manifest', fixtures: [] };
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      adapted = { status: 'unrecognized-format', fixtures: [], detail: 'Malformed JSON fixture manifest' };
    }
    const { status, suite = directory, detail } = adapted;
    const gate = ADAPTERS[directory]?.gate ?? null;
    const admission = status !== 'recognized' ? 'excluded' : gates.includes(gate) ? 'evidence' : 'requirement';
    const entry = { suite, directory, status, gate, admission,
      manifests: manifests.map(({ file, sha256 }) => ({ file, sha256 })), gates, fixtures: adapted.fixtures.length };
    if (detail) entry.detail = detail;
    suites.push(entry);
    if (status.startsWith('unrecognized')) reports.push({ directory, status, detail });
    if (status === 'recognized') {
      const extra = names.filter(n => !ADAPTERS[directory].manifests.includes(n));
      for (const name of extra) reports.push({ directory, manifest: directory + '/' + name, status: 'unrecognized-format', detail: 'No adapter for additional manifest' });
      const documents = Object.fromEntries(manifests.map(m => [m.name, JSON.parse(m.bytes)]));
      fixtures.push(...adapted.fixtures.map(f => ({ ...f, suite, directory, gate, admission,
        ...(directory === 'tests/compiler-modules' ? {
          bundle: documents['expectations.json'].bundle, source_hashes: documents['expectations.json'].sources,
        } : {}) })));
    }
  }
  for (const gate of registry.gates) if (!gate.programs.length) reports.push({ gate: gate.name, status: 'no-fixture-manifest', detail: 'Registered command has no source fixture directory' });
  return { registry, suites, fixtures, reports };
}

export function classEvidence(records, features) {
  return [...features].sort().map(feature => ({ feature, stages: Object.fromEntries(Object.entries(STAGES).map(([stage, success]) => {
    const evidence = [...new Set(records.filter(r => r.features?.includes(feature) && r.stages[stage]?.outcome === success)
      .map(r => `${r.suite}:${r.file}`))].sort();
    return [stage, { status: evidence.length ? 'observed-in-successful-fixtures' : 'no-positive-fixture-evidence', evidence }];
  })) }));
}
