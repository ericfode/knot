// Frozen before either author starts. Sparse population oracle, independent of candidates.
import assert from 'node:assert/strict';

export function advance(width, height, cells) {
  const live = new Set();
  for (let i = 0; i < cells.length; i++) if (cells[i]) live.add(i);
  const counts = new Map();
  for (const i of live) {
    const x = i % width, y = Math.floor(i / width);
    for (const dx of [-1, 0, 1]) for (const dy of [-1, 0, 1]) {
      if (dx === 0 && dy === 0) continue;
      const a = x + dx, b = y + dy;
      if (a < 0 || a >= width || b < 0 || b >= height) continue;
      const j = b * width + a;
      counts.set(j, (counts.get(j) || 0) + 1);
    }
  }
  return Array.from({length: width * height}, (_, i) =>
    Number(counts.get(i) === 3 || (live.has(i) && counts.get(i) === 2)));
}

export function evolve(width, height, cells, turns) {
  let out = cells.slice();
  for (let i = 0; i < turns; i++) out = advance(width, height, out);
  return out;
}

// A second, dense formulation checks the oracle before freezing the experiment.
function dense(width, height, cells) {
  return cells.map((alive, i) => {
    const x = i % width, y = Math.floor(i / width);
    let n = 0;
    for (let b = Math.max(0, y - 1); b <= Math.min(height - 1, y + 1); b++)
      for (let a = Math.max(0, x - 1); a <= Math.min(width - 1, x + 1); a++)
        if (a !== x || b !== y) n += cells[b * width + a];
    return Number(n === 3 || (alive === 1 && n === 2));
  });
}

const board = (w, h, positions) => {
  const out = Array(w * h).fill(0);
  for (const [x, y] of positions) out[y * w + x] = 1;
  return out;
};
const cases = [];
function add(id, width, height, cells, turns, native = false) {
  assert.equal(cells.length, width * height);
  assert(cells.every(x => x === 0 || x === 1));
  assert.deepEqual(advance(width, height, cells), dense(width, height, cells));
  cases.push({id, width, height, cells, turns,
    expected: evolve(width, height, cells, turns), native});
}
for (const [w, h] of [[0,0],[0,7],[7,0],[1,1],[1,5],[5,1],[2,2],[2,3],[3,2],[3,3]]) {
  for (let mask = 0; mask < 2 ** (w * h); mask++) {
    const cells = Array.from({length: w * h}, (_, i) => (mask >>> i) & 1);
    for (const turns of [1,2]) add('exhaustive-' + w + 'x' + h + '-' + mask + '-' + turns,
      w,h,cells,turns,w*h === 0 || (w*h <= 4 && mask === 2 ** (w*h)-1));
  }
}
const block = board(4,4,[[1,1],[2,1],[1,2],[2,2]]);
const blink = board(5,5,[[1,2],[2,2],[3,2]]);
const vertical = board(5,5,[[2,1],[2,2],[2,3]]);
const glider = board(8,8,[[2,1],[3,2],[1,3],[2,3],[3,3]]);
assert.deepEqual(advance(4,4,block),block);
assert.deepEqual(advance(5,5,blink),vertical);
assert.deepEqual(evolve(5,5,blink,2),blink);
assert.deepEqual(evolve(8,8,glider,4),board(8,8,[[3,2],[4,3],[2,4],[3,4],[4,4]]));
assert.deepEqual(advance(3,3,board(3,3,[[0,0],[1,0],[0,1]])),board(3,3,[[0,0],[1,0],[0,1],[1,1]]));
for (const t of [0,1,2,4,8]) {
  add('block-' + t,4,4,block,t,true);
  add('blinker-' + t,5,5,blink,t,true);
  add('glider-' + t,8,8,glider,t,true);
}
let seed = 0x6c696665;
for (const [w,h] of [[4,7],[7,4],[8,8],[12,12],[16,16],[32,32]]) {
  for (let sample = 0; sample < 3; sample++) {
    const cells = Array.from({length:w*h},() => {
      seed = (Math.imul(seed,1664525) + 1013904223) >>> 0;
      return Number((seed >>> 28) < 6);
    });
    for (const t of [0,1,4,8]) add('generated-' + w + 'x' + h + '-' + sample + '-' + t,
      w,h,cells,t,sample === 0 && w <= 8 && t === 4);
  }
}
export const fixtures = cases;
export const compositions = cases.filter(x => x.turns === 0).map(x => ({...x,a:3,b:4}));
export const nativeFixtures = cases.filter(x => x.native);
if (process.argv[1]?.endsWith('fixtures.mjs')) console.log(JSON.stringify({
  oracle_self_check:'passed',fixtures:cases.length,compositions:compositions.length,
  native:nativeFixtures.length,scope:'Finite independent fixtures; no candidate evaluated.'
}));
