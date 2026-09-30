// Seed closure audit of the review helper proofs, not compiler refinement.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import * as Bend from '../../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts';

const root = path.resolve(import.meta.dir, '../../..');
const entry = 'tests/compiler-baseslice/review/PROOF.bend';
const book = Bend.book_nil();
const seen = new Map<string, string | null>();
await Bend.book_load(book, path.join(root, entry), '', seen);
Bend.book_valid(book);
if (book.hols !== 0) throw new Error('Unfilled proof holes');
const prefix = 'LAWS.';
const laws = Object.keys(book.tlds).filter(k => k.startsWith(prefix)).sort();
if (laws.length !== 7) throw new Error('Expected seven filled review laws');
if (laws.some(k => book.tlds[k].v === null || book.tlds[k].u)) throw new Error('A law is unfilled or unsafe');
const digest = (file: string) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const relative = (file: string) => file.includes('/bend2/')
  ? '.toolchain/bend-2.0.29-574b6d3/bend2/' + file.split('/bend2/').at(-1)
  : path.relative(root, file);
console.log(JSON.stringify({entry, holes: book.hols, laws,
  loaded_files: [...seen.keys()].map(file => ({path: relative(file), sha256: digest(file)})),
  loaded_unsafe: Object.entries(book.tlds).filter(([, t]: any) => t.$ === 'Def' && t.u).map(([k]) => k).sort(),
  loaded_foreign: Object.entries(book.tlds).filter(([, t]: any) => t.$ === 'Def' && t.i?.length).map(([k]) => k).sort(),
  limit: 'Five universal helper laws and two ground spelling equations; no compiler-refinement theorem. Whole loaded Base unsafe/foreign inventory is not runtime reach.'}));
