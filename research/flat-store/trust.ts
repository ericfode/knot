// Inventory seed dependencies, proof holes and emitted host calls. No store semantics.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as Bend from '../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';

const root=path.resolve(import.meta.dir,'../..');
const hash=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const relative=(p:string)=>path.relative(root,p);
const entries=[];
for(const [source,output] of [
  ['research/flat-store/PROOF.bend',null],
  ['research/flat-store/emit-cli.bend','.local/flat-store/emitter.js'],
  ['.local/flat-store/oracle-entry.bend','.local/flat-store/oracle.js'],
  ['research/flat-store/probes.bend','.local/flat-store/probes.js'],
] as const) {
  const book=Bend.book_nil(),seen=new Map<string,string|null>();
  await Bend.book_load(book,path.join(root,source),'',seen);
  Bend.book_valid(book);
  if(book.hols!==0)throw new Error('Unfilled proof holes');
  const declarations=Object.entries(book.tlds) as [string,any][];
  const js=output?path.join(root,output):null;
  const runtime=js?JSON.parse(fs.readFileSync(js,'utf8').match(/for \(const k of (\[[^\n]*\])\) \{/)![1]):[];
  if(JSON.stringify(runtime)!==JSON.stringify(output?['IO.print']:[]))throw new Error('Host capability inventory changed');
  entries.push({entry:source,holes:book.hols,
    loaded_files:[...seen.keys()].map(p=>({path:relative(p),sha256:hash(p)})),
    whole_checked_foreign:declarations.filter(([,t])=>t.$==='Def'&&t.i?.length)
      .map(([name,t])=>({name,files:t.i.map((p:string)=>({path:relative(p),sha256:hash(p)}))})),
    whole_checked_unsafe:declarations.filter(([,t])=>t.$==='Def'&&t.u).map(([name])=>name),
    runtime_foreign:runtime,generated_js_sha256:js?hash(js):null});
}
const seed=['main.ts','bend.ts','comp.ts','base.bend'].map(p=>'.toolchain/bend-2.0.29-574b6d3/bend2/'+p);
const result={date:new Date().toISOString(),seed_revision:'574b6d39a235b539eb19a5c532993a0abb3d11ad',
  inventory_script:{path:relative(import.meta.path),sha256:hash(import.meta.path)},
  seed_files:seed.map(p=>({path:p,sha256:hash(path.join(root,p))})),entries,
  limits:'The seed checker, normalization, native primitives and seed-generated emitter/oracle remain trusted. Foreign calls inventory host effects, not all native lowering. The emitted Wasm has no imports; its engine and privileged exported-memory host remain trusted. Fifteen filled laws cover codecs, address boundaries and encoding, not a universal Wasm transition refinement. Word payloads do not establish general Type graph reclamation, shared Data lifetime, self-hosting or generated GPU execution.'};
fs.writeFileSync(path.join(root,'research/flat-store/receipts/trust.json'),JSON.stringify(result,null,2)+'\n');
console.log(entries.map(e=>({entry:e.entry,files:e.loaded_files.length,holes:e.holes,foreign:e.whole_checked_foreign.length,unsafe:e.whole_checked_unsafe,runtime:e.runtime_foreign})));
