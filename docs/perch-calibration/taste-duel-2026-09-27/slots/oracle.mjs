// Independent oracle for task "slots" (Refusal returns the offer), written from
// the contract alone. No Bend code is consulted.
//
// Store: 4 slots, each empty or holding a U32.
//   put(v):  lowest empty slot i gets v -> Placed(i)   encoded i + 1
//            no empty slot, store unchanged -> Refused(v)  encoded 100 + v % 50
//   take(i): slot i (0..3) full -> Taken(v), slot emptied  encoded 200 + v % 50
//            otherwise (empty slot or i >= 4) -> Missing   encoded 999
//
// Scenario(n), values v(k) = n*7 + k*13 + 3 (U32):
//   put v0, put v1, take n%4, put v2, put v3, put v4, put v5,
//   take (n/4)%4, take (n/4)%4, put v6, take (n/16)%4, take n%6,
//   put v7, put v8
const u32 = x => x >>> 0;

export function scenario(n) {
  const slots = [null, null, null, null];
  const out = [];
  const v = k => u32(n * 7 + k * 13 + 3);
  const put = x => {
    const i = slots.findIndex(s => s === null);
    if (i < 0) out.push(100 + x % 50);
    else { slots[i] = x; out.push(i + 1); }
  };
  const take = i => {
    if (i < 4 && slots[i] !== null) { out.push(200 + slots[i] % 50); slots[i] = null; }
    else out.push(999);
  };
  const q = Math.floor;
  put(v(0)); put(v(1)); take(n % 4);
  put(v(2)); put(v(3)); put(v(4)); put(v(5));
  take(q(n / 4) % 4); take(q(n / 4) % 4); put(v(6));
  take(q(n / 16) % 4); take(n % 6);
  put(v(7)); put(v(8));
  return out;
}
