import { readFileSync } from 'node:fs';
import path from 'node:path';
import { ROOT, fileHash } from './system.mjs';

export const FIXTURE_SUITES = ['recursion', 'fields-wasm', 'closures', 'baseslice', 'generics', 'literals'];
const read = file => JSON.parse(readFileSync(path.join(ROOT, file), 'utf8'));

// Manifest adapters copy frozen observations; they neither parse Bend nor
// derive expectations from compiler output. One observation per source keeps
// this a benchmark rather than a second full conformance campaign.
export function fixtureCases(suite) {
  if (!FIXTURE_SUITES.includes(suite)) throw new Error(`unknown fixture suite: ${suite}`);
  const directory = `tests/compiler-${suite}`;
  const manifest = `${directory}/${['recursion', 'fields-wasm'].includes(suite) ? 'cases' : 'expectations'}.json`;
  const data = read(manifest);
  const frozen = suite === 'fields-wasm' ? read(`${directory}/expectations.json`).observations : null;
  return (data.cases ?? data.fixtures).map(row => {
    let calls = [], seedValid, sourceHash, expectedObservation, extraReference;
    if (suite === 'recursion') {
      seedValid = row.reference.exit === 0;
      expectedObservation = row.eval.exit === 0 ? row.eval.stdout : read('bench/expectations.json').recursionObservations[row.name] ?? null;
      if (row.eval.exit !== 0 && expectedObservation) extraReference = 'bench/expectations.json';
    } else if (suite === 'fields-wasm') {
      seedValid = true;
      calls = row.calls.map(c => ({ entry: c.export, args: c.arguments, tag: c.tag, constructor: row.constructors[c.tag] }));
      sourceHash = frozen.find(o => o.case === row.name)?.source_sha256;
    } else if (suite === 'literals') {
      seedValid = row.seed_check.exit === 0;
      sourceHash = row.sha256;
      calls = (row.calls ?? []).filter(c => c.seed.exit === 0).map(c => ({ entry: c.export, args: c.arguments, tag: c.tag, constructor: c.constructor }));
    } else {
      const observed = data.observations.fixtures.find(o => o.case === row.name);
      if (!observed) throw new Error(`${suite}/${row.name}: missing frozen observation`);
      seedValid = observed.check_only.exit === 0;
      sourceHash = observed.source_sha256;
      calls = (observed.calls ?? []).filter(c => c.exit === 0 && c.result).map(c => ({
        entry: c.entry, args: c.ordinals, tag: c.result.tag, constructor: c.result.constructor,
      }));
    }
    const call = calls.find(c => c.entry === 'main' && c.args.length === 0) ?? calls[0];
    const program = row.file.startsWith('tests/') ? row.file : `${directory}/${row.file}`;
    if (sourceHash && sourceHash !== fileHash(path.join(ROOT, program))) throw new Error(`${program}: frozen source hash mismatch`);
    return { name: `${suite}-${row.name}`, program, profile: 'knot-fields-wasm-1',
      entry: call?.entry ?? 'main', args: call?.args ?? [], expected: call?.tag ?? null,
      probe: true, seedValid, compileBudgets: row.compile_budgets ?? [],
      runtimeEligible: Boolean(call),
      oracle: { kind: 'literal', manifest, manifestSha256: fileHash(path.join(ROOT, manifest)),
        constructor: call?.constructor ?? null, expectedObservation: expectedObservation ?? null,
        ...(frozen ? { reference: `${directory}/expectations.json`, referenceSha256: fileHash(path.join(ROOT, `${directory}/expectations.json`)) } : {}),
        ...(extraReference ? { reference: extraReference, referenceSha256: fileHash(path.join(ROOT, extraReference)) } : {}),
        fuel: 1048576 },
    };
  });
}
