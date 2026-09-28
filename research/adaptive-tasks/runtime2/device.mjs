import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {dirname,resolve} from 'node:path';
import {mutants,mutate} from './mutants.mjs';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../..');
const sha=value=>createHash('sha256').update(value).digest('hex');
const args=process.argv.slice(2);
let out=resolve(root,'.local/adaptive-tasks/runtime2'),validationOnly=false,modelPath;
for (let i=0;i<args.length;i++) {
  if (args[i]==='--validate-only')validationOnly=true;
  else if (args[i]==='--out-dir' && args[i+1])out=resolve(args[++i]);
  else if (args[i]==='--model' && args[i+1])modelPath=resolve(args[++i]);
  else throw new Error(`Invalid argument: ${args[i]}`);
}
const layoutText=await readFile(resolve(here,'layout.json'),'utf8');
const layout=JSON.parse(layoutText),H=layout.header;
const shader=await readFile(resolve(here,'runtime.wgsl'),'utf8');
const fixturesText=await readFile(resolve(here,'fixtures.json'),'utf8');
const programsText=await readFile(resolve(here,'programs.json'),'utf8');
const MAX=0xffffffff,GUARD=layout.guard;
let gpu,device,report;
const uncaptured=[];

class ObservationMismatch extends Error {}
function word(value) { assert(Number.isInteger(value)&&value>=0&&value<=MAX,'Invalid U32 transport');return value; }
function checkedBytes(words,limit,what) {
  assert(Number.isSafeInteger(words)&&words>=0,`Invalid ${what} word count`);
  if (words>Math.floor(limit/4))throw new Error(`Exhausted ${what}: ${words} words exceed ${limit} bytes`);
  return words*4;
}
async function host(operation,action) {
  try {return await action();}
  catch(error) {throw new Error(`HostFailure ${operation}: ${error.message}`,{cause:error});}
}
async function loadWebGPU() {
  const locations=[resolve(here,'../gpu/package.json'),resolve(root,'.local/gpu-2/package.json')];
  if (process.env.WEBGPU_NODE_MODULES)locations.unshift(resolve(process.env.WEBGPU_NODE_MODULES,'../package.json'));
  for (const location of locations) {
    let module;
    try {module=createRequire(location).resolve('webgpu');}
    catch(error) {if(error.code==='MODULE_NOT_FOUND')continue;throw error;}
    return import(pathToFileURL(module).href);
  }
  throw new Error('HostFailure webgpu dependency unavailable; install the pinned gpu/package-lock.json locally or set WEBGPU_NODE_MODULES');
}

// Decoder checks every unused word and counts ownership independently of WGSL.
function observe(words,original,programMode=false) {
  const w=Array.from(words),h=name=>w[H[name]];
  assert.deepEqual(w.slice(0,17),original.slice(0,17),'immutable layout header');
  assert.equal(w[H.instructionCount],original[H.instructionCount],'immutable instruction count');
  assert.deepEqual(w.slice(26,32),original.slice(26,32),'reserved header');
  if(!programMode)assert.deepEqual(w.slice(24,26),original.slice(24,26),'transition mode preserves control');
  assert(h('phase')<=3,'driver phase');
  assert.equal(h('words'),w.length,'state length');
  assert(h('pendingCount')<=h('pending'),'pending capacity');
  assert(h('nextIdentity')<=h('idLimit'),'identity ceiling');
  assert([0,1,2,3,5].includes(h('status')),'outcome category');
  if(h('status')!==0)assert.equal(h('reply'),0,'failed request exposed reply');
  const objects=[],captures=[],pending=[],joins=[],byId=new Map(),edges=new Map();
  const edge=identity=>{if(identity)edges.set(identity,(edges.get(identity)??0)+1);};
  for(let i=0;i<h('objects');i++) {
    const base=h('objectBase')+i*h('objectStride');
    const [identity,kind,rc,arity,tag]=w.slice(base,base+5);
    if(identity===0) {
      assert(w.slice(base,base+h('objectStride')).every(x=>x===0),'free object payload');
      objects.push([]);continue;
    }
    assert(!byId.has(identity),'duplicate object identity');
    assert(identity<=h('idLimit') && (h('nextIdentity')===0 || identity<h('nextIdentity')),'issued identity');
    assert(kind===0||kind===1,'object kind');
    assert(arity<=h('arity'),'object arity');
    assert(rc>=1&&rc<=h('rcLimit'),'RC bounds');
    if(kind===0)assert.equal(rc,1,'unique Type count');
    const children=w.slice(base+5,base+5+arity);
    assert(children.every(x=>x!==0),'live child identity');
    assert(w.slice(base+5+arity,base+h('objectStride')).every(x=>x===0),'object unused payload');
    const object=[identity,kind,rc,tag,children];objects.push(object);byId.set(identity,object);
    children.forEach(edge);
  }
  for(let i=0;i<h('captures');i++) {const id=w[h('captureBase')+i];captures.push(id);edge(id);}
  for(let i=0;i<h('pendingCount');i++) {
    const id=w[h('pendingBase')+i];assert.notEqual(id,0,'pending owner');pending.push(id);edge(id);
  }
  assert(w.slice(h('pendingBase')+pending.length,h('pendingBase')+h('pending')).every(x=>x===0),'unused pending stack');
  for(let i=0;i<h('joins');i++) {
    const base=h('joinBase')+i*h('joinStride'),head=w.slice(base,base+8);
    const [attempt,state,arity,received,completions,code,first,count]=head;
    assert(state<=4,'join state');assert(arity<=h('arity'),'join arity');
    assert(attempt<=h('attemptLimit'),'attempt ceiling');
    assert(completions<=attempt,'completion at most once per attempt');
    assert(first<=h('captures') && count<=h('captures')-first,'saved capture bounds');
    const results=w.slice(base+8,base+8+arity);
    if(state===0)assert(w.slice(base,base+h('joinStride')).every(x=>x===0),'unused join payload');
    else {assert(attempt>0,'live attempt');assert(code<h('instructionCount'),'continuation code');}
    if(state===1)assert.equal(received,results.filter(Boolean).length,'waiting received count');
    if(state===2) {assert.equal(received,arity,'ready arity');assert(results.every(Boolean),'ready owns every result');}
    if(state===3)assert.equal(received,0,'cancel clears received');
    if(state===3||state===4)assert(results.every(x=>x===0),'consumed join results');
    if(state===4)assert.equal(received,arity,'resumed arity');
    assert(w.slice(base+8+arity,base+h('joinStride')).every(x=>x===0),'join unused payload');
    results.forEach(edge);joins.push([...head,results]);
  }
  for(const [id,count] of edges) {
    const object=byId.get(id);assert(object,`owner of missing object ${id}`);
    assert.equal(object[2],count,`counted ownership of ${id}`);
  }
  for(const object of byId.values()) {
    assert(edges.has(object[0]),'unrooted live object');
    if(object[1]===1)for(const child of object[4])assert.equal(byId.get(child)?.[1],1,'Type child in Data');
  }
  const guards=[h('objectBase')+h('objects')*h('objectStride'),h('captureBase')+h('captures'),
    h('pendingBase')+h('pending'),h('joinBase')+h('joins')*h('joinStride')];
  for(const offset of guards)assert.equal(w[offset],GUARD,`capacity guard at ${offset}`);
  return [h('status'),h('reply'),h('nextIdentity'),h('readers'),h('freed'),objects,captures,pending,joins];
}

async function main() {
  await mkdir(out,{recursive:true});
  const {create,globals}=await loadWebGPU();Object.assign(globalThis,globals);
  gpu=create([`backend=${validationOnly?'null':'metal'}`]);
  const adapter=await host('requestAdapter',()=>gpu.requestAdapter({powerPreference:'high-performance'}));
  if(!adapter)throw new Error('HostFailure device-unavailable: requestAdapter returned null');
  if(!validationOnly&&adapter.info.isFallbackAdapter!==false)throw new Error('HostFailure fallback adapter cannot qualify device execution');
  const requiredLimits={maxStorageBufferBindingSize:adapter.limits.maxStorageBufferBindingSize,maxBufferSize:adapter.limits.maxBufferSize};
  device=await host('requestDevice',()=>adapter.requestDevice({requiredLimits}));
  device.addEventListener('uncapturederror',event=>uncaptured.push(event.error.message));
  const storageLimit=Math.min(MAX-3,device.limits.maxStorageBufferBindingSize,device.limits.maxBufferSize);
  const bindLayout=device.createBindGroupLayout({entries:[
    ...[0,1,2].map(binding=>({binding,visibility:GPUShaderStage.COMPUTE,buffer:{type:binding===0?'read-only-storage':'storage'}})),
    {binding:3,visibility:GPUShaderStage.COMPUTE,buffer:{type:'uniform',hasDynamicOffset:true,minBindingSize:16}},
    {binding:4,visibility:GPUShaderStage.COMPUTE,buffer:{type:'read-only-storage'}},
  ]});
  const pipelineLayout=device.createPipelineLayout({bindGroupLayouts:[bindLayout]});
  async function compile(source) {
    device.pushErrorScope('validation');
    try {
      const module=device.createShaderModule({code:source});
      const info=await module.getCompilationInfo();
      assert(!info.messages.some(message=>message.type==='error'),`InternalFailure WGSL typecheck: ${JSON.stringify(info.messages)}`);
      const pipelines=[];
      for(const entryPoint of ['execute','run','publish'])pipelines.push(await device.createComputePipelineAsync({layout:pipelineLayout,compute:{module,entryPoint}}));
      return pipelines;
    } finally {
      const error=await device.popErrorScope();
      if(error)throw new Error(`InternalFailure pipeline validation: ${error.message}`);
    }
  }
  const pipelines=await compile(shader),mutationPipelines=[];
  for(const mutant of mutants)mutationPipelines.push(await compile(mutate(shader,mutant)));
  report={contract:layout.contract,date:new Date().toISOString(),
    adapter:{vendor:adapter.info.vendor,architecture:adapter.info.architecture,device:adapter.info.device,
      description:adapter.info.description,isFallbackAdapter:adapter.info.isFallbackAdapter,backend:validationOnly?'null':'metal'},
    limits:{maxStorageBufferBindingSize:device.limits.maxStorageBufferBindingSize,maxBufferSize:device.limits.maxBufferSize,checkedStorageBytes:storageLimit},
    hashes:{shader:sha(shader),runner:sha(await readFile(fileURLToPath(import.meta.url))),mutants:sha(await readFile(resolve(here,'mutants.mjs'))),layout:sha(layoutText),fixtures:sha(fixturesText),programs:sha(programsText)},
    shaderVariants:1+mutants.length,pipelines:3*(1+mutants.length),deviceExecution:false,semanticKills:0,
    mutants:mutants.map(mutant=>({name:mutant.name,witness:mutant.witness,typechecks:true,killed:false,shaderSha256:sha(mutate(shader,mutant))})),
    cases:[],programs:[],commands:0,programRounds:0,dispatches:0,observations:0};
  if(validationOnly) {report.status='validation-only';return;}
  assert(modelPath,'Invalid: --model is required for hardware execution');
  const modelText=await readFile(modelPath,'utf8'),model=JSON.parse(modelText);
  if(model.contract)assert.equal(model.contract,layout.contract,'model contract');
  if(model.fixturesSha256)assert.equal(model.fixturesSha256,sha(fixturesText),'stale model fixtures');
  if(model.programsSha256)assert.equal(model.programsSha256,sha(programsText),'stale model programs');
  for(const [path,digest] of Object.entries(model.sources??{}))assert.equal(sha(await readFile(resolve(root,path))),digest,`stale model ${path}`);
  report.modelSha256=sha(modelText);
  assert(Array.isArray(model.cases),'Invalid model case table');

  async function run(fixture,ps,programMode=false) {
    const rounds=programMode?fixture.quanta:fixture.commands.map((_,index)=>index);
    assert.equal(rounds.length,fixture.observations.length,'missing per-round observations');
    if(programMode)rounds.forEach(word);
    const start=fixture.words.map(word),limit=Math.min(storageLimit,word(fixture.config.maxStorageBytes));
    const bytes=checkedBytes(start.length,limit,'state');
    assert(start.length>=36,'Invalid state header');
    const code=new Uint32Array(fixture.commands.flatMap(command=>{
      assert.equal(command.length,8,'Invalid instruction stride');return command.map(word);
    }));
    const codeBytes=checkedBytes(Math.max(1,code.length),limit,'instructions');
    assert.equal(start[H.instructionCount],fixture.commands.length,'instruction count');
    observe(start,start,programMode);
    const buffers=[],usage=GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC|GPUBufferUsage.COPY_DST;
    function buffer(size,usage,data) {
      if(size>device.limits.maxBufferSize)throw new Error(`Exhausted buffer size ${size}`);
      const value=device.createBuffer({size,usage});buffers.push(value);
      if(data?.byteLength)device.queue.writeBuffer(value,0,data);
      return value;
    }
    const a=buffer(bytes,usage,new Uint32Array(start)),b=buffer(bytes,usage),work=buffer(bytes,usage);
    const program=buffer(codeBytes,usage,code);
    const align=device.limits.minUniformBufferOffsetAlignment;
    if(Math.max(1,rounds.length)>Math.floor(device.limits.maxBufferSize/align))
      throw new Error('Exhausted instruction-index uniform buffer');
    const stepWords=new Uint32Array(Math.max(1,rounds.length)*align/4);
    for(let i=0;i<rounds.length;i++)stepWords[i*align/4]=rounds[i];
    const steps=buffer(stepWords.byteLength,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST,stepWords);
    const backs=[0,1].map(()=>buffer(bytes,GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ));
    const groups=[[a,b],[b,a]].map(([input,output])=>device.createBindGroup({layout:bindLayout,entries:[
      {binding:0,resource:{buffer:input}},{binding:1,resource:{buffer:work}},{binding:2,resource:{buffer:output}},
      {binding:3,resource:{buffer:steps,size:16}},{binding:4,resource:{buffer:program}},
    ]}));
    const trace=[];let encoder=device.createCommandEncoder(),unsubmitted=false;
    device.pushErrorScope('validation');
    try {
      for(let index=0;index<rounds.length;index++) {
        for(const pipeline of [ps[programMode?1:0],ps[2]]) {
          const pass=encoder.beginComputePass();pass.setPipeline(pipeline);
          pass.setBindGroup(0,groups[index%2],[index*align]);pass.dispatchWorkgroups(1);pass.end();
        }
        unsubmitted=true;
        const expected=fixture.observations[index];
        if(expected===null)continue;
        const output=index%2===0?b:a;
        encoder.copyBufferToBuffer(work,0,backs[0],0,bytes);encoder.copyBufferToBuffer(output,0,backs[1],0,bytes);
        await host('submit',()=>device.queue.submit([encoder.finish()]));unsubmitted=false;
        await host('mapAsync',()=>Promise.all(backs.map(back=>back.mapAsync(GPUMapMode.READ))));
        const raw=backs.map(back=>{const words=new Uint32Array(back.getMappedRange().slice(0));back.unmap();return words;});
        const phases=[];
        for(let phase=0;phase<2;phase++) {
          try {
            const state=raw[phase];
            const projection=observe(state,start,programMode);
            const observation=programMode?{pc:state[H.pc],phase:state[H.phase],state:projection}:projection;
            assert.deepEqual(observation,expected);
            phases.push({phase:phase===0?'execute':'publish',wordsSha256:sha(state),observation});
          } catch(error) {throw new ObservationMismatch(`${fixture.name} step ${index} phase ${phase}: ${error.message}`);}
        }
        trace.push({step:index,phases});encoder=device.createCommandEncoder();
      }
      if(unsubmitted)await host('submit',()=>device.queue.submit([encoder.finish()]));
      return {name:fixture.name,instructions:fixture.commands.length,commands:programMode?0:rounds.length,
        programRounds:programMode?rounds.length:0,dispatches:2*rounds.length,observations:trace.length*2,trace};
    } finally {
      await host('onSubmittedWorkDone',()=>device.queue.onSubmittedWorkDone());
      for(const value of buffers)value.destroy();
      const error=await device.popErrorScope();
      if(error)throw new Error(`HostFailure dispatch validation: ${error.message}`);
      if(uncaptured.length)throw new Error(`HostFailure uncaptured device errors: ${uncaptured.join('\n')}`);
    }
  }

  for(const fixture of model.cases)report.cases.push(await run(fixture,pipelines));
  for(const fixture of model.programs??[])report.programs.push(await run(fixture,pipelines,true));
  for(let i=0;i<mutants.length;i++) {
    const mutant=mutants[i],programMode=mutant.mode==='program';
    const fixture=(programMode?model.programs??[]:model.cases).find(item=>item.name===mutant.witness);
    assert(fixture,`missing mutant witness ${mutant.witness}`);
    let diagnostic;
    try {await run(fixture,mutationPipelines[i],programMode);}
    catch(error) {if(error instanceof ObservationMismatch)diagnostic=error.message;else throw error;}
    assert(diagnostic,`InternalFailure surviving mutant: ${mutant.name}`);
    Object.assign(report.mutants[i],{killed:true,diagnostic});report.semanticKills++;
  }
  report.commands=report.cases.reduce((sum,item)=>sum+item.commands,0);
  report.programRounds=report.programs.reduce((sum,item)=>sum+item.programRounds,0);
  report.dispatches=[...report.cases,...report.programs].reduce((sum,item)=>sum+item.dispatches,0);
  report.observations=[...report.cases,...report.programs].reduce((sum,item)=>sum+item.observations,0);
  report.status='pass';report.deviceExecution=true;
}

try {await main();}
catch(error) {
  report??={contract:layout.contract,deviceExecution:false,semanticKills:0};
  report.status='failure';report.error=error.stack;
  report.classification=/^HostFailure/.test(error.message)?'HostFailure':/^Exhausted/.test(error.message)?'Exhausted':/^Invalid/.test(error.message)?'Invalid':'InternalFailure';
  console.error(error.stack);process.exitCode=1;
} finally {
  if(device)device.destroy();gpu=null;
  if(report) {
    await mkdir(out,{recursive:true});
    await writeFile(resolve(out,validationOnly?'shader-validation.json':'device.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({status:report.status,classification:report.classification,cases:report.cases?.length??0,programs:report.programs?.length??0,
      commands:report.commands??0,programRounds:report.programRounds??0,dispatches:report.dispatches??0,observations:report.observations??0,
      shaderVariants:report.shaderVariants??0,pipelines:report.pipelines??0,semanticKills:report.semanticKills,adapter:report.adapter}));
  }
}
