#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { parseArgs } from 'node:util';
import { compareResults, formatComparison } from './lib/compare.mjs';

try {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    margin: { type: 'string' }, confidence: { type: 'string' }, resamples: { type: 'string' },
    seed: { type: 'string' }, 'include-build': { type: 'boolean' }, help: { type: 'boolean' },
  } });
  if (values.help) {
    console.log('bench:compare BASE.json NEW.json [--margin=0.02] [--confidence=0.95] [--resamples=10000] [--seed=1263423316] [--include-build]');
  } else {
    if (positionals.length !== 2) throw new Error('expected BASE.json NEW.json');
    const options = Object.fromEntries(Object.entries(values).filter(([key]) => key !== 'include-build').map(([k, v]) => [k, Number(v)]));
    const result = compareResults(...positionals.map(p => JSON.parse(readFileSync(p, 'utf8'))),
      { ...options, includeBuild: values['include-build'] });
    console.log(`Candidate / baseline; ${(result.config.confidence * 100).toFixed(1)}% percentile bootstrap CI; ${(result.config.margin * 100).toFixed(2)}% margin.`);
    console.log(formatComparison(result));
    console.log(result.insufficient ? 'Insufficient target samples: at least 3 per metric are required.' :
      result.regression ? 'Significant regression detected.' : 'No significant regression detected.');
    process.exitCode = result.insufficient ? 2 : result.regression ? 1 : 0;
  }
} catch (error) {
  console.error(`Comparison refused: ${error.message}`);
  process.exitCode = 2;
}
