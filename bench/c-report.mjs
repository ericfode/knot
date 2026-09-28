#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const result = JSON.parse(readFileSync(process.argv[2], 'utf8'));
if (result.status !== 'passed') throw new Error('cannot report incomplete or failed benchmark evidence');
const number = value => value.toFixed(2);
const time = value => `${number(value.median)} ± ${number(value.mad)}`;
console.log(`# C backend benchmark: ${result.finishedAt}\n`);
console.log(`${result.suite.programs} programs / ${result.suite.calls} frozen calls. Medians ± unscaled MAD; no outliers removed.\n`);
console.log(`Commit: \`${result.environment.git.commit}\` (dirty: ${result.environment.git.dirty}).\n`);
console.log(`C compiler: ${result.environment.cCompiler.version.split('\n')[0]}. Node ${result.environment.tools.node}; Bun ${result.environment.tools.bun}.\n`);
console.log('Compile timings include fresh compiler-process startup and file IO. C total includes a separate cc process. Upstream uses a different Base wrapper per call and is reported with that call.\n');
console.log('| Program | C emission ms | C cc ms | C total ms | Wasm emission ms |');
console.log('| --- | ---: | ---: | ---: | ---: |');
for (const c of result.cases) console.log(`| ${c.name} | ${time(c.compilation.c.emission)} | ${time(c.compilation.c.cc)} | ${time(c.compilation.c.total)} | ${time(c.compilation.wasm.emission)} |`);
console.log('\nFresh-lifetime timing includes C arena reset and dispatch, or Wasm instantiation and export lookup. Both include invocation and result checking. These costs differ; the ratio does not isolate generated instruction speed. Process timing includes native/Node startup, runtime initialization, invocation and output. Upstream prints a constructor; C/Wasm print JSON.\n');
console.log('| Call | C fresh ns | Wasm fresh ns | C process ms | Wasm process ms | Upstream process ms | Upstream build ms |');
console.log('| --- | ---: | ---: | ---: | ---: | ---: | ---: |');
for (const c of result.cases) {
  for (const call of c.calls) {
    const { c: native, wasm, upstream } = call.lanes;
    const valid = native.status === 'passed' && wasm.status === 'passed';
    console.log(`| ${c.name}.${call.export}(${call.arguments.join(',')}) | ${valid ? time(native.freshLifetime) : native.status} | ${valid ? time(wasm.freshLifetime) : wasm.status} | ${valid ? time(native.process.metric) : '—'} | ${valid ? time(wasm.process.metric) : '—'} | ${upstream.status === 'passed' ? time(upstream.process.metric) : 'unavailable'} | ${upstream.status === 'passed' ? time(upstream.compile) : 'unavailable'} |`);
  }
}
const unavailable = result.cases.filter(c => c.calls.some(call => call.lanes.upstream.status === 'unavailable'));
if (unavailable.length) {
  console.log('\nUpstream native unavailable (the required Base import conflicts with names in the unchanged fixture):\n');
  for (const c of unavailable) {
    const failure = c.calls.find(call => call.lanes.upstream.status === 'unavailable').lanes.upstream;
    console.log(`- ${c.name}: ${failure.failure.stderr.split('\n').find(line => line.includes('duplicate declaration:'))?.trim()}`);
  }
}
