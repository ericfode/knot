// Appendable byte storage; arbitrary streams must have amortized O(1) append.
export class Bytes {
  data = new Uint8Array(0);
  length = 0;
  append(value) {
    if (this.length === this.data.length) {
      const next = new Uint8Array(this.length + 1);
      next.set(this.data);
      this.data = next;
    }
    this.data[this.length++] = value;
  }
}
