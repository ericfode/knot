import { readFileSync } from 'node:fs';
import path from 'node:path';
import { generate } from '../generate.mjs';
import { ROOT, fileHash } from './system.mjs';

export function positiveInteger(value, name, max = 100000000) {
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number < 1 || number > max) throw new Error(`${name} must be an integer in 1..${max}`);
  return number;
}

export function loadSuite(name, overrides = {}) {
  if (!/^[a-z0-9][a-z0-9-]*$/.test(name)) throw new Error('invalid suite name');
  const filename = `bench/suites/${name}.json`;
  const suite = JSON.parse(readFileSync(path.join(ROOT, filename), 'utf8'));
  if (suite.schemaVersion !== 1 || suite.name !== name || !Array.isArray(suite.cases) || !suite.cases.length) {
    throw new Error('invalid suite: expected schemaVersion 1, matching name, and nonempty cases');
  }
  const generated = suite.cases.some(c => c.program.startsWith('.local/bench/generated/')) ? generate() : [];
  const manifestPath = 'tests/compiler-wasm/cases.json';
  const manifest = JSON.parse(readFileSync(path.join(ROOT, manifestPath), 'utf8'));
  const names = new Set();
  const cases = suite.cases.map(c => {
    if (typeof c.name !== 'string' || !/^[a-z0-9][a-z0-9-]*$/.test(c.name) || names.has(c.name)) throw new Error('case names must be unique slugs');
    names.add(c.name);
    if (typeof c.program !== 'string' || !c.program.endsWith('.bend') || path.isAbsolute(c.program) || c.program.split('/').includes('..')) {
      throw new Error(`${c.name}: program must be a repository-relative .bend path`);
    }
    if (typeof c.entry !== 'string' || !c.entry || !Array.isArray(c.args) || c.args.some(x => !Number.isInteger(x) || x < 0 || x > 255)) {
      throw new Error(`${c.name}: expected entry and enum ordinals`);
    }
    const reference = manifest.cases.find(r => r.file === c.program);
    const call = reference?.calls.find(r => r.export === c.entry && JSON.stringify(r.arguments) === JSON.stringify(c.args));
    const generatedCase = generated.find(r => r.program === c.program);
    if (generatedCase && (generatedCase.entry !== c.entry || JSON.stringify(generatedCase.args) !== JSON.stringify(c.args))) {
      throw new Error(`${c.name}: generated case must match its declared call`);
    }
    return { name: c.name, program: c.program, entry: c.entry, args: c.args,
      repeat: positiveInteger(overrides.repeat ?? c.repeat, 'repeat', 1000),
      sourceSha256: fileHash(path.join(ROOT, c.program)),
      expected: call?.tag ?? generatedCase?.expected ?? null,
      oracle: call ? { kind: 'literal', manifest: manifestPath, manifestSha256: fileHash(path.join(ROOT, manifestPath)),
        typeId: reference.type_id, constructor: reference.constructors[call.tag] }
        : { kind: 'evaluator', fuel: 65536, formulaCrossCheck: generatedCase?.expected ?? null },
    };
  });
  return { name, path: filename, sha256: fileHash(path.join(ROOT, filename)), cases,
    runtime: {
      warmup: positiveInteger(overrides.warmup ?? suite.runtime.warmup, 'warmup'),
      iterations: positiveInteger(overrides.iterations ?? suite.runtime.iterations, 'iterations'),
    } };
}
