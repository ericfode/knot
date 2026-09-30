// Read-only source analysis of a Git snapshot through the pinned census parser.
// Writes only the plan inventory in the invoking worktree; no compiler semantics.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Inventory,closure,intrinsicOperations,wordRepresentations,packageCatalog,sha256} from '../../tools/census/census.mjs';
const arg = process.argv[2];
if (!arg?.startsWith('--ref=')) throw new Error('Usage: node tests/compiler-baseslice/plan-inventory.mjs --ref=<commit>');
const ref = execFileSync('git', ['rev-parse', '--verify', arg.slice(6) + '^{commit}'], {encoding:'utf8'}).trim();
const show=p=>execFileSync('git',['show',`${ref}:${p}`],{encoding:'utf8'});
const paths=execFileSync('git',['ls-tree','-r','--name-only',ref,'src/'],{encoding:'utf8'}).trim().split('\n').filter(f=>/^src\/[^/]+\.bend$/.test(f));
const sources=new Map(paths.map(p=>[p,show(p)]));
const packages=packageCatalog(process.cwd());
if (show('packages/releases.json') !== fs.readFileSync('packages/releases.json','utf8')) throw new Error('Published package pins differ from the snapshot');
for (const p of packages) if (sha256(show(p.release_record)) !== p.release_record_sha256) throw new Error('Release record differs from the snapshot: '+p.name);
const inv=new Inventory({root:process.cwd(),packages});
const get=inv.source.bind(inv);
inv.source=file=>sources.has(file)?sources.get(file):get(file);
for(const p of paths) inv.load(p);
const files=inv.manifest(), declarations=files.flatMap(f=>f.declarations);
const comp=fs.readFileSync('.toolchain/bend-2.0.29-574b6d3/bend2/comp.ts','utf8');
const operations=intrinsicOperations(comp),words=wordRepresentations(comp);
const roots={frontend:['src/lex.tokenize','src/parse.parse'],compiler:['src/compile-cli.main'],all_src:[...new Set(declarations.filter(d=>d.id.startsWith('src/')).map(d=>d.key))].sort()};
const sets=Object.fromEntries(Object.entries(roots).map(([name,roots])=>[name,Object.fromEntries([['js','runtime','js'],['native','runtime','native'],['static','static','js']].map(([lane,mode,target])=>[lane,closure(roots,declarations,inv.book,operations,mode,target,words)]))]));
for(const v of Object.values(sets))for(const s of Object.values(v))if(s.unresolved.length)throw new Error(JSON.stringify(s.unresolved));
const owners=new Map(Object.entries(inv.book.tlds).flatMap(([k,t])=>t.$==='ADT'?t.c.map(c=>[c.k,k]):[]));
const base=files.find(f=>f.file==='Base');
const data=fs.readFileSync('.toolchain/bend-2.0.29-574b6d3/bend2/base.bend','utf8');
if (data !== get('Base')) throw new Error('Seed and parser Base differ');
const lines=data.split('\n');
const keys=new Set(sets.all_src.static.entries.filter(e=>e.file==='Base').map(e=>e.key));
const entries=[...keys].sort().map(name=>{
 const ds=base.declarations.filter(d=>d.key===name),d=ds[0];
 const text=ds.map(d=>lines.slice(d.lines[0]-1,d.lines[1]).join('\n')+'\n').join('\n');
 const via={};for(const [r,v]of Object.entries(sets))for(const [lane,s]of Object.entries(v)){const e=s.entries.find(e=>e.key===name);if(e)via[`${r}/${lane}`]={boundary:e.boundary,dependencies:e.dependencies,via:e.via};}
 return {name,kind:inv.book.tlds[name].$,lines:ds.map(d=>d.lines),signature:lines[d.lines[0]-1],source_sha256:sha256(text),features:[...new Set(ds.flatMap(d=>d.features))].sort(),direct_users:declarations.filter(d=>d.id.startsWith('src/')&&d.references.some(r=>(owners.get(r)??r)===name)).map(d=>d.key).sort(),reach:via};
});
const record={schema:1,source_ref:ref,seed:{version:'2.0.29',commit:'574b6d39a235b539eb19a5c532993a0abb3d11ad',base_sha256:sha256(data),comp_sha256:sha256(comp)},analysis_files:Object.fromEntries(['tests/compiler-baseslice/plan-inventory.mjs','tools/census/census.mjs','tools/census/features.mjs','vendor/bend-parser/bend.mts','scripts/perch-bend.mjs'].map(p=>[p,sha256(fs.readFileSync(p,'utf8'))])),parser_typechecked:false,package_pins:packages.map(p=>({name:p.name,hash:p.hash,release_record:p.release_record,release_record_sha256:p.release_record_sha256})),source_files:Object.fromEntries(paths.map(p=>[p,sha256(sources.get(p))])),method:'Pinned-parser structural upper bound; source and signature closure, not an execution trace. Runtime closure cuts seed-native primitives and foreign leaves.',counts:Object.fromEntries(Object.entries(sets).map(([n,s])=>[n,Object.fromEntries(Object.entries(s).map(([l,e])=>[l,{...e.totals,unresolved:e.unresolved.length}]))])),entries};
fs.writeFileSync('docs/compiler-campaign/BASE-SLICE-INVENTORY.json',JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(record.counts,null,2));
