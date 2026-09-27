// Independent oracle for task "bitpath", written from the contract alone.
// An ordinary Map models the observable map. The fork census is derived from
// the trie shape the contract fixes: depth exactly 8, key bits read low-first,
// and no branch left with two empty children. A branch then exists at depth d
// (0..7) exactly for each distinct low-d-bit prefix of a surviving key.
export function forks(keys) {
  const ks = [...keys];
  if (ks.length === 0) return 0;
  let total = 0;
  for (let d = 0; d < 8; d++) total += new Set(ks.map(k => k % 2 ** d)).size;
  return total;
}

export function scenario(n) {
  const key = i => (n * 37 + i * 11) % 256;
  const flip = k => (k + 128) % 256;          // shares the first seven bits walked
  const k = Array.from({length: 8}, (_, i) => key(i));
  const v = n + 5;
  const m = new Map();
  const w = (n * 7 + 3) % 256;                      // a wanderer; may collide
  for (let i = 0; i < 8; i++) m.set(k[i], v * i);   // k0 holds the value 0
  m.set(w, n);
  m.set(k[3], n + 100);                             // overwrite
  m.set(flip(k[0]), 7);                             // sibling at the deepest bit
  const c1 = forks(m.keys());
  m.delete(k[1]);
  m.delete(k[4]);
  m.delete(flip(k[0]));                             // leaves a one-sided fork
  m.delete(flip(k[2]));                             // absent, deep path
  m.delete(k[1]);                                   // absent again
  const c2 = forks(m.keys());
  const probes = [...k, flip(k[0]), flip(k[2]), w, key(8)];
  const seen = probes.map(p => (m.has(p) ? m.get(p) + 1 : 0));
  for (const x of [k[0], k[2], k[3], k[5], k[6], k[7], w]) m.delete(x);
  const c3 = forks(m.keys());                        // every fork must collapse
  return [...seen, c1, c2, c3];
}
