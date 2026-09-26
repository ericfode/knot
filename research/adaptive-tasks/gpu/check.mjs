import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { create, globals } from 'webgpu';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../..');
const sha=x=>createHash('sha256').update(x).digest('hex');
const NONE=0xffffffff, SENTINEL=0xdeadbeef;
const MAX_NODES=4096, OP_WORDS=12, TASK_WORDS=16;
const override=process.argv[2];
const shader=await readFile(override??resolve(here,'tasks.wgsl'),'utf8');
const fixturesText=execFileSync(resolve(root,'scripts/bend-reference'),
  [resolve(here,'../fixtures.bend')],{cwd:root,encoding:'utf8',timeout:60000});
const fixtures=fixturesText.trim().split('\n').map(JSON.parse);

function word(x) { assert(Number.isInteger(x)&&x>=0&&x<=NONE,'invalid U32'); return x; }
// Input layout/validation only: program evaluation is exclusively in Bend/WGSL.
function pack(tree) {
  const records=[];
  function visit(node,depth=0) {
    assert(Array.isArray(node)&&depth<=64,'invalid/deep tree');
    const kind=node[0];
    assert([0,1,2].includes(kind),'unsupported instruction');
    let left=NONE,right=NONE,seed=0,ticks=0,factor=0,bias=0;
    if (kind===0) {
      assert.equal(node.length,3); seed=word(node[1]); ticks=word(node[2]);
      assert(ticks<=4096,'tick bound');
    } else if (kind===1) {
      assert.equal(node.length,3); left=visit(node[1],depth+1); right=visit(node[2],depth+1);
    } else {
      assert.equal(node.length,4); left=visit(node[1],depth+1);
      factor=word(node[2]); bias=word(node[3]);
    }
    const id=records.length;
    assert(id<MAX_NODES,'node bound');
    records.push([kind,left,right,seed,ticks,factor,bias,NONE,0,0,0,0]);
    if (left!==NONE) { records[left][7]=id; records[left][8]=0; }
    if (right!==NONE) { records[right][7]=id; records[right][8]=1; }
    return id;
  }
  const root=visit(tree), n=records.length;
  const states=new Uint32Array(n*TASK_WORDS);
  for (let i=0;i<n;i++) {
    states[i*TASK_WORDS+6]=NONE;
    states[i*TASK_WORDS+10]=records[i][7];
    states[i*TASK_WORDS+11]=records[i][8];
    states[i*TASK_WORDS+14]=NONE;
  }
  states[root*TASK_WORDS]=1;
  return {n,root,records,ops:new Uint32Array(records.flat()),states};
}

Object.assign(globalThis,globals);
let gpu=create(['backend=metal']);
const adapter=await gpu.requestAdapter({powerPreference:'high-performance'});
assert(adapter,'hardware adapter unavailable');
assert.equal(adapter.info.isFallbackAdapter,false,'fallback adapter cannot pass');
const device=await adapter.requestDevice();
const uncaptured=[];
device.addEventListener('uncapturederror',event=>uncaptured.push(event.error.message));
device.pushErrorScope('validation');
const module=device.createShaderModule({code:shader});
const compilation=await module.getCompilationInfo();
assert(!compilation.messages.some(m=>m.type==='error'),JSON.stringify(compilation.messages));
const entries=[
  {binding:0,visibility:GPUShaderStage.COMPUTE,buffer:{type:'read-only-storage'}},
  {binding:1,visibility:GPUShaderStage.COMPUTE,buffer:{type:'read-only-storage'}},
  ...[2,3,4,6].map(binding=>({binding,visibility:GPUShaderStage.COMPUTE,buffer:{type:'storage'}})),
  {binding:5,visibility:GPUShaderStage.COMPUTE,buffer:{type:'uniform'}},
];
const layout=device.createBindGroupLayout({entries});
const pipelineLayout=device.createPipelineLayout({bindGroupLayouts:[layout]});
const pipelines={};
for(const entryPoint of ['prepare','execute','join_phase'])
  pipelines[entryPoint]=await device.createComputePipelineAsync({layout:pipelineLayout,compute:{module,entryPoint}});
assert.equal(await device.popErrorScope(),null,'pipeline validation');

async function run(fixture,{quantum=3,adaptive=true,capacity,maxRounds=512}={}) {
  assert(Number.isInteger(quantum)&&quantum>=0&&quantum<=64,'quantum bound');
  assert(Number.isInteger(maxRounds)&&maxRounds>0&&maxRounds<=512,'round bound');
  const p=pack(fixture.tree), n=p.n;
  capacity??=n;
  assert(Number.isInteger(capacity)&&capacity>=0&&capacity<=n,'capacity bound');
  const buffers=[];
  function buffer(size,usage,data) {
    const b=device.createBuffer({size,usage}); buffers.push(b);
    if(data)device.queue.writeBuffer(b,0,data);
    return b;
  }
  const storage=GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|GPUBufferUsage.COPY_SRC;
  const op=buffer(p.ops.byteLength,storage,p.ops);
  const a=buffer(p.states.byteLength,storage,p.states);
  const w=buffer(p.states.byteLength,storage);
  const b=buffer(p.states.byteLength,storage);
  const frontier=buffer((n+1)*4,storage,new Uint32Array(n+1).fill(SENTINEL));
  const control=buffer(16,storage);
  const params=buffer(32,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST);
  const bytes=16+p.states.byteLength+(n+1)*4;
  const readback=buffer(bytes,GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ);
  const makeGroup=(input,output)=>device.createBindGroup({layout,entries:
    [op,input,w,frontier,control,params,output].map((buffer,binding)=>({binding,resource:{buffer}}))});
  const groups=[makeGroup(a,b),makeGroup(b,a)];
  let dispatches=0,peak=0,active=[],result,states,queueWords,rounds=0;
  device.pushErrorScope('validation');
  try {
    for(let round=0;round<maxRounds;round++) {
      const output=round%2===0?b:a;
      device.queue.writeBuffer(params,0,new Uint32Array([n,quantum,capacity,p.root,round,round%2,adaptive?1:0,0]));
      const encoder=device.createCommandEncoder();
      encoder.clearBuffer(control);
      const pass=encoder.beginComputePass();
      pass.setBindGroup(0,groups[round%2]);
      for(const entry of ['prepare','execute','join_phase']) {
        pass.setPipeline(pipelines[entry]); pass.dispatchWorkgroups(Math.ceil(n/64)); dispatches++;
      }
      pass.end();
      encoder.copyBufferToBuffer(control,0,readback,0,16);
      encoder.copyBufferToBuffer(output,0,readback,16,p.states.byteLength);
      encoder.copyBufferToBuffer(frontier,0,readback,16+p.states.byteLength,(n+1)*4);
      device.queue.submit([encoder.finish()]);
      await readback.mapAsync(GPUMapMode.READ);
      const words=new Uint32Array(readback.getMappedRange().slice(0)); readback.unmap();
      states=words.slice(4,4+n*TASK_WORDS); queueWords=words.slice(4+n*TASK_WORDS);
      rounds=round+1; peak=Math.max(peak,words[0]); active.push(words[0]);
      // Every logical destination survives scheduling and all state transitions.
      for(let id=0;id<n;id++) {
        assert.equal(states[id*TASK_WORDS+10],p.records[id][7],'destination changed');
        assert.equal(states[id*TASK_WORDS+11],p.records[id][8],'logical slot changed');
      }
      assert(queueWords.slice(capacity).every(word=>word===SENTINEL),'frontier capacity overrun');
      if(words[1]!==0) { result={kind:'exhausted',resource:'frontier',error:words[1]}; break; }
      if(states[p.root*TASK_WORDS]===5) {
        result={kind:'finished',value:states[p.root*TASK_WORDS+2]}; break;
      }
    }
    result??={kind:'exhausted',resource:'rounds'};
    assert.equal(await device.popErrorScope(),null,'dispatch validation');
    assert.equal(uncaptured.length,0,uncaptured.join('\n'));
    if(result.kind==='finished') {
      assert.equal(result.value,fixture.expected,`${fixture.name}: oracle mismatch`);
      for(let id=0;id<n;id++)if(id!==p.root)assert.equal(states[id*TASK_WORDS],6,'unretired child');
    }
    const sum=field=>Array.from({length:n},(_,i)=>states[i*TASK_WORDS+field]).reduce((a,b)=>a+b,0);
    const rootOp=p.records[p.root];
    const completionOrder=rootOp[0]===1?{
      left:states[rootOp[1]*TASK_WORDS+14],right:states[rootOp[2]*TASK_WORDS+14]}:null;
    return {name:fixture.name,quantum,adaptive,capacity,nodes:n,rounds,dispatches,peakFrontier:peak,
      logicalWorkerMoves:sum(7),workerVisits:sum(8),machineSteps:sum(9),completionOrder,
      stateSha256:sha(new Uint8Array(states.buffer)),result,
      allDestinationsPreserved:true,frontierCanaryPreserved:true,frontierCapacitySuffixPreserved:true,
      allNonRootTasksRetired:result.kind==='finished',activeCounts:active};
  } finally { await device.queue.onSubmittedWorkDone(); for(const b of buffers)b.destroy(); }
}

try {
  const cases=[];
  for(const f of fixtures)for(const quantum of [1,3,16])cases.push(await run(f,{quantum}));
  for(const name of ['balanced','skewed_splittable','opaque_heavy_leaf'])
    cases.push(await run(fixtures.find(f=>f.name===name),{quantum:3,adaptive:false}));
  const reversed=cases.find(c=>c.name==='right_finishes_first'&&c.quantum===1);
  assert(reversed.completionOrder.right<reversed.completionOrder.left,'reversed completion not exercised');
  assert(cases.some(c=>c.logicalWorkerMoves>0),'no redistributable work observed');
  assert(cases.filter(c=>!c.adaptive).every(c=>c.logicalWorkerMoves===0),'fixed baseline moved tasks');
  const empty=await run(fixtures[0],{capacity:0});
  assert.equal(empty.result.resource,'frontier'); assert.equal(empty.machineSteps,0);
  cases.push(empty);
  const tight=await run(fixtures[0],{capacity:1});
  assert.equal(tight.result.resource,'frontier'); cases.push(tight);
  const zero=await run(fixtures[0],{quantum:0,maxRounds:3});
  assert.equal(zero.result.resource,'rounds'); assert.equal(zero.machineSteps,0); cases.push(zero);
  const short=await run(fixtures.find(f=>f.name==='serial_frames'),{maxRounds:2});
  assert.equal(short.result.resource,'rounds'); cases.push(short);
  cases.push(await run(fixtures[0])); // fresh run after failures; all buffers re-created
  assert.throws(()=>pack([99]),/unsupported/);
  assert.throws(()=>pack([0,1,-1]),/invalid U32/);
  const receipt={status:'pass',date:new Date().toISOString(),scope:'handwritten WGSL task-contract probe; no Bend-source compiler',
    webgpuVersion:'0.6.1',node:process.version,platform:process.platform,arch:process.arch,
    adapter:{vendor:adapter.info.vendor,architecture:adapter.info.architecture,device:adapter.info.device,
      description:adapter.info.description,isFallbackAdapter:adapter.info.isFallbackAdapter,backend:'metal'},
    hashes:{shader:sha(shader),runner:sha(await readFile(fileURLToPath(import.meta.url))),fixtures:sha(fixturesText)},
    dispatches:cases.reduce((a,c)=>a+c.dispatches,0),cases,
    shaderCompilationErrors:0,validationErrors:0,unsupportedOpcodeRejected:true,invalidIntegerRejected:true,
    performanceClaim:false};
  await mkdir(resolve(here,'../receipts'),{recursive:true});
  if(!override)await writeFile(resolve(here,'../receipts/gpu.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({status:'pass',adapter:receipt.adapter,cases:cases.length,dispatches:receipt.dispatches,
    maxLogicalWorkerMoves:Math.max(...cases.map(c=>c.logicalWorkerMoves)),performanceClaim:false}));
} finally { device.destroy(); gpu=null; }
