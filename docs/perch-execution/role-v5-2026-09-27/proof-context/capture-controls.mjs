// Offline actual-CLI control capture. Run from repository root with a NEW output path.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const workspace = process.cwd();
const { runPerch } = await import(pathToFileURL(resolve('scripts/perch-workflow.mjs')));
const root = await mkdtemp(join(tmpdir(), 'knot-proof-controls-'));
const previousFetch = globalThis.fetch;
const sha = value => createHash('sha256').update(value).digest('hex');
const requests = [];
try {
  await writeFile(join(root, 'ordinary.bend'), 'import Base\ndef identity(x: U32) -> U32: x\n');
  await writeFile(join(root, 'ordinary.js'), 'export function identity(x) { return x; }\n');
  await writeFile(join(root, 'perch.yaml'), 'rules:\n  - name: fixture-contract\n    where: "**/*"\n    each: method\n    gate: false\n    ensure: Returns its input.\n');
  const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
  git(['init', '-q']); git(['add', '.']);
  git(['-c','user.name=Offline proof fixture','-c','user.email=fixture@example.invalid','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','commit','-qm','fixture']);
  globalThis.fetch = async (_url, options) => {
    const body = JSON.parse(options.body); requests.push(body);
    const answers = Object.fromEntries(Object.entries(body.questions).map(([key,q]) => {
      if (q.type === 'noul') return [key,{noul:key === 'fixture-contract' || key === 'does_what_it_claims' ? 1 : 0}];
      if (q.type === 'score') return [key,{score:0,confidence:1,probabilities:Object.fromEntries(q.criteria.map((_,i)=>[i,i===0?1:0]))}];
      const choice=Object.keys(q.criteria).at(-1); return [key,{choice,confidence:1,probabilities:{[choice]:1}}];
    }));
    const response={model:'offline-proof-control',answers};
    return {ok:true,json:async()=>response,clone:()=>({json:async()=>response})};
  };
  const runs=[];
  for(const target of ['ordinary.bend::identity','ordinary.js::identity']) {
    const output=[],errors=[],start=requests.length;
    const code=await runPerch(['check',target,'--parallel','1'],{root,env:{PERCH_API_KEY:'offline-fixture'},stdout:x=>output.push(x),stderr:x=>errors.push(x)});
    assert.ok([0,3].includes(code),errors.join('\n'));
    assert.ok(requests.slice(start).some(r=>r.state.method),'nonzero built-in coverage');
    runs.push({target,code,requests:requests.slice(start),stderr:errors});
  }
  const receipt={mode:'offline stub fetch; no provider requests',bundle_sha256:sha(await readFile(join(workspace,'node_modules/@lakeday/perch/dist/cli.mjs'))),runs};
  const out=resolve(workspace,process.argv[2]);
  await writeFile(out,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({output:out,requests:requests.length,live_provider_requests:0}));
} finally { globalThis.fetch=previousFetch; await rm(root,{recursive:true,force:true}); }
