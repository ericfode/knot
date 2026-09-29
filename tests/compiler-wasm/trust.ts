// Inventory the pinned seed's actual load/check closure, not Knot semantics.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as Bend from '../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';
const root=path.resolve(import.meta.dir,'../..');
const digest=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const relative=(p:string)=>p.startsWith(root+'/')?path.relative(root,p):p;
const entries=[];
for (const source of ['compile-cli.bend','eval-cli.bend','runtime-PROOF.bend']) {
  const book=Bend.book_nil();const seen=new Map<string,string|null>();
  await Bend.book_load(book,path.join(root,'src',source),'',seen);
  Bend.book_valid(book);if(book.hols!==0)throw new Error('Unfilled proof holes');
  const foreign=Object.entries(book.tlds).filter(([k,t]:any)=>t.$==='Def' && t.i?.length);
  const unsafe=Object.entries(book.tlds).filter(([k,t]:any)=>t.$==='Def' && t.u).map(([name])=>name);
  const generated=source==='runtime-PROOF.bend'?null:path.join(root,'.local/compiler-wasm/gate',source.replace('.bend','.js'));
  const runtime=generated?JSON.parse(fs.readFileSync(generated,'utf8').match(/for \(const k of (\[[^\n]*\])\) \{/)[1]):[];
  const allowed=['IO.args','File.open','File.read','File.close','File.write_bytes','path-host.inspect','IO.print'];
  if(runtime.some((x:string)=>!allowed.includes(x)))throw new Error('Unexpected runtime foreign capability');
  const compiled_foreign=foreign.filter(([k])=>runtime.includes(k)).map(([name,t]:any)=>({name,files:t.i.map((p:string)=>({path:relative(p),sha256:digest(p)}))}));
  entries.push({entry:'src/'+source,holes:book.hols,loaded_files:[...seen.keys()].map(p=>({path:relative(p),sha256:digest(p)})),whole_checked_foreign_count:foreign.length,whole_checked_foreign:foreign.map(([name,t]:any)=>({name,files:t.i.map((p:string)=>({path:relative(p),sha256:digest(p)}))})),whole_checked_unsafe:unsafe,compiled_foreign,compiled_runtime_foreign_names:runtime,generated_js_sha256:generated?digest(generated):null});
}
const toolchain=['main.ts','bend.ts','comp.ts','base.bend'].map(p=>({path:'.toolchain/bend-2.0.29-574b6d3/bend2/'+p,sha256:digest(path.join(root,'.toolchain/bend-2.0.29-574b6d3/bend2',p))}));
const output={date:new Date().toISOString(),seed_revision:'574b6d39a235b539eb19a5c532993a0abb3d11ad',toolchain,entries,limits:'Generated foreign-effect list is read from seed JS emission. It does not inventory every native primitive lowering or prove seed/host correctness. Full pinned comp.ts and its emitted runtime remain trusted.'};
fs.writeFileSync(path.join(root,'research/compiler-wasm/receipts/trust.json'),JSON.stringify(output,null,2)+'\n');
console.log(entries.map(x=>({entry:x.entry,files:x.loaded_files.length,foreign:x.whole_checked_foreign_count,unsafe:x.whole_checked_unsafe,runtime:x.compiled_runtime_foreign_names})));
