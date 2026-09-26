#!/usr/bin/env node
// A bounded parsed-source pass; all provider calls use the shared npm wrapper.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {analyzeBendSource} from '../../../scripts/perch-bend.mjs';
import {createBendReview} from '../../../scripts/perch-bend-context.mjs';
const pkg=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const root=path.resolve(pkg,'../..');
const out=path.join(pkg,'evidence/perch-parsed');
await fs.mkdir(out,{recursive:true});
const sha=s=>createHash('sha256').update(s).digest('hex');
const target='packages/vec/main.bend';
const source=await fs.readFile(path.join(root,target),'utf8');
const analysis=await analyzeBendSource(source);
if(analysis.parser_status!=='parsed'||!analysis.declarations.length)throw new Error('Parser coverage unavailable');
const review=await createBendReview({root,path:target,source,analysis});
const declarations=[];
for(const d of analysis.declarations){
  const c=await review.forUnit(d.qualified_name);
  declarations.push({name:d.qualified_name,line:d.line,end_line:d.end_line,context:c.provenance,helpers:c.seen.calls.map(({name,line,end_line})=>({name,line,end_line})),callers:c.seen.called_by.map(({name,line,end_line})=>({name,line,end_line}))});
}
await fs.writeFile(path.join(out,'preflight.json'),JSON.stringify({target,source_sha256:sha(source),parser:analysis.parser_metadata,profile:analysis.profile,parser_status:analysis.parser_status,diagnostics:analysis.diagnostics,declarations},null,2)+'\n');
const sourceRules=['bend-fuel-completeness','bend-machine-arithmetic','bend-borrow-lifetime','bend-ordered-f32','bend-effect-boundary','bend-device-stack','perf-growing-prefix-copy','perf-loop-invariant-work','perf-linked-list-indexing','perf-amortized-growth'];
const lawRules=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','vec-logical-state-observation'];
const runs=[];
for(const [file,rules,label] of [[target,sourceRules,'implementation'],['packages/vec/LAW_REVIEW.md',lawRules,'law-packet']]){
  const before=new Set(await fs.readdir(path.join(root,'.perch/usage')));
  const args=['run','lint','--',file,'--rules',rules.join(','),'--json'];
  const run=spawnSync('npm',args,{cwd:root,encoding:'utf8',timeout:180000,maxBuffer:16*1024*1024});
  const added=(await fs.readdir(path.join(root,'.perch/usage'))).filter(n=>!before.has(n)&&n.endsWith('.json'));
  const candidates=[];
  for(const name of added){const receipt=JSON.parse(await fs.readFile(path.join(root,'.perch/usage',name),'utf8'));if(receipt.target===file&&JSON.stringify(receipt.selected_rules)===JSON.stringify(rules))candidates.push({name,receipt});}
  if(candidates.length!==1)throw new Error(`Expected one wrapper receipt for ${file}, got ${candidates.length}; npm exit ${run.status}`);
  const {name,receipt}=candidates[0];
  await fs.writeFile(path.join(out,label+'-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  if(!['completed','findings'].includes(receipt.status)||receipt.checked<1||receipt.provider_responses<1)throw new Error(`${file}: incomplete ${receipt.status}`);
  const jsonStart=run.stdout.indexOf('{');
  const result=JSON.parse(run.stdout.slice(jsonStart));
  await fs.writeFile(path.join(out,label+'-result.json'),JSON.stringify(result,null,2)+'\n');
  runs.push({target:file,command:['npm',...args],wrapper_receipt:'.perch/usage/'+name,saved_receipt:`packages/vec/evidence/perch-parsed/${label}-receipt.json`,exit:run.status,checked:receipt.checked,responses:receipt.provider_responses,model:receipt.resolved_model});
  console.log(JSON.stringify({...runs.at(-1),findings:receipt.findings}));
}
await fs.writeFile(path.join(out,'runs.json'),JSON.stringify(runs,null,2)+'\n');
