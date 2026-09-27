// Exercise existing cache identity guards offline against the captured states.
import assert from 'node:assert/strict';
import {readFile,mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {createStyleAnswerCache} from '../../../../scripts/perch-style-cache.mjs';

const hash=x=>createHash('sha256').update(x).digest('hex');
const before=JSON.parse(await readFile(new URL('before.json',import.meta.url)));
const after=JSON.parse(await readFile(new URL('after.json',import.meta.url)));
assert.equal(before.rubric_sha256,after.rubric_sha256);
assert.notEqual(before.parser,after.parser);
assert.notEqual(before.context_contract_sha256,after.context_contract_sha256);
const root=await mkdtemp(join(tmpdir(),'knot-datatype-cache-'));
const results=[];
try{
  const identity=record=>({parser:record.parser,rubric_sha256:record.rubric_sha256,
    requested_model:'offline-cache-control',endpoint_sha256:'offline-only',
    context_contract_sha256:record.context_contract_sha256});
  const oldCache=createStyleAnswerCache(root,identity(before));
  const newCache=createStyleAnswerCache(root,identity(after));
  for(let index=0;index<before.targets.length;index++){
    const old=before.targets[index],current=after.targets[index];
    assert.equal(old.prepared.target,current.prepared.target);
    assert.equal(old.prepared.source_sha256,current.prepared.source_sha256);
    assert.notEqual(old.prepared.state_sha256,current.prepared.state_sha256);
    assert.notEqual(old.request_sha256,current.request_sha256);
    await oldCache.write(old.prepared,old.request_sha256,{model:'offline-cache-control',answers:{}},new Date().toISOString());
    assert(await oldCache.read(old.prepared,old.request_sha256,x=>x));
    assert.equal(await newCache.read(old.prepared,old.request_sha256,x=>x),null,'new parser/context identity rejects even old unchanged state');
    assert.equal(await newCache.read(current.prepared,current.request_sha256,x=>x),null,'new request cannot reuse the historical answer');
    results.push({target:current.prepared.target,old_identity_hit:true,new_identity_old_request_miss:true,new_request_miss:true,
      source_unchanged:true,before_state:old.prepared.state_sha256,after_state:current.prepared.state_sha256,
      before_request:old.request_sha256,after_request:current.request_sha256});
  }
  const bundle=await readFile(new URL('../../../../node_modules/@lakeday/perch/dist/cli.mjs',import.meta.url),'utf8');
  const record={schema:'knot.datatype-cache-invalidation.v1',status:'passed',provider_requests:0,
    rubric_unchanged:true,before_parser:before.parser,after_parser:after.parser,
    before_context_sha256:before.context_contract_sha256,after_context_sha256:after.context_contract_sha256,
    installed_adapter_profile:bundle.match(/var ANALYSIS_PROFILE = "([^"]+)"/)[1],
    installed_bundle_sha256:hash(bundle),old_cache_stats:oldCache.stats,new_cache_stats:newCache.stats,results};
  await writeFile(new URL('cache-invalidation.json',import.meta.url),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({status:record.status,installed_adapter_profile:record.installed_adapter_profile,probes:results.length}));
}finally{await rm(root,{recursive:true,force:true});}
