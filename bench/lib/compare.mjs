import { compareSamples, comparisonOptions } from './stats.mjs';
import { outcome } from './outcome.mjs';

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const require = (condition, message) => { if (!condition) throw new Error(message); };

function validateMetric(metric, unit, count) {
  require(metric?.unit === unit && Array.isArray(metric.samples) && metric.samples.length === count &&
    metric.samples.every(x => Number.isFinite(x) && x > 0), `invalid ${unit} metric samples`);
}

export function validateResult(result) {
  if (result?.schemaVersion === 2) return validateCampaignResult(result);
  require(result?.schemaVersion === 1 && result.status === 'passed', 'requires a passed schemaVersion 1 result');
  require(result.environment?.machine && result.environment.tools && result.environment.sourceHashes &&
    result.environment.harnessHashes && result.environment.git, 'missing environment fingerprint');
  require(result.protocol?.version === 1 && same(result.protocol.lanes, ['native', 'bun']) &&
    result.protocol.compileWarmup === 1, 'unsupported measurement protocol');
  const { warmup, iterations } = result.protocol.runtime ?? {};
  require(Number.isSafeInteger(warmup) && warmup > 0 && Number.isSafeInteger(iterations) && iterations > 0 &&
    Number.isSafeInteger(result.protocol.buildRepeat) && result.protocol.buildRepeat > 0, 'invalid measurement counts');
  require(typeof result.suite?.name === 'string' && typeof result.suite.sha256 === 'string' &&
    Array.isArray(result.cases) && result.cases.length > 0 && result.suite.caseCount === result.cases.length, 'missing suite coverage');
  for (const lane of result.protocol.lanes) {
    validateMetric(result.builds?.[lane]?.metric, 'ms', result.protocol.buildRepeat);
    const build = result.builds[lane];
    require(Array.isArray(build.artifacts) && build.artifacts.length === result.protocol.buildRepeat &&
      build.artifacts.every(a => a.correctness?.valid === true && a.correctness.result === 1) &&
      same(build.artifacts.map(a => a.ms), build.metric.samples), 'missing compiler build guards');
  }
  const names = new Set();
  for (const c of result.cases) {
    require(typeof c.name === 'string' && !names.has(c.name), 'duplicate or missing case name');
    names.add(c.name);
    require(typeof c.program === 'string' && typeof c.sourceSha256 === 'string' && typeof c.entry === 'string' &&
      Array.isArray(c.args) && c.args.every(x => Number.isInteger(x) && x >= 0 && x <= 255) &&
      Number.isInteger(c.expected) && c.expected >= 0 && c.expected <= 255 &&
      Number.isInteger(c.repeat) && c.repeat > 0 && ['literal', 'evaluator'].includes(c.oracle?.kind), 'invalid case identity');
    for (const lane of result.protocol.lanes) {
      const measurement = c.lanes?.[lane];
      validateMetric(measurement?.compile, 'ms', c.repeat);
      validateMetric(measurement?.runtime, 'ns/call', c.repeat);
      validateMetric(measurement?.size, 'bytes', c.repeat);
      require(measurement.correctness?.valid === true && measurement.correctness.result === c.expected &&
        measurement.correctness.checkedCalls === c.repeat + 1 + warmup + c.repeat * iterations,
      `${c.name}/${lane}: missing correctness guard`);
      const artifacts = measurement.compilations;
      require(Array.isArray(artifacts) && artifacts.length === c.repeat + 1 &&
        artifacts.every((a, i) => a.valid === true && a.result === c.expected && a.warmup === (i === 0) &&
          typeof a.sha256 === 'string' && a.sha256.length === 64 && Number.isInteger(a.bytes) && a.bytes > 0) &&
        new Set(artifacts.map(a => a.sha256)).size === 1 &&
        same(artifacts.slice(1).map(a => a.ms), measurement.compile.samples) &&
        same(artifacts.slice(1).map(a => a.bytes), measurement.size.samples),
      `${c.name}/${lane}: invalid compilation receipts`);
    }
  }
}

function validateCampaignResult(result) {
  require(result.status === 'passed' && result.protocol?.version === 2, 'requires passed version 2 evidence');
  require(result.environment?.machine && result.environment.tools && result.environment.sourceHashes &&
    result.environment.harnessHashes && result.environment.git, 'missing environment fingerprint');
  const protocol = result.protocol;
  require(same(protocol.lanes, ['native', 'bun']) && protocol.compileWarmup === 1, 'unsupported measurement protocol');
  const { warmup, iterations, minSampleMs = 0 } = protocol.runtime ?? {};
  require(Number.isSafeInteger(warmup) && warmup > 0 && Number.isSafeInteger(iterations) && iterations > 0 &&
    Number.isFinite(minSampleMs) && minSampleMs >= 0 && Number.isSafeInteger(protocol.buildRepeat) && protocol.buildRepeat > 0, 'invalid measurement counts');
  require(Array.isArray(result.cases) && result.cases.length > 0 && result.suite?.caseCount === result.cases.length, 'missing suite coverage');
  for (const builds of [result.builds, ...Object.values(result.profileBuilds ?? {})]) {
    for (const lane of protocol.lanes) {
      const b = builds?.[lane];
      validateMetric(b?.metric, 'ms', protocol.buildRepeat);
      require(b.artifacts?.length === protocol.buildRepeat && b.artifacts.every(a => a.correctness?.valid && a.correctness.result === 1) &&
        same(b.metric.samples, b.artifacts.map(a => a.ms)), 'missing compiler build guards');
    }
  }
  const names = new Set();
  for (const c of result.cases) {
    require(typeof c.name === 'string' && !names.has(c.name), 'duplicate or missing case name'); names.add(c.name);
    require(typeof c.program === 'string' && typeof c.sourceSha256 === 'string' && typeof c.entry === 'string' &&
      ['knot-enum-1', 'knot-fields-wasm-1'].includes(c.profile) && typeof c.seedValid === 'boolean' &&
      Number.isInteger(c.repeat) && c.repeat > 0 && ['literal', 'evaluator'].includes(c.oracle?.kind) &&
      Array.isArray(c.args) && c.args.every(x => Number.isInteger(x) && x >= 0 && x <= 255), 'invalid case identity');
    if (c.profile === 'knot-fields-wasm-1') require(result.profileBuilds?.[c.profile], 'missing fields compiler build');
    const probes = protocol.lanes.map(lane => c.probes?.[lane]);
    require(probes.every(Boolean) && same(outcome(probes[0]), outcome(probes[1])), 'missing or inconsistent probes');
    if (c.status === 'not-yet-compilable') {
      require(['Invalid', 'Unsupported', 'Exhausted'].includes(c.classification) &&
        probes.every(p => outcome(p).classification === c.classification && !p.path) &&
        c.d4Discrepancy === (c.seedValid && c.classification === 'Invalid') && Object.keys(c.lanes).length === 0, 'invalid exclusion');
      continue;
    }
    require(c.status === 'measured' && c.seedValid && probes.every(p => outcome(p).classification === 'Success'), 'missing accepted coverage');
    require(same(c.lanes?.native?.runtimeStatus, c.lanes?.bun?.runtimeStatus), 'inconsistent runtime coverage');
    if (protocol.selfCost) require(c.lanes?.native?.evaluation?.classification === c.lanes?.bun?.evaluation?.classification &&
      c.lanes?.native?.evaluation?.observations?.[0]?.stdout === c.lanes?.bun?.evaluation?.observations?.[0]?.stdout, 'inconsistent evaluator coverage');
    if (c.oracle.seed) require(c.oracle.seedObservation?.exit === 0 &&
      c.oracle.seedObservation.stdout === `${c.oracle.constructor}{}`, 'missing seed generator guard');
    for (const lane of protocol.lanes) {
      const m = c.lanes?.[lane];
      validateMetric(m?.compile, 'ms', c.repeat); validateMetric(m?.size, 'bytes', c.repeat);
      const artifacts = m.compilations;
      require(artifacts?.length === c.repeat + 1 && artifacts.every((a, i) => a.valid === true && a.exit === 0 &&
        a.stdout === `Built\t${a.bytes}` && a.result === (m.runtime === null ? null : c.expected) && a.warmup === (i === 0) &&
        /^[a-f0-9]{64}$/.test(a.sha256)) && new Set(artifacts.map(a => a.sha256)).size === 1 &&
        same(artifacts.slice(1).map(a => a.ms), m.compile.samples) && same(artifacts.slice(1).map(a => a.bytes), m.size.samples), 'invalid compilation receipts');
      if (c.runtimeEligible && m.runtime !== null) {
        require(Number.isInteger(c.expected) && c.expected >= 0 && c.expected <= 255, 'invalid expected enum');
        validateMetric(m.runtime, 'ns/call', c.repeat);
        require(m.lifecycle === (c.profile === 'knot-fields-wasm-1' ? 'fresh-instance-per-call' : 'persistent-instance'), 'wrong instance lifecycle');
        require(m.batches?.length === c.repeat && m.batches.every(b => Number.isSafeInteger(b.calls) && b.calls >= iterations && b.calls % iterations === 0 &&
          Number.isSafeInteger(b.elapsedNs) && b.elapsedNs > 0 && b.elapsedNs >= minSampleMs * 1e6) &&
          same(m.runtime.samples, m.batches.map(b => b.elapsedNs / b.calls)), 'invalid batch evidence');
        require(m.correctness?.valid === true && m.correctness.result === c.expected &&
          m.correctness.checkedCalls === artifacts.length + warmup + m.batches.reduce((sum, b) => sum + b.calls, 0), 'missing correctness guard');
      } else if (!c.runtimeEligible) require(m.runtime === null && c.expected === null && same(m.runtimeStatus,
        { classification: 'Unsupported', phase: 'host', code: 'structured-result' }), 'unqualified structured host result');
      else {
        require(m.runtimeStatus?.classification === 'Exhausted' && Number.isInteger(m.runtimeEvidence?.exit) && m.runtimeEvidence.exit !== 0 &&
          !m.batches && !m.correctness, 'invalid runtime exclusion');
        let failure; try { failure = JSON.parse(m.runtimeEvidence.stderr); } catch { require(false, 'missing runtime exhaustion evidence'); }
        require(same(failure.outcome, m.runtimeStatus), 'runtime exhaustion evidence mismatch');
      }
      if (protocol.selfCost) {
        const e = m.evaluation;
        if (e?.status === 'unavailable') {
          require(['Exhausted', 'Unsupported'].includes(e.classification) && e.observations?.length === 1 &&
            outcome(e.observations[0]).classification === e.classification, 'invalid evaluation exclusion');
        } else {
          require(e?.status === 'measured' && e.observations?.length === c.repeat && e.warmup?.exit === 0, 'missing evaluation observations');
          validateMetric(e.metric, 'ms', c.repeat);
          require(same(e.metric.samples, e.observations.map(o => o.ms)) && [e.warmup, ...e.observations].every(o => {
            if (o.exit !== 0) return false;
            if (c.oracle.expectedObservation) return o.stdout === c.oracle.expectedObservation;
            const match = /^Evaluated\t\d+\t(\d+)\t([A-Za-z_][A-Za-z_0-9]*)\{\}$/.exec(o.stdout);
            return match && Number(match[1]) === c.expected && (!c.oracle.constructor || match[2] === c.oracle.constructor);
          }), 'invalid evaluator guard');
        }
      }
    }
  }
  require(same(result.coverage, { measured: result.cases.filter(c => c.status === 'measured').length,
    notYetCompilable: result.cases.filter(c => c.status === 'not-yet-compilable').length,
    d4Discrepancies: result.cases.filter(c => c.d4Discrepancy).length }), 'invalid coverage summary');
}

function identity(c) {
  const { observations, seedObservation, ...oracle } = c.oracle;
  return { name: c.name, program: c.program, sourceSha256: c.sourceSha256, entry: c.entry,
    args: c.args, expected: c.expected, oracle, profile: c.profile, compileBudgets: c.compileBudgets,
    status: c.status, classification: c.classification, runtimeEligible: c.runtimeEligible,
    exclusions: c.probes && Object.values(c.probes).map(outcome),
    runtimeStatus: c.probes && Object.values(c.lanes).map(l => l.runtimeStatus ?? null) };
}

export function compareResults(baseline, candidate, options = {}) {
  const config = comparisonOptions(options);
  validateResult(baseline);
  validateResult(candidate);
  for (const key of ['machine', 'tools', 'controls', 'harnessHashes']) {
    require(same(baseline.environment[key], candidate.environment[key]), `incompatible ${key}`);
  }
  require(same(baseline.suite, candidate.suite), 'incompatible suite');
  const { buildRepeat: baseBuilds, ...baseProtocol } = baseline.protocol;
  const { buildRepeat: nextBuilds, ...nextProtocol } = candidate.protocol;
  require(same(baseProtocol, nextProtocol), 'incompatible measurement protocol');
  require(same(baseline.cases.map(identity), candidate.cases.map(identity)), 'incompatible workloads or oracle expectations');
  const rows = [];
  const add = (name, lane, metric, base, next, target = true) => {
    const comparison = compareSamples(base.samples, next.samples, config);
    const regression = target && comparison.verdict === 'slower';
    const verdict = metric === 'size' ? ({ faster: 'smaller', slower: 'larger' }[comparison.verdict] ?? comparison.verdict) : comparison.verdict;
    rows.push({ name, lane, metric, unit: base.unit, target, ...comparison, verdict, regression });
  };
  for (const lane of baseline.protocol.lanes) {
    add('compiler build', lane, 'build', baseline.builds[lane].metric, candidate.builds[lane].metric, options.includeBuild === true);
  }
  require(same(Object.keys(baseline.profileBuilds ?? {}), Object.keys(candidate.profileBuilds ?? {})), 'incompatible profile builds');
  for (const profile of Object.keys(baseline.profileBuilds ?? {})) {
    for (const lane of baseline.protocol.lanes) add(`${profile} build`, lane, 'build',
      baseline.profileBuilds[profile][lane].metric, candidate.profileBuilds[profile][lane].metric, options.includeBuild === true);
  }
  baseline.cases.forEach((c, index) => {
    if (c.status === 'not-yet-compilable') return;
    for (const lane of baseline.protocol.lanes) {
      for (const metric of ['compile', 'runtime', 'size']) {
        if (c.lanes[lane][metric] === null) continue;
        add(c.name, lane, metric, c.lanes[lane][metric], candidate.cases[index].lanes[lane][metric]);
      }
      const a = c.lanes[lane].evaluation, b = candidate.cases[index].lanes[lane].evaluation;
      require(a?.status === b?.status && a?.classification === b?.classification, 'incompatible evaluator coverage');
      if (a?.status === 'measured') add(c.name, lane, 'evaluate', a.metric, b.metric);
    }
  });
  return { rows, regression: rows.some(r => r.regression),
    insufficient: !rows.some(r => r.target) || rows.some(r => r.target && r.verdict === 'insufficient samples'), config };
}

export function formatComparison(comparison) {
  const cells = [['Case / lane / metric', 'Base median ± MAD', 'New median ± MAD', 'Ratio', 'CI', 'Decision']];
  const number = n => n.toFixed(3);
  for (const row of comparison.rows) {
    cells.push([`${row.name} / ${row.lane} / ${row.metric}${row.target ? '' : ' (info)'}`,
      `${number(row.baseline.median)} ± ${number(row.baseline.mad)} ${row.unit}`,
      `${number(row.candidate.median)} ± ${number(row.candidate.mad)} ${row.unit}`,
      number(row.ratio), row.ci ? `[${row.ci.map(number).join(', ')}]` : 'unavailable', row.verdict]);
  }
  const widths = cells[0].map((_, i) => Math.max(...cells.map(row => row[i].length)));
  return cells.map(row => row.map((value, i) => value.padEnd(widths[i])).join('  ').trimEnd()).join('\n');
}
