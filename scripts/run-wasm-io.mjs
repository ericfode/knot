#!/usr/bin/env node
// Host effects only. The guest owns values, continuations, and byte-list validation.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const signatures = Object.freeze({
  args: [1, 0], print: [2, 0], die: [3, 0], open: [5, 0],
  read: [3, 0], write_bytes: [5, 0], close: [1, 0], exhausted: [1, 0],
});
const errors = Object.freeze({
  ENOENT: [2, 'No such file or directory'], EBADF: [9, 'Bad file descriptor'],
  ENOTDIR: [20, 'Not a directory'], EISDIR: [21, 'Is a directory'],
  EINVAL: [22, 'Invalid argument'], EILSEQ: [92, 'Illegal byte sequence'],
});
const MAX_MEMORY = 128 * 1024 * 1024;
const MAX_TRANSFER = 16 * 1024 * 1024;
const decoder = new TextDecoder('utf-8', {ignoreBOM: true});
const strictDecoder = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});
const normalize = bytes => Buffer.from(decoder.decode(bytes), 'utf8');

class Fault extends Error {
  constructor(status, code, exit, message = code) {
    super(message);
    Object.assign(this, {status, code, exit});
  }
}
class Halt { constructor(exit) { this.exit = exit; } }
const bad = (code, message) => { throw new Fault('HostFailure', code, 5, message); };
const exhausted = code => { throw new Fault('Exhausted', code, 4); };

// Validation checks the engine's types first; this reader enforces the narrower ABI.
function abi(bytes) {
  let at = 8, end = bytes.length;
  const byte = () => {
    if (at >= end) bad('abi', 'truncated section');
    return bytes[at++];
  };
  const uint = () => {
    let value = 0;
    for (let n = 0; n < 5; n++) {
      const b = byte();
      value += (b & 127) * 2 ** (7 * n);
      if (!(b & 128)) return value;
    }
    bad('abi', 'oversized integer');
  };
  const name = () => {
    const size = uint();
    if (size > end - at) bad('abi', 'truncated name');
    const text = strictDecoder.decode(bytes.subarray(at, at + size));
    at += size;
    return text;
  };
  const vector = read => Array.from({length: uint()}, read);
  const types = [], functions = [], exports = new Map(), imports = new Set();
  let memories = 0;
  while (at < bytes.length) {
    end = bytes.length;
    const section = byte(), size = uint();
    end = at + size;
    if (end > bytes.length) bad('abi', 'section out of bounds');
    if (section === 1) types.push(...vector(() => {
      if (byte() !== 0x60) bad('abi', 'only function types supported');
      return [vector(byte), vector(byte)];
    }));
    if (section === 2) vector(() => {
      const module = name(), field = name(), kind = byte();
      if (module !== 'knot_io' || !Object.hasOwn(signatures, field) || kind !== 0)
        throw new Fault('Unsupported', 'import', 3, 'unlisted import');
      if (imports.has(field)) bad('abi', 'duplicate import');
      imports.add(field);
      const type = uint();
      functions.push(type);
      signature(type, ...signatures[field]);
    });
    if (section === 3) functions.push(...vector(uint));
    if (section === 5) vector(() => {
      memories++;
      if (byte() !== 1) bad('abi', 'memory needs an unshared i32 maximum');
      const minimum = uint(), maximum = uint();
      if (minimum > maximum || maximum * 65536 > MAX_MEMORY) bad('abi', 'memory limit');
    });
    if (section === 7) vector(() => { const n = name(); exports.set(n, [byte(), uint()]); });
    if (section === 8) bad('abi', 'start section forbidden');
    at = end;
  }
  function signature(index, params, results) {
    const type = types[index];
    if (!type || type[0].length !== params || type[1].length !== results ||
        type.flat().some(t => t !== 0x7f)) bad('abi', 'wrong function signature');
  }
  for (const [n, params, results] of [['knot_main', 0, 0], ['knot_alloc', 1, 1]]) {
    const item = exports.get(n);
    if (!item || item[0] !== 0) bad('abi', 'missing function export');
    signature(functions[item[1]], params, results);
  }
  const memory = exports.get('memory');
  if (memories !== 1 || !memory || memory[0] !== 2 || memory[1] !== 0) bad('abi', 'memory export');
}

function writeAll(fd, bytes) {
  for (let at = 0; at < bytes.length;) {
    const n = fs.writeSync(fd, bytes, at, bytes.length - at);
    if (n <= 0) bad('output', 'write made no progress');
    at += n;
  }
}

export async function runIO({modulePath, sandbox, args = []}) {
  let instance, allocating = false, nextHandle = 1, root;
  const handles = new Map();
  function ready() {
    if (!instance || allocating) bad('abi', 'effect outside guest invocation');
  }
  function memory() {
    ready();
    return instance.exports.memory;
  }
  function range(pointer, length) {
    const p = pointer >>> 0, n = length >>> 0, buffer = memory().buffer;
    if (n > buffer.byteLength || p > buffer.byteLength - n) bad('abi', 'range out of bounds');
    return Buffer.from(buffer, p, n);
  }
  function resultRange(out) {
    if ((out & 3) !== 0) bad('abi', 'unaligned result');
    range(out, 16);
  }
  function text(p, n) {
    try { return strictDecoder.decode(range(p, n)); }
    catch (error) { if (error instanceof Fault) throw error; bad('abi', 'non-scalar UTF-8'); }
  }
  function allocate(bytes) {
    if (bytes.length > MAX_TRANSFER) exhausted('memory');
    allocating = true;
    let p;
    try { p = instance.exports.knot_alloc(bytes.length); }
    finally { allocating = false; }
    range(p, bytes.length).set(bytes);
    return p >>> 0;
  }
  function result(out, errno = 0, value = 0, data = Buffer.alloc(0)) {
    const p = data.length ? allocate(data) : 0;
    // Allocation may grow memory and detach prior views.
    const words = range(out, 16);
    [errno, value, p, data.length].forEach((v, i) => words.writeUInt32LE(v >>> 0, i * 4));
  }
  function fail(out, code, handle = 0) {
    const pair = errors[code];
    if (!pair) bad('os', 'unmodeled OS failure');
    result(out, pair[0], handle, Buffer.from(pair[1]));
  }
  function handle(id) {
    const h = handles.get(id >>> 0);
    if (!h) bad('handle', 'unknown or closed handle');
    return h;
  }
  function confined(name) {
    const parts = name.split('/');
    if (path.isAbsolute(name) || parts.includes('..') ||
        parts.some(p => p === '.env' || p.startsWith('.env.'))) bad('sandbox', 'path refused');
    let current = root;
    for (const part of parts.filter(p => p && p !== '.')) {
      current = path.join(current, part);
      try {
        const st = fs.lstatSync(current);
        if (st.isSymbolicLink() || (!st.isDirectory() && (!st.isFile() || st.nlink !== 1)))
          bad('sandbox', 'link or special file refused');
      } catch (error) {
        if (error.code === 'ENOENT' || error.code === 'ENOTDIR') break;
        throw error;
      }
    }
    return root + '/' + name;
  }
  const io = {
    args(out) {
      resultRange(out);
      const strings = args.map(a => {
        if (typeof a !== 'string' && !Buffer.isBuffer(a) && !(a instanceof Uint8Array))
          bad('arguments', 'expected strings or raw bytes');
        const bytes = normalize(typeof a === 'string' ? Buffer.from(a) : a);
        return [allocate(bytes), bytes.length];
      });
      const table = Buffer.alloc(strings.length * 8);
      strings.forEach(([p, n], i) => { table.writeUInt32LE(p, i * 8); table.writeUInt32LE(n, i * 8 + 4); });
      result(out, 0, strings.length, table);
    },
    print(p, n) {
      const bytes = Buffer.from(text(p, n));
      writeAll(1, Buffer.concat([bytes, Buffer.from('\n')]));
    },
    die(code, p, n) {
      writeAll(2, Buffer.from(text(p, n) + '\n'));
      throw new Halt((code >>> 0) % 256);
    },
    open(p, n, m, count, out) {
      resultRange(out);
      const name = text(p, n);
      if (name.includes('\0')) return fail(out, 'EILSEQ');
      const mode = text(m, count);
      if (!['r', 'w', 'a'].includes(mode)) return fail(out, 'EINVAL');
      if (name === '') return fail(out, 'ENOENT');
      const target = confined(name);
      let fd;
      try {
        const c = fs.constants;
        const flags = {r: c.O_RDONLY, w: c.O_WRONLY | c.O_CREAT | c.O_TRUNC,
          a: c.O_WRONLY | c.O_CREAT | c.O_APPEND};
        fd = fs.openSync(target, flags[mode] | c.O_NOFOLLOW, 0o644);
        const stat = fs.fstatSync(fd);
        if (!stat.isDirectory() && (!stat.isFile() || stat.nlink !== 1)) bad('sandbox', 'special file refused');
        if (nextHandle > 0x7fffffff) exhausted('handles');
        const id = nextHandle++;
        handles.set(id, {fd, mode, directory: stat.isDirectory(), position: 0});
        fd = undefined;
        result(out, 0, id);
      } catch (error) {
        if (fd !== undefined) fs.closeSync(fd);
        if (error instanceof Fault) throw error;
        fail(out, error.code);
      }
    },
    read(id, maximum, out) {
      resultRange(out);
      const h = handle(id);
      if (h.mode !== 'r') return fail(out, 'EBADF', id);
      if (h.directory) return fail(out, 'EISDIR', id);
      let bytes;
      try {
        const remaining = Math.max(0, fs.fstatSync(h.fd).size - h.position);
        const size = Math.min(maximum >>> 0, remaining);
        if (size > MAX_TRANSFER) exhausted('memory');
        bytes = Buffer.alloc(size);
        const count = fs.readSync(h.fd, bytes, 0, size, null);
        h.position += count;
        bytes = normalize(bytes.subarray(0, count));
      } catch (error) {
        if (error instanceof Fault) throw error;
        return fail(out, error.code, id);
      }
      result(out, 0, id, bytes);
    },
    write_bytes(id, p, n, invalid, out) {
      resultRange(out);
      const h = handle(id);
      // The guest scans all U32 elements before narrowing; invalid is its OR of high bits.
      if (invalid !== 0) return fail(out, 'EINVAL', id);
      const bytes = range(p, n);
      if (bytes.length > MAX_TRANSFER) exhausted('memory');
      if (h.mode === 'r') return fail(out, 'EBADF', id);
      try { writeAll(h.fd, bytes); }
      catch (error) {
        if (error instanceof Fault) throw error;
        return fail(out, error.code, id);
      }
      result(out, 0, id);
    },
    close(id) {
      ready();
      const h = handle(id);
      handles.delete(id >>> 0);
      try { fs.closeSync(h.fd); } catch { /* Base ignores close errors. */ }
    },
    exhausted(kind) {
      if (kind === 1) exhausted('steps');
      if (kind === 2) exhausted('memory');
      bad('abi', 'unknown exhaustion reason');
    },
  };
  try {
    root = fs.realpathSync(sandbox);
    if (!fs.statSync(root).isDirectory()) bad('sandbox', 'working directory required');
    let bytes;
    try { bytes = fs.readFileSync(modulePath); } catch { bad('module', 'module unreadable'); }
    if (!WebAssembly.validate(bytes)) bad('module', 'Wasm validation failed');
    abi(bytes);
    const module = await WebAssembly.compile(bytes);
    instance = await WebAssembly.instantiate(module, {knot_io: io});
    instance.exports.knot_main();
    return {status: 'Completed', exit: 0};
  } catch (error) {
    if (error instanceof Halt) return {status: 'Halted', exit: error.exit};
    if (error instanceof RangeError && /maximum call stack size exceeded/i.test(error.message))
      error = new Fault('Exhausted', 'call-stack', 4);
    if (!(error instanceof Fault)) error = new Fault('HostFailure',
      error instanceof WebAssembly.RuntimeError ? 'trap' : 'host', 5);
    writeAll(2, Buffer.from(`${error.status}\tio\t${error.code}\n`));
    return {status: error.status, code: error.code, exit: error.exit};
  } finally {
    for (const h of handles.values()) { try { fs.closeSync(h.fd); } catch {} }
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = 5;
  const [modulePath, sandbox, separator, ...args] = process.argv.slice(2);
  if (!modulePath || !sandbox || (separator !== undefined && separator !== '--')) {
    fs.writeSync(2, 'HostFailure\tio\tusage: module sandbox [-- arguments...]\n');
  } else {
    try { process.exitCode = (await runIO({modulePath, sandbox, args})).exit; }
    catch { fs.writeSync(2, 'HostFailure\tio\thost\n'); }
  }
}
