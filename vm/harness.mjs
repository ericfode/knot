#!/usr/bin/env node
// Test harness for knot-vm-1: an in-memory knot_io host for the imports the VM
// uses, mirroring scripts/run-wasm-io.mjs's observable conventions (stdout,
// stderr, exit and the `Exhausted<TAB>io<TAB>kind` line). With the test build
// it also steps the machine and reads its state. The gate uses it for batches;
// acceptance runs of the production module go through the real host.
//
// Batch mode: a JSON array of jobs on stdin, one JSON result per line.
//   {id, wasm, files: {name: path}, argv, limits?: {frames, heap}, trace?: 'yields' | 'audit'}
// A traced result says whether vm_boot returned (`booted`): an image refusal
// happens before, a run-time failure after.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

class Stop extends Error {
  constructor(status, exit) { super(status); Object.assign(this, {status, exit}); }
}

// `bump` and `HL` are 64-bit (a heap may end exactly at 4 GiB): their high words follow.
const REGISTERS = ['mode', 'node', 'val', 'tgt', 'tfn', 'ops', 'nops', 'act', 'top', 'F0', 'FL', 'H0', 'bump',
  'fuel', 'calls', 'quantum', 'outcome', 'kind', 'cause', 'W', 'terminal', 'yields', 'HL', 'bump_high', 'HL_high',
  'grows'];
const OUTCOMES = [null, 'Completed', 'Halted', 'HostFailure', 'Unsupported', 'Exhausted', 'InternalFailure'];
const strict = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});

export function registers(x) {
  const at = x.vm_dump(), v = new DataView(x.memory.buffer);
  const r = Object.fromEntries(REGISTERS.map((k, i) => [k, v.getUint32(at + 4 * i, true)]));
  for (const k of ['bump', 'HL']) {
    r[k] += 2 ** 32 * r[`${k}_high`];
    delete r[`${k}_high`];
  }
  const bytes = new Uint8Array(x.memory.buffer);
  let end = r.cause;
  while (r.cause && bytes[end]) end++;
  r.cause = r.cause ? Buffer.from(bytes.subarray(r.cause, end)).toString() : null;
  r.outcome = OUTCOMES[r.outcome];
  return r;
}

// Structural audit of a state (SPEC section 5-6 layouts): the frame records chain
// exactly down to F0, the cells tile [H0, bump), and every word held by a frame,
// the result register or a cell's owning edges is zero, an immediate, or the
// address of a cell start.
export function audit(x) {
  const r = registers(x), v = new DataView(x.memory.buffer), u = at => v.getUint32(at, true);
  const cells = new Map();
  for (let p = r.H0; p < r.bump;) {
    const hdr = u(p + 4), payload = hdr >>> 3, cls = hdr & 7;
    if (cls > 4) return `class ${cls} at ${p}`;
    const size = 4 * Math.max(4, 2 ** Math.ceil(Math.log2(payload + 2)));
    cells.set(p, {cls, payload});
    p += size;
    if (p > r.bump) return `cell at ${p - size} overruns the bump`;
  }
  const word = (w, where) => (w === 0 || (w & 1) || cells.has(w)) ? null : `${where}: dangling ${w}`;
  const frames = [];
  for (let top = r.top; top > r.F0;) {
    const head = u(top - 4), kind = head & 15, n = head >>> 4;
    if (kind > 6) return `frame kind ${kind}`;
    const base = top - 12 - 4 * n;
    if (base < r.F0) return 'frame below F0';
    for (let i = 0; i < n; i++) {
      const bad = word(u(base + 4 * i), `frame ${kind}`);
      if (bad) return bad;
    }
    frames.push(kind);
    top = base;
  }
  if (r.top !== r.F0 && frames.at(-1) !== 0) return 'bottom frame is not Top';
  if (r.act && cells.get(r.act)?.cls !== 4) return 'act is not an Activation';
  for (const [p, {cls, payload}] of cells) {
    const edges = cls === 0 ? [p + 16, payload - 2] : cls === 1 ? [p + 12, payload - 1]
      : cls === 3 ? [p + 12, payload - 1] : cls === 4 ? [p + 16, payload - 2] : [p, 0];
    for (let i = 0; i < edges[1]; i++) {
      const bad = word(u(edges[0] + 4 * i), `cell ${p}`);
      if (bad) return bad;
    }
  }
  if (r.mode === 1) return word(r.val, 'result');
  return null;
}

export async function runVM({module, files = {}, argv = [], limits = null, trace = null}) {
  const stdout = [], stderr = [], handles = new Map(), yields = [];
  let instance, next = 1, steps = 0, audited = 0, broken = null, booted = null;
  const mem = () => new Uint8Array(instance.exports.memory.buffer);
  // the VM passes u32 addresses and lengths, which arrive as signed numbers
  const text = (p, n) => strict.decode(mem().subarray(p >>> 0, (p >>> 0) + (n >>> 0)));
  const alloc = bytes => {
    const p = instance.exports.knot_alloc(bytes.length) >>> 0;
    mem().set(bytes, p);
    return p;
  };
  const result = (out, errno, value = 0, data = Buffer.alloc(0)) => {
    const p = data.length ? alloc(data) : 0;
    const v = new DataView(instance.exports.memory.buffer);
    [errno, value, p, data.length].forEach((w, i) => v.setUint32((out >>> 0) + 4 * i, w >>> 0, true));
  };
  const io = {
    args(out) {
      const table = Buffer.alloc(argv.length * 8);
      argv.forEach((a, i) => {
        const bytes = Buffer.from(a);
        table.writeUInt32LE(alloc(bytes), i * 8);
        table.writeUInt32LE(bytes.length, i * 8 + 4);
      });
      result(out, 0, argv.length, table);
    },
    print(p, n) {
      let line;
      try { line = text(p, n); } catch {
        // as the real host: text that is not scalar UTF-8 is an ABI fault
        stderr.push(Buffer.from('HostFailure\tio\tabi\n'));
        throw new Stop('HostFailure', 5);
      }
      stdout.push(Buffer.from(line + '\n'));
    },
    die(code, p, n) {
      stderr.push(Buffer.from(text(p, n) + '\n'));
      throw new Stop('Halted', (code >>> 0) % 256);
    },
    open(p, n, m, count, out) {
      const name = text(p, n), mode = text(m, count);
      if (mode !== 'r' || !Object.hasOwn(files, name)) return result(out, 2, 0, Buffer.from('No such file or directory'));
      handles.set(next, {data: files[name], at: 0});
      result(out, 0, next++);
    },
    read_bytes(id, maximum, out) {
      const h = handles.get(id);
      const n = Math.min(maximum >>> 0, h.data.length - h.at);
      const chunk = h.data.subarray(h.at, h.at + n);
      h.at += n;
      result(out, 0, id, Buffer.from(chunk));
    },
    close(id) { handles.delete(id); },
    exhausted(kind) {
      stderr.push(Buffer.from(`Exhausted\tio\t${{1: 'steps', 2: 'memory', 3: 'frames'}[kind]}\n`));
      throw new Stop('Exhausted', 4);
    },
  };
  instance = await WebAssembly.instantiate(module, {knot_io: io});
  const x = instance.exports;
  let status = 'Completed', exit = 0;
  try {
    if (limits) x.vm_limits(limits.frames, BigInt(limits.heap));
    if (!trace) x.knot_main();
    else {
      booted = false;
      x.vm_boot();
      booted = true;
      for (;;) {
        if (trace === 'audit' && !broken) {
          broken = audit(x);
          audited++;
        }
        const r = x.vm_step();
        steps++;
        if (r === 1) yields.push(registers(x).calls);
        if (r === 0) break;
      }
    }
  } catch (error) {
    if (error instanceof Stop) ({status, exit} = error);
    else if (error instanceof WebAssembly.RuntimeError) [status, exit] = ['Trap', 5];
    else if (error instanceof RangeError) [status, exit] = ['HostStack', 4];
    else throw error;
  }
  const state = x.vm_dump ? registers(x) : null;
  return {status, exit, stdout: Buffer.concat(stdout).toString(), stderr: Buffer.concat(stderr).toString(),
    state, steps, yields, audited, broken, booted};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
  const modules = new Map();
  for (const job of jobs) {
    if (!modules.has(job.wasm)) modules.set(job.wasm, await WebAssembly.compile(fs.readFileSync(job.wasm)));
    const files = Object.fromEntries(Object.entries(job.files ?? {}).map(([k, p]) => [k, fs.readFileSync(p)]));
    const got = await runVM({...job, module: modules.get(job.wasm), files});
    process.stdout.write(JSON.stringify({id: job.id, ...got}) + '\n');
  }
}
