// Inspect the pinned seed closure and generated host calls; no Knot semantics.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as Bend from '../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';

const root = path.resolve(import.meta.dir, '../..');
const hash = (p: string) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const relative = (p: string) => path.relative(root, p);
const entries = [];
for (const [source, output] of [
  ['src/fields-PROOF.bend', null],
  ['src/check-cli.bend', 'check.js'],
  ['src/eval-cli.bend', 'eval.js'],
  ['src/compile-cli.bend', 'compile.js'],
] as const) {
  const book = Bend.book_nil();
  const seen = new Map<string, string | null>();
  await Bend.book_load(book, path.join(root, source), '', seen);
  Bend.book_valid(book);
  if (book.hols !== 0) throw new Error('Unfilled proof holes');
  const declarations = Object.entries(book.tlds) as [string, any][];
  const js = output ? path.join(root, '.local/compiler-fields/gate', output) : null;
  const runtime = js ? JSON.parse(fs.readFileSync(js, 'utf8').match(/for \(const k of (\[[^\n]*\])\) \{/)![1]) : [];
  const expected = output ? ['IO.args', 'File.open', 'File.read', 'File.close',
    ...(output === 'compile.js' ? ['File.write_bytes', 'path-host.inspect', 'IO.print']
      : ['IO.print', 'path-host.inspect'])] : [];
  if (JSON.stringify(runtime) !== JSON.stringify(expected)) throw new Error('Host capability inventory changed');
  entries.push({entry: source, holes: book.hols,
    loaded_files: [...seen.keys()].map(p => ({path: relative(p), sha256: hash(p)})),
    whole_checked_foreign: declarations.filter(([, t]) => t.$ === 'Def' && t.i?.length)
      .map(([name, t]) => ({name, files: t.i.map((p: string) => ({path: relative(p), sha256: hash(p)}))})),
    whole_checked_unsafe: declarations.filter(([, t]) => t.$ === 'Def' && t.u).map(([name]) => name),
    runtime_foreign: runtime, generated_js_sha256: js ? hash(js) : null});
}
const seed = ['main.ts', 'bend.ts', 'comp.ts', 'base.bend'].map(p =>
  '.toolchain/bend-2.0.29-574b6d3/bend2/' + p);
const result = {date: new Date().toISOString(), seed_revision: '574b6d39a235b539eb19a5c532993a0abb3d11ad',
  inventory_script: {path: relative(import.meta.path), sha256: hash(import.meta.path)},
  seed_files: seed.map(p => ({path: p, sha256: hash(path.join(root, p))})), entries,
  limits: 'Seed checking, normalization, native primitive lowering and emitted runtime remain trusted. Generated foreign calls inventory host effects, not every native lowering. Persistent evaluator trees do not prove an owning heap. No Knot self-hosting or field/GPU code generation is established.'};
fs.writeFileSync(path.join(root, 'research/compiler-fields/receipts/trust.json'), JSON.stringify(result, null, 2) + '\n');
console.log(entries.map(e => ({entry: e.entry, files: e.loaded_files.length, holes: e.holes,
  foreign: e.whole_checked_foreign.length, unsafe: e.whole_checked_unsafe, runtime: e.runtime_foreign})));
