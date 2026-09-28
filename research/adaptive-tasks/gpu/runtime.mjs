import assert from 'node:assert/strict';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';
import {create, globals} from 'webgpu';

const here=dirname(fileURLToPath(import.meta.url)), root=resolve(here,'../../..');
const sha=x=>createHash('sha256').update(x).digest('hex');
const args=process.argv.slice(2);
let out=resolve(root,'.local/adaptive-tasks/runtime'), validationOnly=false, modelPath;
for(let i=0;i<args.length;i++) {
  if(args[i]==='--validate-only')validationOnly=true;
  else if(args[i]==='--out-dir')out=resolve(args[++i]);
  else if(args[i]==='--model')modelPath=resolve(args[++i]);
  else throw new Error(`unknown argument: ${args[i]}`);
}
const fixturesPath=resolve(here,'../runtime/fixtures.json');
const fixturesText=await readFile(fixturesPath,'utf8'), fixtures=JSON.parse(fixturesText);
assert.equal(fixtures.contract,'knot-device-records-1');
assert.deepEqual(fixtures.programs,[[0,1,2],[1,0,2]],'Unsupported probe instruction bundle');
const shader=await readFile(resolve(here,'runtime.wgsl'),'utf8');
const CANARY=0xdeadbeef, WORDS=36, BYTES=WORDS*4;

// Every replacement preserves WGSL types. Only hardware observation can kill it.
const mutants=[
  {name:'retain-extracted-payload',witness:'reuse-and-retire',edits:[
    ['prepared.w[base+2u]=0u;','prepared.w[base+2u]=value;']]},
  {name:'ignore-generation',witness:'reuse-and-retire',edits:[['generation!=current','false']]},
  {name:'ignore-arena',witness:'reuse-and-retire',edits:[['arena!=prepared.w[2]','false']]},
  {name:'wrap-generation',witness:'reuse-and-retire',edits:[
    ['current<prepared.w[5]','true'],['prepared.w[base+1u]=current+1u','prepared.w[base+1u]=(current+1u)%(prepared.w[5]+1u)']]},
  {name:'consume-full-owner',witness:'capacity-one-preserves-owner',edits:[
    ['if (count>=prepared.w[3]) { reply','if (count>=prepared.w[3]) { prepared.w[base+1u]=2u; reply']]},
  {name:'duplicate-compaction',witness:'zero-quantum-reverse',edits:[
    ['let task=before.w[32u+source]','let task=before.w[32u]']]},
  {name:'change-destination',witness:'suspend-wait-wake-complete',edits:[
    ['work.w[base+2u]=pc+1u;','work.w[base+2u]=pc+1u; work.w[base+4u]=0u;']]},
  {name:'read-before-publication',witness:'zero-quantum-reverse',edits:[
    ['if (prepared.w[base+1u]!=3u)','if (before.w[base+1u]!=3u)']]},
  {name:'advance-zero-budget',witness:'zero-quantum-reverse',edits:[
    ['if (command.a==0u) { work.w[base+1u]=4u; return; }',
     'if (command.a==0u) { work.w[base+1u]=4u; work.w[base+2u]+=1u; return; }']]},
];
function mutate(m) {
  let code=shader;
  for(const [old,replacement] of m.edits) {
    assert.equal(code.split(old).length,2,`${m.name}: mutation anchor`);
    code=code.replace(old,replacement);
  }
  return code;
}
function word(x) { assert(Number.isInteger(x)&&x>=0&&x<=0xffffffff,'Invalid U32 transport'); return x; }
function initial(kind,f) {
  assert(Number.isInteger(f.capacity)&&f.capacity>=0&&f.capacity<=2,'Unsupported capacity');
  const words=new Uint32Array(WORDS).fill(CANARY);
  words.fill(0,0,16);
  words.set([1,kind,word(f.arena??0),f.capacity,kind===4?f.capacity:2,word(f.ceiling??0),kind===4?f.capacity:0]);
  for(let id=0;id<words[4];id++) {
    words.fill(0,16+id*8,24+id*8);
    if(kind===6)words.set([id,1,word(f.initialPc?.[id]??0),id===0?7:9,id===0?73:41,id,id*3,3],16+id*8);
    else words[32+id]=id;
  }
  return words;
}
function frontier(w) {
  return [w[7],w[8],w[9],Array.from(w.slice(32,32+w[6])),
    Array.from({length:2},(_,id)=>Array.from(w.slice(16+8*id,22+8*id)))];
}
const reasons={1:'full',2:'bounds',3:'arena',4:'stale',5:'vacant',6:'occupied',7:'retired'};
function storeEvent(w,cmd) {
  if(w[7]===2) {
    assert.equal(w[8],4,'unsupported reason');
    assert.equal(w[9]|w[10]|w[11],0,'unsupported reply');
    return 'unsupported';
  }
  if(w[7]!==0) {
    assert(reasons[w[8]],'InternalFailure store reason');
    assert.equal(w[7],[1,7].includes(w[8])?3:4,'store outcome classification');
    assert.equal(w[10]|w[11],0,'noncanonical rejected reply');
    if(cmd[0]!==1&&cmd[0]!==4)assert.equal(w[9],0,'rejection exposed a payload');
    return `fail:${reasons[w[8]]}:${cmd[0]===1||cmd[0]===4?w[9]:'-'}`;
  }
  assert.equal(w[8],0,'nonzero success reason');
  if(cmd[0]===1||cmd[0]===4)return `alloc:${w[9]},${w[10]},${w[11]}`;
  assert.equal(w[10]|w[11],0,'noncanonical extraction reply');
  return `${cmd[0]===2?'take':'drop'}:${w[9]}`;
}
function storeSnapshot(w,events) {
  const free=Array.from(w.slice(32,32+w[6]));
  const cells=Array.from({length:w[4]},(_,id)=>{
    const [state,generation,value]=w.slice(16+8*id,19+8*id);
    assert(state<=2,'InternalFailure store tag');
    return state===2?'retired':state===1?`live:${generation}:${value}`:`free:${generation}`;
  });
  return `[${events.join(',')}]/${w[2]};${w[3]};${w[5]};[${free.join(',')}];[${cells.join(',')}]`;
}
function invariant(w,original,kind) {
  assert.deepEqual(w.slice(0,6),original.slice(0,6),'record header changed');
  assert(w[6]<=w[3],'index count exceeds capacity');
  assert(w.slice(12,16).every(x=>x===0),'reserved header changed');
  assert(w.slice(32+w[3]).every(x=>x===CANARY),'queue capacity canary');
  if(kind===4) {
    assert(w.slice(16+8*w[4],32).every(x=>x===CANARY),'store capacity canary');
    for(let id=0;id<w[4];id++) {
      assert(w.slice(19+8*id,24+8*id).every(x=>x===0),'store padding');
      if(w[16+8*id]!==1)assert.equal(w[18+8*id],0,'non-live slot retained payload');
    }
  } else {
    assert.equal(w[10]|w[11],0,'noncanonical task reply');
    for(let id=0;id<2;id++) {
      assert.equal(w[16+8*id],id,'task identity');
      assert.deepEqual(w.slice(19+8*id,24+8*id),original.slice(19+8*id,24+8*id),'task payload/destination/program changed');
    }
  }
}

Object.assign(globalThis,globals);
let gpu,device;
async function host(operation, action) {
  try { return await action(); }
  catch(error) { throw new Error(`HostFailure ${operation}: ${error.message}`,{cause:error}); }
}
async function main() {
  await mkdir(out,{recursive:true});
  gpu=create([`backend=${validationOnly?'null':'metal'}`]);
  const adapter=await host('requestAdapter',()=>gpu.requestAdapter({powerPreference:'high-performance'}));
  if(!adapter)throw new Error('HostFailure device-unavailable: Metal requestAdapter returned null');
  if(!validationOnly)assert.equal(adapter.info.isFallbackAdapter,false,'HostFailure fallback adapter cannot pass');
  device=await host('requestDevice',()=>adapter.requestDevice());
  const uncaptured=[];
  device.addEventListener('uncapturederror',e=>uncaptured.push(e.error.message));
  const layout=device.createBindGroupLayout({entries:[
    ...[0,1,2,3].map(binding=>({binding,visibility:GPUShaderStage.COMPUTE,buffer:{type:binding===0?'read-only-storage':'storage'}})),
    {binding:4,visibility:GPUShaderStage.COMPUTE,buffer:{type:'uniform'}},
    {binding:5,visibility:GPUShaderStage.COMPUTE,buffer:{type:'read-only-storage'}},
  ]});
  const pipelineLayout=device.createPipelineLayout({bindGroupLayouts:[layout]});
  async function compile(code) {
    device.pushErrorScope('validation');
    const module=device.createShaderModule({code});
    const info=await module.getCompilationInfo();
    assert(!info.messages.some(m=>m.type==='error'),JSON.stringify(info.messages));
    const pipelines=[];
    for(const entryPoint of ['prepare','execute','publish'])
      pipelines.push(await device.createComputePipelineAsync({layout:pipelineLayout,compute:{module,entryPoint}}));
    assert.equal(await device.popErrorScope(),null,'pipeline validation');
    return pipelines;
  }
  const pipelines=await compile(shader), mutationPipelines=[];
  for(const m of mutants)mutationPipelines.push(await compile(mutate(m)));
  const report={contract:fixtures.contract,date:new Date().toISOString(),
    adapter:{vendor:adapter.info.vendor,architecture:adapter.info.architecture,device:adapter.info.device,
      description:adapter.info.description,isFallbackAdapter:adapter.info.isFallbackAdapter,backend:validationOnly?'null':'metal'},
    hashes:{shader:sha(shader),runner:sha(await readFile(fileURLToPath(import.meta.url))),fixtures:sha(fixturesText)},
    shaderVariants:1+mutants.length,pipelines:3*(1+mutants.length),deviceExecution:false,semanticKills:0,
    mutants:mutants.map(m=>({name:m.name,witness:m.witness,typechecks:true,killed:false})),cases:[],dispatches:0};
  if(validationOnly) {
    report.status='validation-only';
  } else {
    assert(modelPath,'--model is required for hardware execution');
    const model=JSON.parse(await readFile(modelPath,'utf8'));
    assert.equal(model.fixturesSha256,sha(fixturesText),'stale model fixtures');
    for(const [path,digest] of Object.entries(model.sources))
      assert.equal(sha(await readFile(resolve(root,path))),digest,`stale model: ${path}`);
    report.modelSha256=sha(await readFile(modelPath));
    async function run(kind,f,ps) {
      const observed=model.cases[f.name]; assert(observed,'missing model case');
      const start=initial(kind,f), buffers=[];
      const storage=GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC|GPUBufferUsage.COPY_DST;
      function buffer(size,usage,data) {
        const b=device.createBuffer({size,usage});buffers.push(b);
        if(data)device.queue.writeBuffer(b,0,data);
        return b;
      }
      const a=buffer(BYTES,storage,start),p=buffer(BYTES,storage),w=buffer(BYTES,storage),b=buffer(BYTES,storage);
      const cmd=buffer(32,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST);
      const code=new Uint32Array(fixtures.programs.flat());
      const instructions=buffer(code.byteLength,storage,code);
      const back=buffer(3*BYTES,GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ);
      const groups=[[a,b],[b,a]].map(([input,output])=>device.createBindGroup({layout,entries:
        [input,p,w,output,cmd,instructions].map((buffer,binding)=>({binding,resource:{buffer}}))}));
      const events=[],trace=[];
      device.pushErrorScope('validation');
      try {
        for(let step=0;step<f.commands.length;step++) {
          const command=f.commands[step],packed=new Uint32Array(8);
          packed.set(command.map(word));device.queue.writeBuffer(cmd,0,packed);
          const enc=device.createCommandEncoder();
          for(let phase=0;phase<3;phase++) {
            const pass=enc.beginComputePass();pass.setBindGroup(0,groups[step%2]);
            pass.setPipeline(ps[phase]);pass.dispatchWorkgroups(1);pass.end();
          }
          const output=step%2===0?b:a;
          [p,w,output].forEach((buffer,phase)=>enc.copyBufferToBuffer(buffer,0,back,phase*BYTES,BYTES));
          await host('submit',()=>device.queue.submit([enc.finish()]));
          await host('mapAsync',()=>back.mapAsync(GPUMapMode.READ));
          const raw=new Uint32Array(back.getMappedRange().slice(0));back.unmap();
          const phases=[];
          for(let phase=0;phase<3;phase++) {
            const state=raw.slice(phase*WORDS,(phase+1)*WORDS);
            // Tag semantic assertions so a shader/host error cannot kill a mutant.
            try {
              invariant(state,start,kind);
              const value=kind===4?storeSnapshot(state,[...events,storeEvent(state,command)]):frontier(state);
              assert.deepEqual(value,observed[step][phase]);phases.push(value);
            } catch(e) { throw new Error(`observation mismatch: ${f.name} step ${step} phase ${phase}: ${e.message}`); }
          }
          if(kind===4)events.push(storeEvent(raw.slice(2*WORDS),command));
          trace.push(phases);
        }
        return {name:f.name,commands:f.commands.length,phases:trace.length*3,trace};
      } finally {
        await host('onSubmittedWorkDone',()=>device.queue.onSubmittedWorkDone());
        for(const buffer of buffers)buffer.destroy();
        assert.equal(await device.popErrorScope(),null,'dispatch validation');
        assert.equal(uncaptured.length,0,uncaptured.join('\n'));
      }
    }
    for(const [kind,cases] of [[4,fixtures.store],[6,fixtures.frontier]])
      for(const f of cases)report.cases.push(await run(kind,f,pipelines));
    for(let i=0;i<mutants.length;i++) {
      const m=mutants[i],store=fixtures.store.find(f=>f.name===m.witness);
      const fixture=store??fixtures.frontier.find(f=>f.name===m.witness);
      let kill;
      try {await run(store?4:6,fixture,mutationPipelines[i]);}
      catch(e) {if(e.message.startsWith(`observation mismatch: ${m.witness} `))kill=e.message;else throw e;}
      assert(kill,`surviving mutant: ${m.name}`);
      report.mutants[i].killed=true;report.mutants[i].diagnostic=kill;report.semanticKills++;
    }
    report.dispatches=report.cases.reduce((sum,c)=>sum+c.phases,0);
    report.status='pass';report.deviceExecution=true;
  }
  assert.equal(uncaptured.length,0,uncaptured.join('\n'));
  await writeFile(resolve(out,validationOnly?'shader-validation.json':'device.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,cases:report.cases.length,dispatches:report.dispatches,
    shaderVariants:report.shaderVariants,pipelines:report.pipelines,semanticKills:report.semanticKills,adapter:report.adapter}));
}
try {await main();}
catch(error) {console.error(error.stack);process.exitCode=1;}
finally {if(device)device.destroy();gpu=null;}
