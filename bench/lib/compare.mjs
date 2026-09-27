import { compareSamples, comparisonOptions } from './stats.mjs';

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const require = (condition, message) => { if (!condition) throw new Error(message); };

function validateMetric(metric, unit, count) {
  require(metric?.unit === unit && Array.isArray(metric.samples) && metric.samples.length === count &&
    metric.samples.every(x => Number.isFinite(x) && x > 0), `invalid ${unit} metric samples`);
}

export function validateResult(result) {
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

function identity(c) {
  const { observations, ...oracle } = c.oracle;
  return { name: c.name, program: c.program, sourceSha256: c.sourceSha256, entry: c.entry,
    args: c.args, expected: c.expected, oracle };
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
  baseline.cases.forEach((c, index) => {
    for (const lane of baseline.protocol.lanes) {
      for (const metric of ['compile', 'runtime', 'size']) {
        add(c.name, lane, metric, c.lanes[lane][metric], candidate.cases[index].lanes[lane][metric]);
      }
    }
  });
  return { rows, regression: rows.some(r => r.regression),
    insufficient: rows.some(r => r.target && r.verdict === 'insufficient samples'), config };
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
