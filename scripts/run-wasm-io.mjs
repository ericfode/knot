#!/usr/bin/env node
// Host effects only. The guest owns values, continuations, and byte-list validation.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

// knot-io-2: knot-io-1 plus read_bytes, path_identity and exhaustion kind 3.
const signatures = Object.freeze({
  args: [1, 0], print: [2, 0], die: [3, 0], open: [5, 0], read: [3, 0],
  read_bytes: [3, 0], write_bytes: [5, 0], close: [1, 0], path_identity: [3, 0],
  exhausted: [1, 0],
});
const errors = Object.freeze({
  ENOENT: [2, 'No such file or directory'], EBADF: [9, 'Bad file descriptor'],
  ENOTDIR: [20, 'Not a directory'], EISDIR: [21, 'Is a directory'],
  EINVAL: [22, 'Invalid argument'], EILSEQ: [92, 'Illegal byte sequence'],
});
// Identity fails only on NUL and on the length and listing errors its foreign bodies witness.
const identityErrors = Object.freeze({
  EACCES: [13, 'Permission denied'], EILSEQ: errors.EILSEQ,
  ENAMETOOLONG: [63, 'File name too long'],
});
const MAX_MEMORY = 128 * 1024 * 1024;
const MAX_TRANSFER = 16 * 1024 * 1024;
const decoder = new TextDecoder('utf-8', {ignoreBOM: true});
const strictDecoder = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});
const normalize = bytes => Buffer.from(decoder.decode(bytes), 'utf8');
const secret = parts => parts.some(p => {
  const q = p.toLowerCase();
  return q === '.env' || q.startsWith('.env.');
});

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
  function fail(out, code, handle = 0, surface = errors) {
    const pair = surface[code];
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
    if (path.isAbsolute(name) || parts.includes('..') || secret(parts)) bad('sandbox', 'path refused');
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
  // Identity may spell the canonical root absolutely and step back to it, never above it.
  // Policy only refuses spellings: an absolute one is walked from '/', through the root's ancestors.
  function rooted(name) {
    const parts = name.split('/').filter(p => p && p !== '.');
    const base = path.isAbsolute(name) ? root.split('/').filter(Boolean) : [];
    let depth = 0;
    if (secret(parts) || base.some((b, i) => parts[i] !== b) ||
        parts.slice(base.length).some(p => (depth += p === '..' ? -1 : 1) < 0)) bad('sandbox', 'path refused');
    return path.isAbsolute(name) ? ['/', parts] : [root, parts];
  }
  // The modules loader's foreign `inspect`: in spelling order, every existing
  // component is an exact directory entry and no symlink; a missing one defers to open.
  function canonical(current, parts) {
    for (const part of parts) {
      if (part === '..') { current = path.dirname(current); continue; }
      const next = path.join(current, part);
      let st;
      try { st = fs.lstatSync(next); }
      catch (error) {
        if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return true;
        throw error;
      }
      if (st.isSymbolicLink()) return false;
      const exact = fs.readdirSync(current, {encoding: 'buffer'}).some(entry => entry.equals(Buffer.from(part)));
      if (!exact) return false;
      current = next;
    }
    return true;
  }
  // read decodes each result independently; read_bytes returns it raw. Both share the cursor.
  function readFile(id, maximum, out, decode) {
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
      bytes = decode(bytes.subarray(0, count));
    } catch (error) {
      if (error instanceof Fault) throw error;
      return fail(out, error.code, id);
    }
    result(out, 0, id, bytes);
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
    read: (id, maximum, out) => readFile(id, maximum, out, normalize),
    read_bytes: (id, maximum, out) => readFile(id, maximum, out, bytes => bytes),
    write_bytes(id, p, n, invalid, out) {
      resultRange(out);
      const h = handle(id);
      // The guest scans all U32 elements before narrowing; invalid is its OR of high bits.
      if (invalid !== 0) return fail(out, 'EINVAL', id);
      const bytes = range(p, n);
      if (bytes.length > MAX_TRANSFER) exhausted('memory');
      if (h.mode === 'r' && bytes.length > 0) return fail(out, 'EBADF', id);
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
    path_identity(p, n, out) {
      resultRange(out);
      const name = text(p, n);
      if (name.includes('\0')) return fail(out, 'EILSEQ');
      const walk = rooted(name);
      let exact;
      try { exact = canonical(...walk); }
      catch (error) { return fail(out, error.code, 0, identityErrors); }
      result(out, 0, exact ? 1 : 0);
    },
    exhausted(kind) {
      // The allocator's sole permitted callback is exhausted(2).
      if (allocating && kind !== 2) bad('abi', 'effect outside guest invocation');
      if (kind === 1) exhausted('steps');
      if (kind === 2) exhausted('memory');
      if (kind === 3) exhausted('frames');
      bad('abi', 'unknown exhaustion reason');
    },
  };
  try {
    // The native call also restores on-disk case, so rooted identity queries see the canonical root.
    root = fs.realpathSync.native(sandbox);
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
