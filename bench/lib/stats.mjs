// All ratios are candidate / baseline; lower is better. No outliers are removed.
export function median(values) {
  if (!Array.isArray(values) || !values.length || values.some(x => !Number.isFinite(x))) {
    throw new Error('expected nonempty finite samples');
  }
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

export function summarize(samples) {
  const center = median(samples);
  return { n: samples.length, median: center,
    mad: median(samples.map(x => Math.abs(x - center))), min: Math.min(...samples) };
}

export function metric(unit, samples) {
  return { unit, samples, ...summarize(samples) };
}

function random(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6D2B79F5) >>> 0;
    let x = Math.imul(state ^ (state >>> 15), 1 | state);
    x ^= x + Math.imul(x ^ (x >>> 7), 61 | x);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

function quantile(sorted, p) {
  const position = (sorted.length - 1) * p;
  const index = Math.floor(position);
  return sorted[index] + (sorted[Math.min(index + 1, sorted.length - 1)] - sorted[index]) * (position - index);
}

export function comparisonOptions({ margin = 0.02, confidence = 0.95, resamples = 10000, seed = 1263423316 } = {}) {
  if (!Number.isFinite(margin) || margin < 0 || margin >= 1) throw new Error('margin must be in [0, 1)');
  if (!Number.isFinite(confidence) || confidence <= 0 || confidence >= 1) throw new Error('confidence must be in (0, 1)');
  if (!Number.isInteger(resamples) || resamples < 100 || resamples > 1000000) throw new Error('resamples must be 100..1000000');
  if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295) throw new Error('seed must be a uint32');
  return { margin, confidence, resamples, seed };
}

export function compareSamples(baseline, candidate, options = {}) {
  const config = comparisonOptions(options);
  const base = summarize(baseline), next = summarize(candidate);
  if ([...baseline, ...candidate].some(x => x <= 0)) throw new Error('ratio samples must be positive');
  const ratio = next.median / base.median;
  // A single observation has a degenerate bootstrap, not useful uncertainty.
  if (Math.min(base.n, next.n) < 3) {
    return { baseline: base, candidate: next, ratio, ci: null, verdict: 'insufficient samples', ...config };
  }
  const rng = random(config.seed);
  const draw = samples => median(Array.from({ length: samples.length }, () => samples[Math.floor(rng() * samples.length)]));
  const ratios = Array.from({ length: config.resamples }, () => draw(candidate) / draw(baseline)).sort((a, b) => a - b);
  const tail = (1 - config.confidence) / 2;
  const ci = [quantile(ratios, tail), quantile(ratios, 1 - tail)];
  const verdict = ci[1] < 1 - config.margin ? 'faster' : ci[0] > 1 + config.margin ? 'slower' : 'no change';
  return { baseline: base, candidate: next, ratio, ci, verdict, ...config };
}
