// Executes the exact pinned CLI pkg_files function; no copied upstream code is
// redistributed. This script orchestrates loading and hashes, not Vec semantics.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as B from '../../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';
const root=path.resolve(import.meta.dir,'../../..');
const pkg=path.join(root,'packages/vec');
const entry=path.join(pkg,'release.bend');
const main=fs.readFileSync(path.join(root,'.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'),'utf8');
const source=main.slice(main.indexOf('function pkg_files('),main.indexOf('\nfunction sha256(',main.indexOf('function pkg_files(')));
if(!source.endsWith('}\n')) throw new Error('Unexpected pinned function boundary');
const code=new Bun.Transpiler({loader:'ts'}).transformSync(source);
const pkgFiles=new Function('fs','path','BASE',code+'\nreturn pkg_files;')(fs,path,B.BASE_BEND);
const book=B.book_nil();const seen=new Map<string,string|null>();
await B.book_load(book,entry,'',seen);B.book_valid(book);
if(book.hols!==0) throw new Error('Open proof holes: '+book.hols);
const files: Record<string,string>=pkgFiles(entry,book,seen);
const sha=(s:string)=>crypto.createHash('sha256').update(s).digest('hex');
const names=Object.keys(files).sort();
const expected='0x'+sha(names.map(n=>sha(files[n])+' '+n+'\n').join('')).slice(0,32);
const allowed=['release.bend','main.bend','model.bend','trace.bend','observations.bend','LAWS.bend','PROOF.bend','witnesses.bend','conformance.bend','benchmark.bend','example.bend','generic.bend','LICENSE'].sort();
if(JSON.stringify(names)!==JSON.stringify(allowed)) throw new Error('Unexpected upload closure: '+names.join(','));
if(!files.LICENSE.startsWith('SPDX-License-Identifier: MIT-0')) throw new Error('Wrong license');
const inventory=Object.entries(book.tlds).filter(([,v])=>v.$==='Def').map(([name,v])=>({name,base:v.b===true,unsafe:v.u===true,foreign:v.i??[],body:v.v!==null}));
const reachable=new Set<string>();
function visitTerm(term:any) {
  if(!term || typeof term!=='object') return;
  if(['Ref','ADT'].includes(term.$)) visitName(term.k);
  if(term.$==='Ctr' && book.ctrs[term.k]) visitTerm(B.term_lower(book.ctrs[term.k].T));
  for(const [k,v] of Object.entries(term)) if(k!=='s') {
    if(Array.isArray(v)) v.forEach(visitTerm); else if(v && typeof v==='object') visitTerm(v);
  }
}
function visitName(name:string) {
  if(reachable.has(name))return;const t=book.tlds[name];if(!t)return;
  reachable.add(name);visitTerm(B.term_lower(t.T));
  if(t.$==='Def' && t.v)visitTerm(B.term_lower(t.v));
  if(t.$==='ADT')t.c.forEach(c=>visitTerm(B.term_lower(c.T)));
}
for(const [name,v] of Object.entries(book.tlds)) if(!v.b)visitName(name);
const receipt={compiler:'Bend 2.0.29',revision:'574b6d39a235b539eb19a5c532993a0abb3d11ad',entry:'release.bend',expected_hash:expected,bytes:names.reduce((n,p)=>n+Buffer.byteLength(files[p]),0),files:names.map(name=>({name,sha256:sha(files[name]),bytes:Buffer.byteLength(files[name])})),holes:book.hols,license:'MIT-0',dependency_packages:[],license_review:'Original package code only; imported Base is supplied by pinned compiler and excluded by pkg_files. No incorporated third-party source.',loaded_unsafe:inventory.filter(i=>i.unsafe),loaded_foreign:inventory.filter(i=>i.foreign.length),reachable_unsafe:inventory.filter(i=>reachable.has(i.name)&&i.unsafe),reachable_foreign:inventory.filter(i=>reachable.has(i.name)&&i.foreign.length),reachable_bodiless:inventory.filter(i=>reachable.has(i.name)&&!i.body),static_reachable:[...reachable].sort(),pkg_files_function_sha256:sha(source)};
fs.writeFileSync(path.join(pkg,'receipts/closure.json'),JSON.stringify(receipt,null,2)+'\n');
fs.writeFileSync(path.join(pkg,'build/upload-files.json'),JSON.stringify(files,null,2)+'\n');
console.log(JSON.stringify({expected_hash:expected,files:names,bytes:receipt.bytes,holes:book.hols,reachable_unsafe:receipt.reachable_unsafe,reachable_foreign:receipt.reachable_foreign,reachable_bodiless:receipt.reachable_bodiless}));
