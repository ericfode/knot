// Capture the existing host packer, without reimplementing it or creating a GPU.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { Script } from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../..');
const host=await readFile(resolve(here,'../gpu/check.mjs'),'utf8');
const start='function word(', end='\nObject.assign(globalThis,globals);';
assert.equal(host.split(start).length,2,'packer start changed');
assert.equal(host.split(end).length,2,'packer end changed');
const first=host.indexOf(start), last=host.indexOf(end);
assert(first<last);
const packer=host.slice(first,last);
const text=execFileSync(resolve(root,'scripts/bend-reference'),
  [resolve(here,'../fixtures.bend')],{cwd:root,encoding:'utf8',timeout:60000});
const fixture=text.trim().split('\n').map(JSON.parse).find(x=>x.name==='cpu_frames');
assert(fixture);
// These constants are checked against the actual host before executing its body.
assert(host.includes('const NONE=0xffffffff, SENTINEL=0xdeadbeef;'));
assert(host.includes('const MAX_NODES=4096, OP_WORDS=12, TASK_WORDS=16;'));
const packed=new Script(packer+'\npack(tree);').runInNewContext({
  assert,NONE:0xffffffff,MAX_NODES:4096,TASK_WORDS:16,tree:fixture.tree,
},{timeout:1000});
const tasks=Array.from({length:packed.n},(_,i)=>Array.from(packed.states.slice(i*16,(i+1)*16)));
const opFields=['kind','left','right','seed','ticks','factor','bias','parent','slot','pad0','pad1','pad2'];
const taskFields=['state','remaining','value','left_value','right_value','mask','last_worker','moves',
  'runs','steps','destination','slot','factor','bias','completed_round','pad'];
const arrayLines=rows=>rows.map(row=>'    '+JSON.stringify(row)).join(',\n');
process.stdout.write('{'+'\n'+[
  '  "fixture": '+JSON.stringify(fixture),
  '  "packer": '+JSON.stringify({path:'research/adaptive-tasks/gpu/check.mjs',
    firstLine:host.slice(0,first).split('\n').length,lastLine:host.slice(0,last).split('\n').length,
    sha256:createHash('sha256').update(packer).digest('hex')}),
  '  "root": '+packed.root,
  '  "opFields": '+JSON.stringify(opFields),
  '  "operations": [\n'+arrayLines(packed.records)+'\n  ]',
  '  "taskFields": '+JSON.stringify(taskFields),
  '  "initialTasks": [\n'+arrayLines(tasks)+'\n  ]',
].join(',\n')+'\n}\n');
