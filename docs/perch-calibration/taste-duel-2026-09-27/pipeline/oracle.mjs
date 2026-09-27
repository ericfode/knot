// Independent oracle for task "pipeline" (Stop at the first error), written
// from the contract alone. No rendering code is used.
//
// Pinned interpretation, shared by every rendering:
//   stage 1 (lex):   chars 48..57 are digits, 44 is a comma, anything else is
//                    Err(1, position of that char). Maximal digit runs become
//                    number tokens (decimal, U32 wrapping); each comma becomes
//                    a separator token.
//   stage 2 (parse): tokens must be  number (comma number)*.  The first token
//                    whose kind breaks the alternation gives Err(2, its token
//                    index); a stream that ends while a number is expected
//                    (including the empty stream) gives Err(2, token count).
//                    So "" gives Err(2, 0).
//   stage 3 (check): numbers (0-based index k in the list of numbers) must be
//                    <= 1000 and strictly increasing; the first k with
//                    v_k > 1000 or v_k <= v_{k-1} gives Err(3, k).
//   success:         Ok(sum of the numbers), U32 wrapping.
//   The first failing stage wins: stage 1 runs over the whole input before
//   stage 2 is consulted, and so on.
// Encoding: Ok v -> (v * 4) mod 2^32; Err s p -> (p * 4 + s) mod 2^32.
// Harness: 15 fixed strings, each perturbed by n: m = n % 4, k = floor(n / 4);
//   m = 0 unchanged; otherwise insert one char at position min(k, length):
//   m = 1 the digit 48 + k % 10, m = 2 a comma (44), m = 3 the boundary char
//   47 ('/') when k is even, 58 (':') when k is odd.

export const BASE = [
  '1,2,3', '10,20,300', '', '1,,2', '5,3', '999,1000', '12a,3', '1,2000,',
  ',7', '4,8,15,16,23,42', '1001', '0,0', '1,,2x', '2000,1x', '2000,,1',
];

const u32 = x => ((x % 2 ** 32) + 2 ** 32) % 2 ** 32;

export function perturb(n, s) {
  const cs = [...s].map(ch => ch.charCodeAt(0));
  const m = n % 4, k = Math.floor(n / 4);
  if (m === 0) return cs;
  const c = m === 1 ? 48 + (k % 10) : m === 2 ? 44 : (k % 2 === 0 ? 47 : 58);
  cs.splice(Math.min(k, cs.length), 0, c);
  return cs;
}

export function pipeline(cs) {
  const isDigit = c => c >= 48 && c <= 57;
  // stage 1
  const tokens = [];
  for (let i = 0; i < cs.length;) {
    if (isDigit(cs[i])) {
      let v = 0;
      while (i < cs.length && isDigit(cs[i])) { v = u32(v * 10 + (cs[i] - 48)); i++; }
      tokens.push({kind: 'num', v});
    } else if (cs[i] === 44) {
      tokens.push({kind: 'sep'}); i++;
    } else {
      return {err: [1, i]};
    }
  }
  // stage 2
  for (let j = 0; j < tokens.length; j++) {
    const want = j % 2 === 0 ? 'num' : 'sep';
    if (tokens[j].kind !== want) return {err: [2, j]};
  }
  if (tokens.length % 2 === 0) return {err: [2, tokens.length]};
  // stage 3
  const nums = tokens.filter(t => t.kind === 'num').map(t => t.v);
  let sum = 0;
  for (let k = 0; k < nums.length; k++) {
    if (nums[k] > 1000 || (k > 0 && nums[k] <= nums[k - 1])) return {err: [3, k]};
    sum = u32(sum + nums[k]);
  }
  return {ok: sum};
}

export const encode = r => r.err ? u32(r.err[1] * 4 + r.err[0]) : u32(r.ok * 4);

export function scenario(n) {
  return BASE.map(s => encode(pipeline(perturb(n, s))));
}
