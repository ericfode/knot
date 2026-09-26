// Bounded parsed-declaration audit, through the shared receipt wrapper.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {analyzeBendSource} from '../../../scripts/perch-bend.mjs';
import {createBendReview} from '../../../scripts/perch-bend-context.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const out=path.join(root,'packages/source/receipts/perch-parsed-2026-09-26');
fs.mkdirSync(out,{recursive:true});
const main='packages/source/main.bend';
const source=fs.readFileSync(path.join(root,main),'utf8');
const sha=createHash('sha256').update(source).digest('hex');
const analysis=await analyzeBendSource(source);
if(analysis.parser_status!=='parsed')throw new Error('Source failed actual parser');
const review=await createBendReview({root,path:main,source,analysis});
const names=['Source.locate','Source.bounded','Source.text','Source.get','Source.cursor','Source.restore','Source.peek','Source.bump','Source.span','Source.extract','Source.offset','build','search','offset_line'];
const rules=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack','perf-growing-prefix-copy','perf-loop-invariant-work','perf-linked-list-indexing','perf-amortized-growth'];
const lawRules=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','source-checkpoint-observation'];
const index=[];let parserIdentity=null;
function receiptFor(after,target,id){return fs.readdirSync(path.join(root,'.perch/usage')).filter(n=>n.endsWith('.json')).map(n=>({file:'.perch/usage/'+n,receipt:JSON.parse(fs.readFileSync(path.join(root,'.perch/usage',n),'utf8'))})).filter(x=>x.receipt.at>=after&&x.receipt.target===target&&(!id||x.receipt.id===id)).sort((a,b)=>a.receipt.at.localeCompare(b.receipt.at)).at(-1);}
for(const name of [...names,null]){
 const target=name?main+'::'+name:'packages/source/LAW_REVIEW.md';
 const selected=name?rules:lawRules;const started=new Date().toISOString();let result,wrapped;
 if(name==='Source.locate'&&process.argv.includes('--reuse-initial-locate')){
  // This one real npm invocation was inspected interactively before this driver.
  wrapped=receiptFor('',main,'9d21c5ad-8825-4970-9fb9-634d0ce06908');
  if(wrapped.receipt.source_sha256!==sha)throw new Error('Stale initial receipt');
  const d=analysis.declarations.find(d=>d.qualified_name===name);
  const context=await review.forUnit(name);
  result={name,line:d.line,end_line:d.end_line,checked:wrapped.receipt.checked,context:context.provenance,context_reconstructed_from_identical_source:true};
 }else{
  const cli=spawnSync('npm',['run','lint','--',target,'--rules',selected.join(','),'--json'],{cwd:root,encoding:'utf8'});
  const start=cli.stdout.indexOf('\n{');
  if(start<0)throw new Error('No structured CLI result; see wrapper failure receipt');
  result=JSON.parse(cli.stdout.slice(start));wrapped=receiptFor(started,name?main:target);
  if(![0,3].includes(cli.status))throw new Error('Perch incomplete; see wrapper receipt');
 }
 const r=wrapped.receipt;
 if(name)parserIdentity=r.parser;
 if(r.checked!==selected.length||r.provider_responses!==1||r.provider_requests!==1||r.answers.length!==selected.length)throw new Error('Incomplete coverage');
 if(name&&r.parser?.status!=='parsed')throw new Error('Missing parsed declaration evidence');
 fs.writeFileSync(path.join(out,r.id+'.json'),JSON.stringify(r,null,2)+'\n');
 fs.writeFileSync(path.join(out,r.id+'-context.json'),JSON.stringify(result,null,2)+'\n');
 index.push({target,receipt:r.id+'.json',cli_context:r.id+'-context.json',wrapper_receipt:wrapped.file,checked:r.checked,provider_responses:r.provider_responses,model:r.resolved_model,source_sha256:r.source_sha256,truncated:result.context?.truncated??false,findings:r.findings});
 console.log(target,r.checked,r.status,'truncated='+String(result.context?.truncated??false),JSON.stringify(r.findings));
 fs.writeFileSync(path.join(out,'index.json'),JSON.stringify({source_sha256:sha,parser:parserIdentity,records:index},null,2)+'\n');
}
