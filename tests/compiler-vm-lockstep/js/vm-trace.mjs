#!/usr/bin/env node
// The VM side of vm-lockstep: run the test build one transition at a time
// (`vm_step`) and print the machine's complete state before the first
// transition and after each one, in the line format vm/model-trace.bend prints:
//
//   step | control | act | fuel calls quantum | top | frames | bump | free | output | heap
//
// Everything is read out of linear memory and the exported registers; the
// production module and the test build's source are not touched. The VM has
// no reclamation yet (vm/CORE.md choice 1), so `free` is always empty.
//
//   node vm-trace.mjs TEST_WASM STRIDE FROM TO IMAGE ARGS...     Book: FN FUEL [ORDINALS...]; Program: FUEL -- [ARGS...]
// A state is printed when its step is 0, a multiple of STRIDE or in FROM..TO, and whenever the machine has halted.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {registers} from '../../../vm/harness.mjs';

class Stop extends Error {
  constructor(status) { super('stop'); this.status = status; }
}

const strict = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});
export const HEAP_WORD_LIMIT = 1 << 22;

// Record offsets, in words, of the image's function table: the VM links an
// Application's target as the callee's record offset, the model as its index.
export function functionOffsets(image) {
  const words = new Uint32Array(image.buffer.slice(image.byteOffset, image.byteOffset + image.length - (image.length % 4)));
  const at = words[7], offsets = [];
  let record = at + 1;
  for (let i = 0; i < words[at]; i++) { offsets.push(record); record += words[record]; }
  return offsets;
}

const codes = text => [...text].map(c => c.codePointAt(0));

// `stderr` is the die text of a stop: `Class<TAB>phase<TAB>code`.
function stopText(r, text) {
  if (r.outcome === 'Exhausted') return `E:${r.kind}:${r.cause}`;
  const [cls, phase, ...code] = text.split('\t');
  const letter = {HostFailure: 'F', Unsupported: 'U', InternalFailure: 'I'}[cls] ?? '?';
  return letter === 'I' ? `I:${code.join(' ')}` : `${letter}:${phase}:${code.join(' ')}`;
}

export async function traceVM({module, image, argv = [], limit = 1 << 20, stride = 1, from = 0, to = -1}) {
  const stdout = [], names = ['image.kimg'], files = {'image.kimg': image}, handles = new Map();
  let instance, next = 1, dieText = null, dieCode = null;
  const mem = () => new Uint8Array(instance.exports.memory.buffer);
  const text = (p, n) => strict.decode(mem().subarray(p >>> 0, (p >>> 0) + (n >>> 0)));
  const alloc = bytes => { const p = instance.exports.knot_alloc(bytes.length) >>> 0; mem().set(bytes, p); return p; };
  const result = (out, errno, value = 0, data = Buffer.alloc(0)) => {
    const p = data.length ? alloc(data) : 0, v = new DataView(instance.exports.memory.buffer);
    [errno, value, p, data.length].forEach((w, i) => v.setUint32((out >>> 0) + 4 * i, w >>> 0, true));
  };
  const args = ['image.kimg', ...argv];
  const io = {
    args(out) {
      const table = Buffer.alloc(args.length * 8);
      args.forEach((a, i) => {
        const bytes = Buffer.from(a);
        table.writeUInt32LE(alloc(bytes), i * 8);
        table.writeUInt32LE(bytes.length, i * 8 + 4);
      });
      result(out, 0, args.length, table);
    },
    print(p, n) {
      try { stdout.push(text(p, n)); } catch { dieText = 'HostFailure\tio\tabi'; throw new Stop(5); }
    },
    die(code, p, n) { dieCode = code >>> 0; dieText = text(p, n); throw new Stop(code >>> 0); },
    open(p, n, m, count, out) {
      const name = text(p, n);
      if (text(m, count) !== 'r' || !Object.hasOwn(files, name)) return result(out, 2, 0, Buffer.from('No such file or directory'));
      handles.set(next, {data: files[name], at: 0});
      result(out, 0, next++);
    },
    read_bytes(id, maximum, out) {
      const h = handles.get(id), n = Math.min(maximum >>> 0, h.data.length - h.at), chunk = h.data.subarray(h.at, h.at + n);
      h.at += n;
      result(out, 0, id, Buffer.from(chunk));
    },
    close(id) { handles.delete(id); },
    exhausted(kind) { throw new Stop(kind); },
  };
  instance = await WebAssembly.instantiate(module, {knot_io: io});
  const x = instance.exports, offsets = functionOffsets(image), states = [];
  const u = at => new DataView(x.memory.buffer).getUint32(at, true);

  const frames = r => {
    const out = [];
    for (let top = r.top; top > r.F0;) {
      const head = u(top - 4), kind = head & 15, n = head >>> 4, base = top - 12 - 4 * n;
      out.push([kind, u(top - 12), u(top - 8), n, ...Array.from({length: n}, (_, i) => u(base + 4 * i))].join(','));
      top = base;
    }
    return out.join(';');
  };
  const heap = r => {
    const n = Math.floor((r.bump - r.H0) / 4);
    if (n > limit) throw new Error(`heap of ${n} words exceeds the trace limit ${limit}`);
    return Array.from(new Uint32Array(x.memory.buffer, r.H0, n)).map(w => ` ${w}`).join('');
  };
  const enter = r => {
    const ops = Array.from({length: r.nops}, (_, i) => ` ${u(r.ops + 4 * i)}`).join('');
    return r.tfn ? `N F ${offsets.indexOf(r.tgt)}${ops}` : `N W ${r.tgt}${ops}`;
  };
  const control = (r, stopped) => {
    if (r.mode === 0) return `E ${r.node}`;
    if (r.mode === 1) return `R ${r.val}`;
    if (r.mode === 2) return enter(r);
    const last = stdout.at(-1);
    if (r.outcome === 'Completed') {
      if (last?.startsWith('Evaluated\t')) {
        const [, type, tag, tree] = last.split('\t');
        return `H D ${type} ${tag} ${codes(tree).map(c => `${c}`).join(',')}`.replace(/,$/, '');
      }
      return 'H X';
    }
    if (r.outcome === 'Halted') return `H Z ${dieCode} ${codes(dieText).join(',')}`;
    // At zero fuel the pending Enter's registers are kept (CORE.md choice 8): print them as the model's
    // `Stopped` keeps its Enter. Any other stop keeps no control the registers can name.
    return `H S ${stopText(r, dieText ?? '')}@${r.outcome === 'Exhausted' && r.cause === 'fuel' ? enter(r) : '?'}`;
  };
  const outputs = r => {
    const lines = r.mode === 3 && r.outcome === 'Completed' && stdout.at(-1)?.startsWith('Evaluated\t') ? stdout.slice(0, -1) : stdout;
    return `${lines.length}:${lines.map(line => codes(line).join(',')).join('/')}`;
  };
  const state = (step, stopped = false) => {
    const r = registers(x);
    const halted = r.mode === 3;
    if (!(halted || step === 0 || step % stride === 0 || (step >= from && step <= to))) return;
    states.push([step, control(r, stopped), r.act, `${r.fuel} ${r.calls} ${r.quantum}`, (r.top - r.F0) / 4, frames(r), r.bump, '', outputs(r), heap(r)].join('|'));
  };

  let booted = false, status = 'Completed', step = 1, refusal = '';
  const yields = [];
  try {
    x.vm_boot();
    booted = true;
    state(0);
    for (;; step++) {
      const r = x.vm_step();
      if (r === 1) yields.push(step);  // a quantum yield: the entry completed, vm_step reset quantum
      state(step);
      if (r === 0) break;
    }
  } catch (error) {
    if (!(error instanceof Stop)) throw error;
    status = 'Stopped';
    if (booted) state(step);
    else {
      const r = registers(x);
      refusal = r.outcome === 'Exhausted' ? `Exhausted\tvm\t${r.kind}\t${r.cause}` : (dieText ?? '').trim();
    }
  }
  return {booted, status, states, stdout, dieText, refusal, yields};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [wasm, stride, from, to, imagePath, ...argv] = process.argv.slice(2);
  const module = await WebAssembly.compile(fs.readFileSync(wasm));
  const got = await traceVM({module, image: fs.readFileSync(imagePath), argv, stride: Number(stride), from: Number(from), to: Number(to)});
  if (!got.booted) process.stdout.write(`R ${got.refusal}\n`);
  else process.stdout.write(got.states.join('\n') + `\n#yields ${got.yields.join(',')}\n`);
}
