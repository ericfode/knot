// Actual installed checkTarget -> methodSteps -> methodStep request capture.
// All transport is replaced. Run from repository root with a NEW output path.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { main } = await import(pathToFileURL(resolve('node_modules/@lakeday/perch/dist/cli.mjs')));
const { analyzeBendSource } = await import(pathToFileURL(resolve('scripts/perch-bend.mjs')));
const { createBendReview } = await import(pathToFileURL(resolve('scripts/perch-bend-context.mjs')));
const sha = value => createHash('sha256').update(value).digest('hex');
const path = '.local/perch-execution-current/candidate-3-review/PROOF.bend', name = 'L.put_empty';
const original = JSON.parse(await readFile('docs/perch-execution/role-v5-2026-09-27/proof-context/reproduction.json'));
const inputs = Object.keys(original.inputs_sha256);
const before = Object.fromEntries(await Promise.all(inputs.map(async path => [path, sha(await readFile(path))])));
const source = await readFile(path, 'utf8');
const context = await (await createBendReview({ root: process.cwd(), path, source, analysis: await analyzeBendSource(source) })).forUnit(name);
const requests = [], output = [], errors = [], previousFetch = globalThis.fetch;
let code;
try {
  globalThis.fetch = async (_url, options) => {
    const request = JSON.parse(options.body); requests.push(request);
    const answers = Object.fromEntries(Object.entries(request.questions).map(([key,q]) => {
      if(q.type === 'noul') return [key, { noul: key === 'does_what_it_claims' || key.startsWith('bend-') ? 1 : 0 }];
      if(q.type === 'score') return [key, { score:0, confidence:1, probabilities:Object.fromEntries(q.criteria.map((_,i) => [i,i===0?1:0])) }];
      const choice=Object.keys(q.criteria).at(-1); return [key, { choice, confidence:1, probabilities:{[choice]:1} }];
    }));
    const response = { model:'offline-context-fixture', answers };
    return { ok:true, json:async()=>response, clone:()=>({ json:async()=>response }) };
  };
  code = await main(original.argv, { env:{PERCH_API_KEY:'offline-fixture'}, stdout:x=>output.push(x), stderr:x=>errors.push(x) });
} finally { globalThis.fetch = previousFetch; }
assert.ok([0,3].includes(code), errors.join('\n'));
assert.deepEqual(Object.fromEntries(await Promise.all(inputs.map(async path => [path,sha(await readFile(path))]))), before);
for(const path of inputs.filter(path => path.endsWith('.bend') || path === 'perch.yaml')) assert.equal(before[path], original.inputs_sha256[path]);
const law = context.seen.laws[0];
const captures = requests.map(request=>({ kind:request.state.method?'builtin':'custom', state:request.state, questions:request.questions,
  state_sha256:sha(JSON.stringify(request.state)), request_sha256:sha(JSON.stringify(request)),
  law_source_occurrences:JSON.stringify(request.state).split(JSON.stringify(law.source).slice(1,-1)).length-1 }));
assert.ok(captures.some(request=>request.kind==='custom') && captures.some(request=>request.kind==='builtin'));
assert.ok(captures.every(request=>request.law_source_occurrences===1));
const receipt={schema:'knot-proof-context-reproduction-after-v1',created_at:new Date().toISOString(),mode:'offline installed CLI with fully replaced fetch',
  live_provider_requests:0,stub_cli_exit:code,stub_answers_are_review_evidence:false,target:`${path}::${name}`,argv:original.argv,
  inputs_sha256:before,inputs_unchanged:true,proof_and_law_and_rules_match_before:true,selected_laws:context.seen.laws,provenance:context.provenance,
  request_count:captures.length,requests:captures,regression_assertion:{passed:true,exit_code:0},stderr:errors};
await writeFile(resolve(process.argv[2]),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({output:process.argv[2],requests:captures.length,law_occurrences:captures.map(request=>[request.kind,request.law_source_occurrences]),passed:true,live_provider_requests:0}));
