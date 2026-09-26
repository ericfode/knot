// Uses the installed Perch selectors without a provider request to establish
// nonzero rule eligibility; live results are recorded separately and honestly.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
const root=path.resolve(import.meta.dirname,'../../..');
const pkg=path.join(root,'packages/int_map');
const bin=path.join(root,'node_modules/@lakeday/perch/bin/perch.mjs');
const src=fs.readFileSync(path.join(root,'node_modules/@lakeday/perch/dist/cli.mjs'),'utf8');
const selectors=src.slice(src.indexOf('function expand2(glob)'),src.indexOf('function selectUnits('))+src.slice(src.indexOf('function rulesFor(rules, unit'),src.indexOf('var brokenHere ='));
const select=new Function(selectors+'\nreturn rulesFor;')();
const listed=spawnSync('node',[bin,'rules','list','--json'],{cwd:root,encoding:'utf8'});
if(listed.status!==0) throw Error(listed.stderr);
const rules=JSON.parse(listed.stdout).filter(r=>r.name.startsWith('law-')||r.name==='package-int-map-union-observation');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const targets=['packages/int_map/LAW_REVIEW.md',...['clean','broken','held_out'].map(c=>`packages/int_map/tests/perch/${c}/LAW_REVIEW.md`)];
const attempts=targets.map(target=>{
 const only=target===targets[0]?rules.map(r=>r.name):['package-int-map-union-observation'];
 const selected=select(rules,{path:target,part:false},only).map(r=>r.name);
 if(selected.length!==(target===targets[0]?9:1)) throw Error('unexpected rule coverage '+target);
 const live=spawnSync('node',[bin,'check',target,'--rules',only.join(','),'--json'],{cwd:root,encoding:'utf8'});
 return {target,sha256:sha(fs.readFileSync(path.join(root,target))),selected_rules:selected,eligible_rule_count:selected.length,live_exit:live.status,live_stdout:live.stdout,live_stderr:live.stderr};
});
fs.mkdirSync(path.join(pkg,'receipts'),{recursive:true});
fs.writeFileSync(path.join(pkg,'receipts/perch.json'),JSON.stringify({version:'0.3.5',selector_sha256:sha(selectors),rules,attempts,calibration:'unavailable: PERCH_API_KEY not set; no probabilities; no model pass',completed_model_requests:0},null,2)+'\n');
console.log(JSON.stringify(attempts.map(a=>({target:a.target,eligible_rules:a.eligible_rule_count,live_exit:a.live_exit,error:a.live_stderr.trim()}))));
