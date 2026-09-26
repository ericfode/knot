// Inspect the pinned seed's loaded closure; this is not Knot source semantics.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as Bend from '../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';

const root = path.resolve(import.meta.dir, '../..');
const hash = (p: string) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const relative = (p: string) => path.relative(root, p);
const entries = [];
for (const source of ['src/catalog-PROOF.bend', 'tests/compiler-structural/observe.bend']) {
  const book = Bend.book_nil();
  const seen = new Map<string, string | null>();
  await Bend.book_load(book, path.join(root, source), '', seen);
  Bend.book_valid(book);
  if (book.hols !== 0) throw new Error('Unfilled proof holes');
  const declarations = Object.entries(book.tlds) as [string, any][];
  entries.push({entry: source, holes: book.hols,
    loaded_files: [...seen.keys()].map(p => ({path: relative(p), sha256: hash(p)})),
    whole_checked_foreign: declarations.filter(([, t]) => t.$ === 'Def' && t.i?.length)
      .map(([name, t]) => ({name, files: t.i.map((p: string) => ({path: relative(p), sha256: hash(p)}))})),
    whole_checked_unsafe: declarations.filter(([, t]) => t.$ === 'Def' && t.u).map(([name]) => name)});
}
const js = path.join(root, '.local/compiler-structural/gate/catalog.js');
const foreign = JSON.parse(fs.readFileSync(js, 'utf8').match(/for \(const k of (\[[^\n]*\])\) \{/)![1]);
const expected = ['IO.args', 'File.open', 'File.read', 'File.close', 'IO.print'];
if (JSON.stringify(foreign) !== JSON.stringify(expected)) throw new Error('Observer host capabilities changed');
const seedFiles = ['main.ts', 'bend.ts', 'comp.ts', 'base.bend'].map(p =>
  '.toolchain/bend-2.0.29-574b6d3/bend2/' + p);
const result = {date: new Date().toISOString(),
  seed_revision: '574b6d39a235b539eb19a5c532993a0abb3d11ad', entries,
  seed_files: seedFiles.map(p => ({path: p, sha256: hash(path.join(root, p))})),
  observer_generated_js_sha256: hash(js), observer_runtime_foreign: foreign,
  limits: 'Seed checking, normalization, native primitive lowering and emitted runtime remain trusted. The foreign list inventories host effects, not every primitive lowering. No Knot self-hosting or GPU execution is established.'};
fs.writeFileSync(path.join(root, 'research/compiler-structural/receipts/trust.json'), JSON.stringify(result, null, 2) + '\n');
console.log(entries.map(e => ({entry: e.entry, files: e.loaded_files.length,
  foreign: e.whole_checked_foreign.length, unsafe: e.whole_checked_unsafe})), foreign);
