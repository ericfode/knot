// Offline request preparation only. No provider, cache writes or score reassessment.
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {prepareStyleTargets} from '../../../../scripts/perch-style.mjs';
import {BEND_PARSER_PROFILE} from '../../../../scripts/perch-bend.mjs';

const root=fileURLToPath(new URL('../../../../',import.meta.url));
const output=process.argv[2];
if(!/^(before|after)\.json$/.test(output??'')) throw new Error('Use before.json or after.json; never overwrite evidence');
const hash=value=>createHash('sha256').update(value).digest('hex');
const read=name=>readFile(resolve(root,name));
const configText=await read('perch-style.json'),config=JSON.parse(configText);
const report={schema:'knot.datatype-context-preparation.v1',at:new Date().toISOString(),
  provider_requests:0,answers_reassessed:false,parser:BEND_PARSER_PROFILE,
  rubric_sha256:hash(configText),context_contract_sha256:hash(await read('scripts/perch-bend-context.mjs')),
  parser_adapter_sha256:hash(await read('scripts/perch-bend.mjs')),targets:[]};
for(const [receiptPath,names] of [
  ['docs/perch-execution/role-v5-2026-09-27/task-baseline.json.gz',['tick_owned','combine']],
  ['research/adaptive-tasks/comparison-gate/receipts/style-oracle-v5.json.gz',['frame_json']]]){
  const receiptBytes=await read(receiptPath),receipt=JSON.parse(gunzipSync(receiptBytes));
  const contract=receipt.potential_profundity.review.request.state.contract;
  for(const name of names){
    const previous=receipt.rows.find(row=>row.target.endsWith('::'+name));
    const [prepared]=await prepareStyleTargets([previous.target],contract,config,root);
    const rubrics=[...config.dimensions,...(prepared.context.truncated?[]:config.diagnostic_dimensions),config.criticality,config.style_role];
    const questions=Object.fromEntries(rubrics.map(d=>[d.id,{type:'score',instructions:d.instructions,criteria:d.levels}]));
    const request={model:receipt.requested_model,state:prepared.state,questions};
    report.targets.push({receipt:receiptPath,receipt_sha256:hash(receiptBytes),
      recorded_source_sha256:previous.source_sha256,recorded_state_sha256:previous.state_sha256,
      source_matches_receipt:prepared.source_sha256===previous.source_sha256,
      state_matches_receipt:prepared.state_sha256===previous.state_sha256,
      context_sha256:hash(JSON.stringify(prepared.context)),request_sha256:hash(JSON.stringify(request)),
      prepared});
  }
}
await writeFile(new URL(output,import.meta.url),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({output,parser:report.parser,targets:report.targets.map(t=>({target:t.prepared.target,state:t.prepared.state_sha256,request:t.request_sha256,source_matches_receipt:t.source_matches_receipt,state_matches_receipt:t.state_matches_receipt}))}));
