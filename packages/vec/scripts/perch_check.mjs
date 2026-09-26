// Expose exact installed Perch rule-selection/packet-sizing functions locally.
// No provider call is mocked; this is explicitly deterministic coverage only.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const pkg=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const root=path.resolve(pkg,'../..');
const input=path.join(root,'node_modules/@lakeday/perch/dist/cli.mjs');
const tmp=path.join(pkg,'build/perch_internals.mjs');
fs.writeFileSync(tmp,fs.readFileSync(input,'utf8').replaceAll('import.meta.url',JSON.stringify(pathToFileURL(input).href))+'\nexport {readRules,rulesFor,unitSteps};\n');
const p=await import(pathToFileURL(tmp));
const rules=await p.readRules(root);
const names=['law-domain-inhabited','law-observable-essence','law-public-contract-coverage','law-independent-model','law-state-composition','law-boundaries-and-exhaustion','law-mutation-sensitivity','law-proof-claim-integrity','vec-logical-state-observation'];
const targets=['packages/vec/LAW_REVIEW.md',...['clean','broken','heldout'].map(x=>`packages/vec/tests/perch/${x}/LAW_REVIEW.md`)];
const coverage=targets.map(target=>{
 const text=fs.readFileSync(path.join(root,target),'utf8');
 const unit={path:target,name:target,line:1};
 const selected=p.rulesFor(rules,unit,names);
 const steps=p.unitSteps({rules:selected,unit,source:text});
 if(!selected.length||steps.length!==1)throw new Error('Missing coverage or split packet: '+target);
 return {target,selected_rules:selected.map(x=>x.name),selected_count:selected.length,complete_packet:steps.length===1,sha256:crypto.createHash('sha256').update(text).digest('hex')};
});
const live=spawnSync(path.join(root,'node_modules/.bin/perch'),['check',targets[0],'--rules',names.join(','),'--json'],{cwd:root,encoding:'utf8'});
const receipt={deterministic_coverage:coverage,live_attempt:{exit:live.status,stdout:live.stdout,stderr:live.stderr},calibration:'No clean/broken/held-out live separation claimed unless actual provider results are recorded.'};
fs.writeFileSync(path.join(pkg,'receipts/perch.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt));
