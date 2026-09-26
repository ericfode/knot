import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import * as Bend from "../../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts";

const dir = path.resolve(import.meta.dir,"..");
const seed = path.resolve(dir,"../../.toolchain/bend-2.0.29-574b6d3/bend2");
const cli = fs.readFileSync(path.join(seed,"main.ts"),"utf8");
const sha = (s: string) => crypto.createHash("sha256").update(s).digest("hex");
// Execute the exact pinned publisher closure function, not a hand-maintained approximation.
const start = cli.indexOf("function pkg_files(");
const end = cli.indexOf("\nfunction sha256",start);
const fn = cli.slice(start,end);
const js = new Bun.Transpiler({loader:"ts"}).transformSync(fn);
const pkgFiles = new Function("fs","path","BASE",js+"\nreturn pkg_files;")(fs,path,fs.realpathSync(Bend.BASE_BEND));
const seen = new Map<string,string|null>();
const book = Bend.book_nil();
const entry = path.join(dir,"release.bend");
await Bend.book_load(book,entry,"",seen);
Bend.book_valid(book);
if (book.hols !== 0) throw new Error(`Unresolved holes: ${book.hols}`);
const files = pkgFiles(entry,book,seen) as Record<string,string>;
const paths = Object.keys(files).sort();
const expected = "0x"+sha(paths.map(p=>sha(files[p])+" "+p+"\n").join("")).slice(0,32);
if (!paths.includes("PROOF.bend") || !paths.includes("LAWS.bend") || !paths.includes("BYTE_PROOF.bend") || !paths.includes("LICENSE")) throw new Error("Missing proof/license closure");
if (paths.some(p=>p.includes("/") || (!p.endsWith(".bend") && p!=="LICENSE"))) throw new Error("Unexpected release path");
const unsafe:string[] = [];
const foreign:string[] = [];
for (const [name,tld] of Object.entries(book.tlds)) {
  if (tld.$ === "Def") {
    if (tld.u) unsafe.push(name);
    if (tld.i) foreign.push(name);
  }
}
const evidence = {reference:"2.0.29",revision:"574b6d39a235b539eb19a5c532993a0abb3d11ad",holes:book.hols,
  pkg_files_function_sha256:sha(fn),expected_hash:expected,license:"MIT-0",bytes:paths.reduce((n,p)=>n+Buffer.byteLength(files[p]),0),
  closure:paths.map(p=>({path:p,sha256:sha(files[p]),bytes:Buffer.byteLength(files[p])})),
  trust:{loaded_unsafe:unsafe.sort(),loaded_foreign:foreign.sort(),note:"Entire loaded Base inventory; these entries are not all reachable from the package core. No package-owned unsafe or foreign definitions."}};
fs.writeFileSync(path.join(dir,"evidence/closure.json"),JSON.stringify(evidence,null,2)+"\n");
fs.writeFileSync(path.join(dir,"build/upload-files.json"),JSON.stringify(files,null,2)+"\n");
console.log(JSON.stringify({holes:book.hols,expected_hash:expected,paths,unsafe:unsafe.length,foreign:foreign.length}));
