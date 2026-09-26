// Offline request/coverage test only. No model calibration or probabilities claimed.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {main} from '../../../node_modules/@lakeday/perch/dist/cli.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');process.chdir(root);
const rules=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','source-checkpoint-observation'];
const calls=[];const saved=globalThis.fetch;
globalThis.fetch=async(url,options)=>{assert.equal(String(url),'https://api.typesafe.ai/v1/systemone');const body=JSON.parse(options.body);calls.push(body);return {ok:true,json:async()=>({model:'offline-wiring-only',answers:Object.fromEntries(Object.keys(body.questions).map(k=>[k,{noul:1}]))})};};
const receipts=[];
try {
 for(const [packet,names] of [['packages/source/LAW_REVIEW.md',rules],...['clean','broken','held_out'].map(p=>[`packages/source/tests/perch/${p}.md`,['source-checkpoint-observation']])]){
  const out=[],err=[];const before=calls.length;
  const code=await main(['check',packet,'--rules',names.join(','),'--json'],{env:{PERCH_API_KEY:'offline-wiring-only'},stdout:s=>out.push(s),stderr:s=>err.push(s)});
  assert.equal(code,0,err.join('\n'));const result=JSON.parse(out.join('\n'));assert.equal(result.checked,names.length);assert.equal(calls.length-before,1);assert.equal(Object.keys(calls.at(-1).questions).length,names.length);
  receipts.push({packet,checked:result.checked,requests:1});
 }
 fs.writeFileSync('packages/source/receipts/perch-wiring.json',JSON.stringify({kind:'offline-stub-wiring',provider_contacted:false,calibration:false,model_probabilities:null,receipts},null,2)+'\n');
 console.log('PASS: nine rules cover Source packet; one package rule covers each control; four complete stubbed requests. No live calibration.');
}finally{globalThis.fetch=saved;}
