import {writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import {fixtures,compositions,evolve} from './fixtures.mjs';
const [, ,modulePath,outputPath] = process.argv;
const mod = (await import(pathToFileURL(modulePath).href)).default;
if (typeof mod.call_step !== 'function' || typeof mod.call_evolve !== 'function')
  throw new Error('Missing checked public entry');
const list = xs => xs.reduceRight((tail,head) => ({$: 'Con',head,tail}),{$:'Nil'});
function observe(xs,length) {
  const out=[];
  while (xs?.$ === 'Con') {
    if (out.length >= length || ![0,1].includes(xs.head)) throw new Error('Malformed board');
    out.push(xs.head); xs=xs.tail;
  }
  if (xs?.$ !== 'Nil' || out.length !== length) throw new Error('Wrong board shape');
  return out;
}
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
const rows=[];
const start=performance.now();
for (const f of fixtures) {
  const t=performance.now();
  let got,unchanged,error;
  try {
    const input=list(f.cells);
    const output=f.turns===1 ? mod.call_step(f.width,f.height,input)
      : mod.call_evolve(BigInt(f.turns),f.width,f.height,input);
    got=observe(output,f.cells.length);
    unchanged=same(observe(input,f.cells.length),f.cells);
  } catch (e) { error=String(e); }
  const pass=!error && unchanged && same(got,f.expected);
  rows.push({id:f.id,pass,milliseconds:performance.now()-t,
    ...(!pass ? {expected:f.expected,actual:got,input_preserved:unchanged,error}: {})});
}
const composition=[];
for (const f of compositions) {
  let got,direct,error;
  try {
    const first=mod.call_evolve(BigInt(f.a),f.width,f.height,list(f.cells));
    got=observe(mod.call_evolve(BigInt(f.b),f.width,f.height,first),f.cells.length);
    direct=observe(mod.call_evolve(BigInt(f.a+f.b),f.width,f.height,list(f.cells)),f.cells.length);
  } catch (e) { error=String(e); }
  const expected=evolve(f.width,f.height,f.cells,f.a+f.b);
  const pass=!error && same(got,direct) && same(got,expected);
  composition.push({id:f.id,pass,...(!pass ? {expected,actual:got,direct,error}:{})});
}
const report={passed:rows.every(x=>x.pass)&&composition.every(x=>x.pass),
  runtime:process.version,fixture_count:rows.length,composition_count:composition.length,
  milliseconds:performance.now()-start,observations:rows,composition};
writeFileSync(outputPath,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,fixture_count:rows.length,
  composition_count:composition.length,failures:[...rows,...composition].filter(x=>!x.pass).slice(0,5)}));
process.exitCode=report.passed?0:1;
