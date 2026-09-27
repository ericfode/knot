// Exercise emitted Bend functions. The host supplies inputs and compares outputs;
// the independent semantic oracle and universal equations remain in Bend.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../../..');
const [gateReceipt='cpu-gates-reproduction.json',outputName='cost-gate-reproduction.json']=process.argv.slice(2);
assert(/^[a-z0-9-]+\.json$/.test(gateReceipt)&&/^[a-z0-9-]+\.json$/.test(outputName));
const gate=JSON.parse(readFileSync(resolve(here,gateReceipt),'utf8'));
assert.equal(gate.status,'passed');
const work=resolve(root,'.local/style-pilot/adaptive-run-1',gateReceipt.slice(0,-5));
const sha=s=>createHash('sha256').update(s).digest('hex');
const sources=Object.fromEntries(['baseline','candidate'].map(v=>[v,readFileSync(resolve(work,v,'conformance.js'),'utf8')]));
const runPattern=/function \$task\$run\$\([^\n]*\) \{.*?\n\}/s;
const bodies=Object.fromEntries(Object.entries(sources).map(([v,s])=>[v,s.match(runPattern)?.[0]]));
assert(bodies.baseline&&bodies.candidate,'known emitted run functions');
assert.equal(sources.baseline.replace(runPattern,'RUN'),sources.candidate.replace(runPattern,'RUN'),
  'All emitted code outside run must remain byte-identical');
const reconstruction='          const _dest_0 = _state_0["destination"];\n'
  +'          const _payload_0 = _state_0["payload"];\n'
  +'          return {$: "task.Delivered", "destination": _dest_0, "payload": _payload_0};';
assert.equal(bodies.candidate,bodies.baseline.replace(reconstruction,'          return _state_0;'),
  'The only emitted change must replace terminal reconstruction by identity');

function load(text){
  const footer='cli(process.argv.slice(2));\nio_exit($main$, null);';
  assert(text.endsWith(footer),'known generated CLI footer');
  const instrumentation=`
let observed_steps=0;
const original_step=$task$step$;
$task$step$=function(task){observed_steps++;return original_step(task);};
return {start:$task$start$, run(fuel,state){observed_steps=0;const result=$task$run$(fuel,state);return {result,steps:observed_steps};}};
`;
  return new Function(text.slice(0,-footer.length)+instrumentation)();
}
const api=Object.fromEntries(Object.entries(sources).map(([v,s])=>[v,load(s)]));
const frames=()=>({$: 'Con',head:{$:'task.Unary',factor:3,bias:5},tail:
  {$:'Con',head:{$:'task.Binary',left:{$:'task.OwnedWord',value:7}},tail:{$:'Nil'}}});
const probes=[];
for(const ticks of [0,1,16,256,4096,65536]){
  for(const fuel of [...new Set([0,1,Math.floor(ticks/2),ticks,ticks+2,ticks+3,ticks+4])]){
    const results=Object.fromEntries(Object.entries(api).map(([v,a])=>[v,a.run(fuel,a.start(73,ticks,11,frames()))]));
    assert.deepEqual(results.candidate,results.baseline,`ticks=${ticks} fuel=${fuel}`);
    assert(results.candidate.steps<=fuel);
    probes.push({kind:'checkpoint',ticks,fuel,steps:results.candidate.steps,
      exact_full_state_match:true,result_sha256:sha(JSON.stringify(results.candidate.result))});
  }
}
for(const fuel of [0,1,16,65536]){
  const results=Object.fromEntries(Object.entries(api).map(([v,a])=>[v,a.run(fuel,
    {$:'task.Delivered',destination:73,payload:{$:'task.OwnedWord',value:4294967295}})]));
  assert.deepEqual(results.candidate,results.baseline);
  assert.equal(results.candidate.steps,0);
  probes.push({kind:'delivered',fuel,steps:0,exact_full_state_match:true,
    result_sha256:sha(JSON.stringify(results.candidate.result))});
}
const output=resolve(here,outputName);
writeFileSync(output,JSON.stringify({at:new Date().toISOString(),status:'passed',
  backend:`Bun ${process.versions.bun ?? 'unavailable'}; emitted JavaScript`,
  gate_receipt:gateReceipt,gate_sha256:sha(readFileSync(resolve(here,gateReceipt))),
  source_hashes:Object.fromEntries(Object.entries(sources).map(([v,s])=>[v,sha(s)])),
  driver_sha256:sha(readFileSync(fileURLToPath(import.meta.url))),
  exact_generated_delta:'Only two Delivered field reads and one wrapper construction become return existing state.',
  advancing_path_byte_identical:true,all_other_generated_code_byte_identical:true,
  step_instrumentation:'Counts calls to the emitted step function; does not implement an evaluator.',
  probes,performance_boundary:'Same counted task steps through 65536 ticks; no new work on advancing path. No wall-time speedup, universal runtime bound or native/GPU performance claim.'},null,2)+'\n',{flag:'wx'});
console.log(`PASS: ${probes.length} exact full-state/step-count comparisons; generated advancing path unchanged, terminal wrapper reconstruction removed.`);
