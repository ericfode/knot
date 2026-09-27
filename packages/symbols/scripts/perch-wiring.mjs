// Offline shape/coverage verification. Stub probabilities are not calibration.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {main} from '../../../node_modules/@lakeday/perch/dist/cli.mjs';
const pkg=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const receipts=path.resolve(pkg,process.env.SYMBOLS_RECEIPTS_DIR||'receipts/working');
fs.mkdirSync(receipts,{recursive:true});
process.chdir(path.resolve(pkg,'../..'));
const names=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','symbols-bidirectional-preservation'];
let requests=[];
const real=globalThis.fetch;
globalThis.fetch=async(url,opts)=>{
 assert.equal(String(url),'https://api.typesafe.ai/v1/systemone');
 const body=JSON.parse(opts.body); requests.push(body);
 return {ok:true,json:async()=>({model:'offline-wiring-only',answers:Object.fromEntries(Object.keys(body.questions).map(k=>[k,{noul:1}]))})};
};
const results=[];
try {
 for(const packet of ['LAW_REVIEW.md','tests/perch/clean.md','tests/perch/broken.md','tests/perch/held_out.md']) {
  const output=[],errors=[]; requests=[];
  const selected=packet==='LAW_REVIEW.md'?names:[names.at(-1)];
  const code=await main(['check',`packages/symbols/${packet}`,'--rules',selected.join(','),'--json'],{env:{PERCH_API_KEY:'offline-wiring-only'},stdout:s=>output.push(s),stderr:s=>errors.push(s)});
  assert.equal(code,0,errors.join('\n'));
  const json=JSON.parse(output.join('\n')); assert.equal(json.checked,selected.length); assert.equal(requests.length,1); assert.equal(Object.keys(requests[0].questions).length,selected.length);
  results.push({packet,checked:json.checked,requests:requests.length});
 }
 fs.writeFileSync(path.join(receipts,'perch-wiring.json'),JSON.stringify({mode:'offline synthetic provider; no live calibration',results},null,2)+'\n');
 console.log('PASS: 9 review rules and 1 dedicated rule on each of 3 controls; nonzero complete requests. Offline wiring only.');
} finally {globalThis.fetch=real;}
