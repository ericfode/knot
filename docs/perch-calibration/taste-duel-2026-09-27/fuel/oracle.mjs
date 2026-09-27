// Independent oracle for task "fuel", written from the contract alone.
//
// A task is (remaining, total), both U32. One step, taken only while
// remaining > 0, costs one unit of fuel and sets
//   total     := total * 3 + (remaining mod 7)   (wrapping U32)
//   remaining := remaining - 1
// A task whose remaining is 0 is finished: it is Done(total), whether or not
// fuel is left. Otherwise, when fuel runs out, the task is handed back as
// Owed(task) (so an Owed task always has remaining > 0).
//
// Encoding: Done v -> v*2+1 (wrapping U32); Owed task -> remaining*2.
// For each split (a, b) the harness reports run(a+b, t) then run(b, run(a, t)).

export const SPLITS = [
  [0, 0], [0, 1], [1, 0], [2, 3], [5, 8], [13, 21],
  [20, 19], [34, 6], [39, 1], [40, 0], [3, 50], [17, 17],
];

const u32 = x => x >>> 0;

function run(fuel, o) {
  let f = fuel;
  let cur = o;
  for (;;) {
    if (cur.done) return cur;
    if (cur.remaining === 0) return {done: true, total: cur.total};
    if (f === 0) return cur;
    f -= 1;
    cur = {
      done: false,
      remaining: cur.remaining - 1,
      total: u32(Math.imul(cur.total, 3) + (cur.remaining % 7)),
    };
  }
}

function encode(o) {
  return o.done ? u32(Math.imul(o.total, 2) + 1) : u32(o.remaining * 2);
}

export function scenario(n) {
  const start = () => ({done: false, remaining: n % 40, total: u32(n)});
  const out = [];
  for (const [a, b] of SPLITS) {
    const direct = encode(run(a + b, start()));
    const composed = encode(run(b, run(a, start())));
    if (direct !== composed) throw new Error(`oracle law failure n=${n} a=${a} b=${b}`);
    out.push(direct, composed);
  }
  return out;
}
