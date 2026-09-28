#!/usr/bin/env node
// Host seam for Knot-built Wasm modules in the bootstrap harness. It supplies
// input bytes and returns observations; it contains no Bend source semantics
// and never writes files. See README.md for the request and ABI contracts.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// The IO fixture suite (campaign/io) defines the real host ABI. It plugs in by
// adding this module, exporting `run(module, runs) -> [observation]`.
const IO_ADAPTER = path.join(path.dirname(fileURLToPath(import.meta.url)), 'io-abi.mjs');

const b64 = bytes => Buffer.from(bytes).toString('base64');
const note = (exit, outcome, phase, code) => ({ exit, stdout: '', stderr: b64(`${outcome}\t${phase}\t${code}\n`), host: true });
const blocked = (source, exit, outcome, code) => ({ source, exit, stdout: '', stderr: `${outcome}\thost\t${code}\n` });

// A trap is the host's observation, not the module's own exit record. Running
// out of the host's stack or memory is Exhausted (host: true), which the
// harness tags host-stack or host-memory; any other trap is a HostFailure.
export function trap(error) {
  if (error instanceof RangeError && /maximum call stack size exceeded/i.test(error.message)) {
    return note(4, 'Exhausted', 'wasm', 'call-stack');
  }
  if (error instanceof RangeError && /out of memory|(could not|cannot) allocate|allocation failed/i.test(error.message)) {
    return note(4, 'Exhausted', 'wasm', 'memory');
  }
  return note(5, 'HostFailure', 'wasm', String(error.message).replace(/\s+/g, ' '));
}

// knot-bytes-0: input bytes in, (exit, stdout, stderr) bytes out, one fresh
// instance per run so no state crosses corpus files.
function runBytes(module, run) {
  const input = fs.readFileSync(run.argv[0]);
  try {
    const { memory, knot_input, knot_run } = new WebAssembly.Instance(module, {}).exports;
    const at = knot_input(input.length) >>> 0;
    new Uint8Array(memory.buffer, at, input.length).set(input);
    const record = knot_run(input.length) >>> 0;
    const view = new DataView(memory.buffer);
    const [exit, out, err] = [0, 4, 8].map(offset => view.getUint32(record + offset, true));
    const start = record + 12;
    if (start + out + err > memory.buffer.byteLength) return note(5, 'HostFailure', 'wasm', 'record-out-of-bounds');
    const bytes = new Uint8Array(memory.buffer);
    return { exit, stdout: b64(bytes.slice(start, start + out)), stderr: b64(bytes.slice(start + out, start + out + err)) };
  } catch (error) {
    return trap(error);
  }
}

function exportsBytesAbi(module) {
  const kinds = Object.fromEntries(WebAssembly.Module.exports(module).map(e => [e.name, e.kind]));
  return kinds.memory === 'memory' && kinds.knot_input === 'function' && kinds.knot_run === 'function';
}

async function invoke(request) {
  const bytes = fs.readFileSync(request.module);
  // Knot emitted this module; an invalid one is a compiler defect, never Unsupported.
  if (!WebAssembly.validate(bytes)) return { abi: null, blocked: blocked('knot', 5, 'HostFailure', 'invalid-module'), runs: [] };
  const module = new WebAssembly.Module(bytes);
  const wanted = request.abi ?? 'auto';
  const abi = wanted !== 'auto' ? wanted
    : WebAssembly.Module.imports(module).length ? 'knot-io'
    : exportsBytesAbi(module) ? 'knot-bytes-0' : null;
  if (abi === 'knot-bytes-0') {
    if (!exportsBytesAbi(module) || WebAssembly.Module.imports(module).length) {
      return { abi, blocked: blocked('knot', 5, 'HostFailure', 'abi-mismatch'), runs: [] };
    }
    return { abi, blocked: null, runs: request.runs.map(run => runBytes(module, run)) };
  }
  if (abi === 'knot-io') {
    if (!fs.existsSync(IO_ADAPTER)) return { abi, blocked: blocked('harness', 3, 'Unsupported', 'io-abi-pending'), runs: [] };
    const adapter = await import(pathToFileURL(IO_ADAPTER).href);
    return { abi, blocked: null, runs: await adapter.run(module, request.runs) };
  }
  return { abi, blocked: blocked('harness', 3, 'Unsupported', 'abi-unrecognized'), runs: [] };
}

// Imported (by the harness's classification control) it only exports trap().
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const [requestPath] = process.argv.slice(2);
  if (!requestPath) {
    console.error('HostFailure\targuments\texpected request.json');
    process.exit(5);
  }
  process.stdout.write(JSON.stringify(await invoke(JSON.parse(fs.readFileSync(requestPath, 'utf8')))) + '\n');
}
