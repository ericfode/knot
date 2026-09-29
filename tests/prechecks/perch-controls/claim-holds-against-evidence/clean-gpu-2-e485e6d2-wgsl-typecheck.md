<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=gpu-2; head=e485e6d29497; base=d14418b7cb04; builder=scripts/prechecks/packets@3a2ef420dff1; sources: research/adaptive-tasks/runtime2/SPEC.md@e485e6d2 sha256=8a28edaa4c8ecb06ab7dd4dc2185df7df8e34482c88c4da6493101b775b2a624; research/adaptive-tasks/runtime2/device.mjs@e485e6d2 sha256=b6ae9fcd92215bc681a61cd54a9c258e438126ae4151fdaee20663e9acdb8bcb -->
# Claim
research/adaptive-tasks/runtime2/SPEC.md:144-145 (section: Evidence boundary) - verbatim text:

> WGSL mutants must typecheck. Only real-device mismatches kill WGSL mutants;
> null-backend validation records them as constructed/typechecked, never killed.

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
`research/adaptive-tasks/runtime2/device.mjs:123-282` (added)
  123  async function main() {
  124    await mkdir(out,{recursive:true});
  125    const {create,globals}=await loadWebGPU();Object.assign(globalThis,globals);
  126    gpu=create([`backend=${validationOnly?'null':'metal'}`]);
  127    const adapter=await host('requestAdapter',()=>gpu.requestAdapter({powerPreference:'high-performance'}));
  128    if(!adapter)throw new Error('HostFailure device-unavailable: requestAdapter returned null');
  129    if(!validationOnly&&adapter.info.isFallbackAdapter!==false)throw new Error('HostFailure fallback adapter cannot qualify device execution');
  130    const requiredLimits={maxStorageBufferBindingSize:adapter.limits.maxStorageBufferBindingSize,maxBufferSize:adapter.limits.maxBufferSize};
  131    device=await host('requestDevice',()=>adapter.requestDevice({requiredLimits}));
  132    device.addEventListener('uncapturederror',event=>uncaptured.push(event.error.message));
  133    const storageLimit=Math.min(MAX-3,device.limits.maxStorageBufferBindingSize,device.limits.maxBufferSize);
  134    const bindLayout=device.createBindGroupLayout({entries:[
  135      ...[0,1,2].map(binding=>({binding,visibility:GPUShaderStage.COMPUTE,buffer:{type:binding===0?'read-only-storage':'storage'}})),
  136      {binding:3,visibility:GPUShaderStage.COMPUTE,buffer:{type:'uniform',hasDynamicOffset:true,minBindingSize:16}},
  137      {binding:4,visibility:GPUShaderStage.COMPUTE,buffer:{type:'read-only-storage'}},
  138    ]});
  139    const pipelineLayout=device.createPipelineLayout({bindGroupLayouts:[bindLayout]});
  140    async function compile(source) {
  141      device.pushErrorScope('validation');
  142      try {
  143        const module=device.createShaderModule({code:source});
  144        const info=await module.getCompilationInfo();
  145        assert(!info.messages.some(message=>message.type==='error'),`InternalFailure WGSL typecheck: ${JSON.stringify(info.messages)}`);
  146        const pipelines=[];
  147        for(const entryPoint of ['execute','run','publish'])pipelines.push(await device.createComputePipelineAsync({layout:pipelineLayout,compute:{module,entryPoint}}));
  148        return pipelines;
  149      } finally {
  150        const error=await device.popErrorScope();
  151        if(error)throw new Error(`InternalFailure pipeline validation: ${error.message}`);
  152      }
  153    }
  154    const pipelines=await compile(shader),mutationPipelines=[];
  155    for(const mutant of mutants)mutationPipelines.push(await compile(mutate(shader,mutant)));
  156    report={contract:layout.contract,date:new Date().toISOString(),
  157      adapter:{vendor:adapter.info.vendor,architecture:adapter.info.architecture,device:adapter.info.device,
  158        description:adapter.info.description,isFallbackAdapter:adapter.info.isFallbackAdapter,backend:validationOnly?'null':'metal'},
  159      limits:{maxStorageBufferBindingSize:device.limits.maxStorageBufferBindingSize,maxBufferSize:device.limits.maxBufferSize,checkedStorageBytes:storageLimit},
  160      hashes:{shader:sha(shader),runner:sha(await readFile(fileURLToPath(import.meta.url))),mutants:sha(await readFile(resolve(here,'mutants.mjs'))),layout:sha(layoutText),fixtures:sha(fixturesText),programs:sha(programsText)},
  161      shaderVariants:1+mutants.length,pipelines:3*(1+mutants.length),deviceExecution:false,semanticKills:0,
  162      mutants:mutants.map(mutant=>({name:mutant.name,witness:mutant.witness,typechecks:true,killed:false,shaderSha256:sha(mutate(shader,mutant))})),
  163      cases:[],programs:[],commands:0,programRounds:0,dispatches:0,observations:0};
  164    if(validationOnly) {report.status='validation-only';return;}
  165    assert(modelPath,'Invalid: --model is required for hardware execution');
  166    const modelText=await readFile(modelPath,'utf8'),model=JSON.parse(modelText);
  167    if(model.contract)assert.equal(model.contract,layout.contract,'model contract');
  168    if(model.fixturesSha256)assert.equal(model.fixturesSha256,sha(fixturesText),'stale model fixtures');
  169    if(model.programsSha256)assert.equal(model.programsSha256,sha(programsText),'stale model programs');
  170    for(const [path,digest] of Object.entries(model.sources??{}))assert.equal(sha(await readFile(resolve(root,path))),digest,`stale model ${path}`);
  171    report.modelSha256=sha(modelText);
  172    assert(Array.isArray(model.cases),'Invalid model case table');
  173  
  174    async function run(fixture,ps,programMode=false) {
  175      const rounds=programMode?fixture.quanta:fixture.commands.map((_,index)=>index);
  176      assert.equal(rounds.length,fixture.observations.length,'missing per-round observations');
  177      if(programMode)rounds.forEach(word);
  178      const start=fixture.words.map(word),limit=Math.min(storageLimit,word(fixture.config.maxStorageBytes));
  179      const bytes=checkedBytes(start.length,limit,'state');
  180      assert(start.length>=36,'Invalid state header');
  181      const code=new Uint32Array(fixture.commands.flatMap(command=>{
  182        assert.equal(command.length,8,'Invalid instruction stride');return command.map(word);
  183      }));
  184      const codeBytes=checkedBytes(Math.max(1,code.length),limit,'instructions');
  185      assert.equal(start[H.instructionCount],fixture.commands.length,'instruction count');
  186      observe(start,start,programMode);
  187      const buffers=[],usage=GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC|GPUBufferUsage.COPY_DST;
  188      function buffer(size,usage,data) {
  189        if(size>device.limits.maxBufferSize)throw new Error(`Exhausted buffer size ${size}`);
  190        const value=device.createBuffer({size,usage});buffers.push(value);
  191        if(data?.byteLength)device.queue.writeBuffer(value,0,data);
  192        return value;
  193      }
  194      const a=buffer(bytes,usage,new Uint32Array(start)),b=buffer(bytes,usage),work=buffer(bytes,usage);
  195      const program=buffer(codeBytes,usage,code);
  196      const align=device.limits.minUniformBufferOffsetAlignment;
  197      if(Math.max(1,rounds.length)>Math.floor(device.limits.maxBufferSize/align))
  198        throw new Error('Exhausted instruction-index uniform buffer');
  199      const stepWords=new Uint32Array(Math.max(1,rounds.length)*align/4);
  200      for(let i=0;i<rounds.length;i++)stepWords[i*align/4]=rounds[i];
  201      const steps=buffer(stepWords.byteLength,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST,stepWords);
  202      const backs=[0,1].map(()=>buffer(bytes,GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ));
  203      const groups=[[a,b],[b,a]].map(([input,output])=>device.createBindGroup({layout:bindLayout,entries:[
  204        {binding:0,resource:{buffer:input}},{binding:1,resource:{buffer:work}},{binding:2,resource:{buffer:output}},
  205        {binding:3,resource:{buffer:steps,size:16}},{binding:4,resource:{buffer:program}},
  206      ]}));
  207      const trace=[];let encoder=device.createCommandEncoder(),unsubmitted=false;
  208      device.pushErrorScope('validation');
  209      try {
  210        for(let index=0;index<rounds.length;index++) {
  211          for(const pipeline of [ps[programMode?1:0],ps[2]]) {
  212            const pass=encoder.beginComputePass();pass.setPipeline(pipeline);
  213            pass.setBindGroup(0,groups[index%2],[index*align]);pass.dispatchWorkgroups(1);pass.end();
  214          }
  215          unsubmitted=true;
  216          const expected=fixture.observations[index];
  217          if(expected===null)continue;
  218          const output=index%2===0?b:a;
  219          encoder.copyBufferToBuffer(work,0,backs[0],0,bytes);encoder.copyBufferToBuffer(output,0,backs[1],0,bytes);
  220          await host('submit',()=>device.queue.submit([encoder.finish()]));unsubmitted=false;
  221          await host('mapAsync',()=>Promise.all(backs.map(back=>back.mapAsync(GPUMapMode.READ))));
  222          const raw=backs.map(back=>{const words=new Uint32Array(back.getMappedRange().slice(0));back.unmap();return words;});
  223          const phases=[];
  224          for(let phase=0;phase<2;phase++) {
  225            try {
  226              const state=raw[phase];
  227              const projection=observe(state,start,programMode);
  228              const observation=programMode?{pc:state[H.pc],phase:state[H.phase],state:projection}:projection;
  229              assert.deepEqual(observation,expected);
  230              phases.push({phase:phase===0?'execute':'publish',wordsSha256:sha(state),observation});
  231            } catch(error) {throw new ObservationMismatch(`${fixture.name} step ${index} phase ${phase}: ${error.message}`);}
  232          }
  233          trace.push({step:index,phases});encoder=device.createCommandEncoder();
  234        }
  235        if(unsubmitted)await host('submit',()=>device.queue.submit([encoder.finish()]));
  236        return {name:fixture.name,instructions:fixture.commands.length,commands:programMode?0:rounds.length,
  237          programRounds:programMode?rounds.length:0,dispatches:2*rounds.length,observations:trace.length*2,trace};
  238      } finally {
  239        await host('onSubmittedWorkDone',()=>device.queue.onSubmittedWorkDone());
  240        for(const value of buffers)value.destroy();
  241        const error=await device.popErrorScope();
  242        if(error)throw new Error(`HostFailure dispatch validation: ${error.message}`);
  243        if(uncaptured.length)throw new Error(`HostFailure uncaptured device errors: ${uncaptured.join('\n')}`);
  244      }
  245    }
  246  
  247    for(const fixture of model.cases)report.cases.push(await run(fixture,pipelines));
  248    for(const fixture of model.programs??[])report.programs.push(await run(fixture,pipelines,true));
  249    for(let i=0;i<mutants.length;i++) {
  250      const mutant=mutants[i],programMode=mutant.mode==='program';
  251      const fixture=(programMode?model.programs??[]:model.cases).find(item=>item.name===mutant.witness);
  252      assert(fixture,`missing mutant witness ${mutant.witness}`);
  253      let diagnostic;
  254      try {await run(fixture,mutationPipelines[i],programMode);}
  255      catch(error) {if(error instanceof ObservationMismatch)diagnostic=error.message;else throw error;}
  256      assert(diagnostic,`InternalFailure surviving mutant: ${mutant.name}`);
  257      Object.assign(report.mutants[i],{killed:true,diagnostic});report.semanticKills++;
  258    }
  259    report.commands=report.cases.reduce((sum,item)=>sum+item.commands,0);
  260    report.programRounds=report.programs.reduce((sum,item)=>sum+item.programRounds,0);
  261    report.dispatches=[...report.cases,...report.programs].reduce((sum,item)=>sum+item.dispatches,0);
  262    report.observations=[...report.cases,...report.programs].reduce((sum,item)=>sum+item.observations,0);
  263    report.status='pass';report.deviceExecution=true;
  264  }
  265  
  266  try {await main();}
  267  catch(error) {
  268    report??={contract:layout.contract,deviceExecution:false,semanticKills:0};
  269    report.status='failure';report.error=error.stack;
  270    report.classification=/^HostFailure/.test(error.message)?'HostFailure':/^Exhausted/.test(error.message)?'Exhausted':/^Invalid/.test(error.message)?'Invalid':'InternalFailure';
  271    console.error(error.stack);process.exitCode=1;
  272  } finally {
  273    if(device)device.destroy();gpu=null;
  274    if(report) {
  275      await mkdir(out,{recursive:true});
  276      await writeFile(resolve(out,validationOnly?'shader-validation.json':'device.json'),JSON.stringify(report,null,2)+'\n');
  277      console.log(JSON.stringify({status:report.status,classification:report.classification,cases:report.cases?.length??0,programs:report.programs?.length??0,
  278        commands:report.commands??0,programRounds:report.programRounds??0,dispatches:report.dispatches??0,observations:report.observations??0,
  279        shaderVariants:report.shaderVariants??0,pipelines:report.pipelines??0,semanticKills:report.semanticKills,adapter:report.adapter}));
  280    }
  281  }
  282  
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
