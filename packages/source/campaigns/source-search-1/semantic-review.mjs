import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
const out='packages/source/campaigns/source-search-1/evidence';
const bend=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack','perf-growing-prefix-copy','perf-loop-invariant-work','perf-linked-list-indexing','perf-amortized-growth'];
const laws=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity'];
const index=[];
for(const [label,target,rules] of [['search','packages/source/main.bend::search',bend],['laws','packages/source/campaigns/source-search-1/LAW_REVIEW.md',laws]]){
 const at=new Date().toISOString();const args=['run','lint','--',target,'--rules',rules.join(','),'--json'];
 const r=spawnSync('npm',args,{encoding:'utf8'});
 fs.writeFileSync(`${out}/semantic-${label}-cli.txt`,r.stdout+r.stderr);
 if(![0,3].includes(r.status))throw new Error(`Review incomplete: ${r.status}`);
 const result=JSON.parse(r.stdout.slice(r.stdout.indexOf('\n{')));
 const receipt=fs.readdirSync('.perch/usage').filter(x=>x.endsWith('.json')).map(x=>({path:'.perch/usage/'+x,data:JSON.parse(fs.readFileSync('.perch/usage/'+x))})).filter(x=>x.data.at>=at&&x.data.target===target.split('::')[0]).sort((a,b)=>a.data.at.localeCompare(b.data.at)).at(-1);
 if(!receipt||receipt.data.checked!==rules.length||receipt.data.provider_responses!==1||receipt.data.provider_requests!==1)throw new Error('Incomplete receipt');
 fs.writeFileSync(`${out}/semantic-${label}.json`,JSON.stringify(receipt.data,null,2)+'\n');
 index.push({target,command:['npm',...args],exit:r.status,wrapper_receipt:receipt.path,receipt:`semantic-${label}.json`,checked:receipt.data.checked,model:receipt.data.resolved_model,findings:receipt.data.findings,context:result.context??null});
 fs.writeFileSync(`${out}/semantic-index.json`,JSON.stringify(index,null,2)+'\n');
 console.log(label,receipt.data.checked,receipt.data.resolved_model,JSON.stringify(receipt.data.findings));
}
