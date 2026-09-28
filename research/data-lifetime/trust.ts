// Inspect the seed closure and emitted effects; this is not a heap refinement proof.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as Bend from '../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';

const root = path.resolve(import.meta.dir, '../..');
const seed = fs.realpathSync(path.join(root, '.toolchain/bend-2.0.29-574b6d3/bend2'));
const hash = (p: string) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const relative = (p: string) => p.startsWith(seed + '/')
  ? '.toolchain/bend-2.0.29-574b6d3/bend2/' + path.relative(seed, p) : path.relative(root, p);
const entries = [];
for (const entry of ['research/data-lifetime/PROOF.bend', '.local/data-lifetime/baseline/entry.bend']) {
  const book = Bend.book_nil();
  const seen = new Map<string, string | null>();
  await Bend.book_load(book, path.join(root, entry), '', seen);
  Bend.book_valid(book);
  if (book.hols !== 0) throw new Error('Unfilled proof holes');
  const declarations = Object.entries(book.tlds) as [string, any][];
  const foreign = declarations.filter(([, t]) => t.$ === 'Def' && t.i?.length).map(([name]) => name);
  const unsafe = declarations.filter(([, t]) => t.$ === 'Def' && t.u).map(([name]) => name);
  if (foreign.length !== 42 || JSON.stringify(unsafe) !== JSON.stringify(['Array.fork', 'Array.join'])) {
    throw new Error('Pinned Base trust inventory changed');
  }
  entries.push({entry, holes: book.hols,
    files: [...seen.keys()].map(p => ({path: relative(p), sha256: hash(p)})),
    whole_checked_foreign: foreign, whole_checked_unsafe: unsafe});
}
const generated = path.join(root, '.local/data-lifetime/baseline/program.js');
const runtime = JSON.parse(fs.readFileSync(generated, 'utf8').match(/for \(const k of (\[[^\n]*\])\) \{/)![1]);
if (JSON.stringify(runtime) !== JSON.stringify(['IO.print'])) throw new Error('Unexpected generated effect');
const result = {schema: 1, seed_revision: '574b6d39a235b539eb19a5c532993a0abb3d11ad', entries,
  seed_files: ['main.ts', 'bend.ts', 'comp.ts', 'base.bend'].map(p => ({path: relative(path.join(seed, p)), sha256: hash(path.join(seed, p))})),
  generated_js_sha256: hash(generated), runtime_foreign: runtime,
  limits: 'Pure reusable ownership metadata with an affine Store wrapper, not a generic Type payload heap. Base checking/normalization, U32 lowering, native/JS runtimes and IO.print remain trusted. No Wasm/GPU lifetime execution or universal graph refinement.'};
fs.writeFileSync(path.join(root, 'research/data-lifetime/receipts/trust.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({entries: entries.length, holes: 0, foreign_per_entry: 42, unsafe_per_entry: 2, runtime}));
