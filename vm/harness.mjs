#!/usr/bin/env node
// Test harness for knot-vm-1: an in-memory knot_io host for the imports the VM
// uses, mirroring scripts/run-wasm-io.mjs's observable conventions (stdout,
// stderr, exit and the `Exhausted<TAB>io<TAB>kind` line). With the test build
// it also steps the machine and reads its state. The gate uses it for batches;
// acceptance runs of the production module go through the real host.
//
// Batch mode: a JSON array of jobs on stdin, one JSON result per line.
//   {id, wasm, files: {name: path}, argv, limits?: {frames, heap}, trace?: 'yields' | 'audit', deadline?: ms, atomic?: true}
// An `atomic` job is traced, and when it ends in a refusal of the kinds that SPEC section 6 says change no state (an
// ill-typed word, a request that a read meets, NatRange, D20's `io abi`) the run is played again to its last step and the
// result's `atomic` names the registers and memory that step changed (`moved`, empty when it left the machine as it found it).
// The step that returns a Book's result to Top is exempt: SPEC section 6's table drops `act` before section 8 describes.
// A result reports `effects`: the host calls the run made for requests (every `print`, less the one a completed Book's result is described with).
// A traced result says whether vm_boot returned (`booted`): an image refusal
// happens before, a run-time failure after. A job with a `deadline` that outlives it is stopped and
// reported as status `Timeout` (a run that does not end is a defect only where the row promises an
// end); with KNOT_HARNESS_MAX_TIMEOUTS set, the jobs after that many timeouts are `Skipped`.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
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
    if (cls > 5) return `class ${cls} at ${p}`;
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
      : cls === 3 || cls === 5 ? [p + 12, payload - 1] : cls === 4 ? [p + 16, payload - 2] : [p, 0];
    for (let i = 0; i < edges[1]; i++) {
      const bad = word(u(edges[0] + 4 * i), `cell ${p}`);
      if (bad) return bad;
    }
  }
  if (r.mode === 1) return word(r.val, 'result');
  return null;
}

// The machine as a step sees it: its registers but the outcome's, the frame region below Top and the cells of the heap.
function snapshot(x) {
  const r = registers(x), bytes = new Uint8Array(x.memory.buffer);
  return {r, frames: Buffer.from(bytes.subarray(r.F0, r.top)), heap: Buffer.from(bytes.subarray(r.H0, r.bump))};
}

// What one step changed. Its debit (one unit of fuel for one call and one quantum) is the step's own (SPEC section 7).
function moved(before, after) {
  const names = ['node', 'val', 'tgt', 'tfn', 'ops', 'nops', 'act', 'top', 'bump'].filter(k => before.r[k] !== after.r[k]);
  const debit = before.r.fuel - after.r.fuel === 1 && after.r.calls - before.r.calls === 1 && after.r.quantum - before.r.quantum === 1;
  if (!debit) names.push(...['fuel', 'calls', 'quantum'].filter(k => before.r[k] !== after.r[k]));
  const kept = Math.min(before.r.top, after.r.top) - before.r.F0;
  if (!before.frames.subarray(0, kept).equals(after.frames.subarray(0, kept))) names.push('frames');
  if (!before.heap.equals(after.heap)) names.push('heap');
  return names;
}

// The step that returns a Book's result to its Top frame (phase 0) is not held to atomicity: section 6's table drops `act` first.
function booksAnswer(before) {
  const f = before.frames, n = f.length;
  return before.r.mode === 1 && n >= 12 && (f.readUInt32LE(n - 4) & 15) === 0 && f.readUInt32LE(n - 8) === 0;
}

const ATOMIC = new Set(['ill-typed', 'effect', 'NatRange', 'abi']);

export async function runVM({module, files = {}, argv = [], limits = null, trace = null, deadline = null, atomicAt = null}) {
  const stdout = [], stderr = [], handles = new Map(), yields = [];
  let instance, next = 1, steps = 0, audited = 0, broken = null, booted = null, prints = 0, entry = null, atomic = null;
  const mem = () => new Uint8Array(instance.exports.memory.buffer);
  // the VM passes u32 addresses and lengths, which arrive as signed numbers. As the real host: text that
  // is not scalar UTF-8 is an ABI fault, in a print, a Halt message or a name alike.
  const text = (p, n) => {
    try { return strict.decode(mem().subarray(p >>> 0, (p >>> 0) + (n >>> 0))); } catch {
      stderr.push(Buffer.from('HostFailure\tio\tabi\n'));
      throw new Stop('HostFailure', 5);
    }
  };
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
      stdout.push(Buffer.from(text(p, n) + '\n'));
      prints++;
    },
    die(code, p, n) {
      stderr.push(Buffer.from(text(p, n) + '\n'));
      throw new Stop('Halted', (code >>> 0) % 256);
    },
    open(p, n, m, count, out) {
      const name = text(p, n), mode = text(m, count);
      if (mode !== 'r' || !Object.hasOwn(files, name)) return result(out, 2, 0, Buffer.from('No such file or directory'));
      entry ??= files[name].length >= 16 ? files[name].readUInt32LE(12) : null;  // the image's entry kind: 0 Book, 1 Program
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
  const execute = () => {
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
          let r;
          if (steps === atomicAt) {  // the last step of a run that stops: what it changed
            const before = snapshot(x);
            try { r = x.vm_step(); } finally {
              atomic = booksAnswer(before) ? {exempt: true, moved: []} : {exempt: false, moved: moved(before, snapshot(x))};
            }
          } else r = x.vm_step();
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
  };
  if (deadline) {
    globalThis.knotExecute = execute;  // the watchdog stops a loop that never ends, Wasm loops included
    try { vm.runInThisContext('knotExecute()', {timeout: deadline}); } catch (error) {
      if (error?.code !== 'ERR_SCRIPT_EXECUTION_TIMEOUT') throw error;
      [status, exit] = ['Timeout', 4];
    }
  } else execute();
  const state = x.vm_dump ? registers(x) : null;
  return {status, exit, stdout: Buffer.concat(stdout).toString(), stderr: Buffer.concat(stderr).toString(),
    state, steps, yields, audited, broken, booted, atomic,
    // host calls made for requests: every `print`, less the one a completed Book's result is described with
    effects: prints - (entry === 0 && status === 'Completed' ? 1 : 0)};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
  const modules = new Map(), most = Number(process.env.KNOT_HARNESS_MAX_TIMEOUTS ?? Infinity);
  let timeouts = 0;
  for (const job of jobs) {
    if (timeouts >= most) {
      process.stdout.write(JSON.stringify({id: job.id, status: 'Skipped', exit: null, stdout: '', stderr: '', state: null}) + '\n');
      continue;
    }
    if (!modules.has(job.wasm)) modules.set(job.wasm, await WebAssembly.compile(fs.readFileSync(job.wasm)));
    const files = Object.fromEntries(Object.entries(job.files ?? {}).map(([k, p]) => [k, fs.readFileSync(p)]));
    let got = await runVM({...job, module: modules.get(job.wasm), files, trace: job.atomic ? job.trace ?? 'yields' : job.trace});
    if (job.atomic) {
      const stop = got.booted && got.state && ATOMIC.has(got.state.cause) && ['HostFailure', 'Unsupported', 'Exhausted'].includes(got.state.outcome);
      const again = stop ? await runVM({...job, module: modules.get(job.wasm), files, trace: 'yields', atomicAt: got.steps}) : null;
      got = {...got, atomic: again ? again.atomic : null};
    }
    timeouts += got.status === 'Timeout';
    process.stdout.write(JSON.stringify({id: job.id, ...got}) + '\n');
  }
}
