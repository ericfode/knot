// Encode an arbitrarily long input of u16 words, returning their LE bytes.
export function encode(words) {
  let output = new Uint8Array(0);
  for (const word of words) {
    const next = new Uint8Array(output.length + 2);
    next.set(output);
    next[output.length] = word & 255;
    next[output.length + 1] = word >>> 8;
    output = next;
  }
  return output;
}
