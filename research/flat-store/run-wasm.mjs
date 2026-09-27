// Invoke exports and compare exact Bend-generated observations. No store semantics.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

const [modulePath, oraclePath, reportPath] = process.argv.slice(2);
const bytes = fs.readFileSync(modulePath);
const oracle = fs.readFileSync(oraclePath, 'utf8');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const sentinel = 0xdecafbad;
const referencePadding = new Uint32Array(32768).fill(sentinel);
const paddingBytes = Buffer.from(referencePadding.buffer);
const report = {status:'incomplete', node:process.version, module_sha256:sha(bytes),
  oracle_sha256:sha(oracle), observations:0, instances:0, installed_boundary_states:0,
  lifecycle_checks:0, imports:[], exports:[]};
let row, actualStatus, actualWords;
function word(x) { assert(Number.isInteger(x) && x>=0 && x<=0xffffffff, 'not a U32'); return x; }
function unchanged(memory, before) { assert(Buffer.from(memory.buffer).equals(before), 'unexpected memory write'); }
try {
  assert(WebAssembly.validate(bytes), 'module validation');
  const module=await WebAssembly.compile(bytes);
  report.imports=WebAssembly.Module.imports(module); report.exports=WebAssembly.Module.exports(module);
  assert.deepEqual(report.imports, []);
  assert.deepEqual(report.exports.map(x=>[x.name,x.kind]),
    ['init','put','alloc','take','release'].map(x=>[x,'function']).concat([['memory','memory']]));
  let e=null, current=null;
  for(const line of oracle.trim().split('\n')) {
    const [id,operation,argsText,statusText,wordsText]=line.split('|');
    const args=JSON.parse(argsText).map(word), expected=JSON.parse(wordsText).map(word);
    const expectedStatus=word(Number(statusText));
    row={id,operation,args,expectedStatus,expectedWords:expected};
    if(operation==='init') {
      e=(await WebAssembly.instantiate(module)).exports; current=id; report.instances++;
      assert.equal(e.memory.buffer.byteLength,131072);
      new Uint32Array(e.memory.buffer).fill(sentinel);
    }
    assert(e && id===current, 'missing instance boundary');
    if(operation==='install') {
      // Privileged fixed input image emitted by Bend for near-ceiling witnesses.
      new Uint32Array(e.memory.buffer,0,expected.length).set(expected);
      actualStatus=0; report.installed_boundary_states++;
    } else {
      assert.equal(e[operation].length,args.length,'ABI arity');
      actualStatus=e[operation](...args)>>>0;
    }
    actualWords=Array.from(new Uint32Array(e.memory.buffer,0,expected.length));
    assert.equal(actualStatus,expectedStatus,'status mismatch');
    assert.deepEqual(actualWords,expected,'word mismatch');
    assert(Buffer.from(e.memory.buffer).subarray(expected.length*4)
      .equals(paddingBytes.subarray(expected.length*4)), 'padding modified');
    report.observations++;
  }
  // Literal lifecycle contracts extend the abstract one-shot model boundary.
  e=(await WebAssembly.instantiate(module)).exports;
  new Uint32Array(e.memory.buffer).fill(sentinel);
  // Passing a typed array copies; passing its ArrayBuffer would alias memory.
  let before=Buffer.from(new Uint8Array(e.memory.buffer));
  for(const [name,args] of [['put',[0,7]],['alloc',[7]],['take',[41,0,0]],['release',[41,0,0]]]) {
    row={id:'lifecycle',operation:name,args}; actualWords=undefined;
    actualStatus=e[name](...args);
    assert.equal(actualStatus,9); unchanged(e.memory,before); report.lifecycle_checks++;
  }
  row={id:'lifecycle',operation:'oversized-init',args:[41,4097,1]};
  actualStatus=e.init(...row.args);
  assert.equal(actualStatus,1); unchanged(e.memory,before); report.lifecycle_checks++;
  assert.equal(e.init(41,1,1),0); assert.equal(e.alloc(7),0);
  before=Buffer.from(new Uint8Array(e.memory.buffer));
  row={id:'lifecycle',operation:'reinit',args:[42,2,0]};
  actualStatus=e.init(...row.args);
  assert.equal(actualStatus,10); unchanged(e.memory,before); report.lifecycle_checks++;
  row={id:'lifecycle',operation:'memory.grow',args:[1]};
  assert.throws(()=>e.memory.grow(1),RangeError); report.lifecycle_checks++;
  report.status='pass';
} catch(error) {
  report.status=error instanceof assert.AssertionError ? 'semantic-mismatch' : 'engine-or-harness-failure';
  report.failure={name:error.name,message:error.message.slice(0,1200),row,actualStatus,actualWords};
  process.exitCode=3;
} finally {
  fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,observations:report.observations,instances:report.instances,
    lifecycle_checks:report.lifecycle_checks,module_sha256:report.module_sha256,
    failure:report.failure?{name:report.failure.name,message:report.failure.message.slice(0,150),id:row?.id,operation:row?.operation}:undefined}));
}
