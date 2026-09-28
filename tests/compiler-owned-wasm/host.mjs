import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

function require(condition, detail) {
  if (!condition) throw new Error(detail);
}

export async function instantiate(path) {
  const bytes = await readFile(path);
  require(WebAssembly.validate(bytes), 'invalid Wasm module');
  const module = await WebAssembly.compile(bytes);
  require(WebAssembly.Module.imports(module).length === 0, 'unexpected imports');
  return (await WebAssembly.instantiate(module)).exports;
}

export function snapshot(exports) {
  const get = name => typeof exports[name] === 'function' ? exports[name]() >>> 0 : null;
  return {
    live: get('__heap_live') ?? 0,
    allocations: get('__heap_allocations') ?? 0,
    peak: get('__heap_peak') ?? 0,
    pending: get('__heap_pending') ?? 0,
    status: get('__heap_status') ?? 0,
    bump: get('__heap_bump'),
    memory_bytes: exports.__heap_memory?.buffer.byteLength ?? 0,
  };
}

// This decodes a reviewed physical layout. It does not parse or execute Bend.
export function decode(exports, value, resultType, types) {
  const memory = exports.__heap_memory;
  const view = memory ? new DataView(memory.buffer) : null;
  const cells = new Map();
  const active = new Set();
  const incoming = new Map();
  const word = address => {
    require(view && address % 4 === 0 && address >= 0 && address + 4 <= view.byteLength,
      `invalid word address ${address}`);
    return view.getUint32(address, true);
  };
  function visit(raw, typeId, depth) {
    require(depth < 4096, 'decoder depth exhausted');
    const type = types[typeId];
    require(type, `missing literal descriptor ${typeId}`);
    const pointer = raw >>> 0;
    const tag = type.cell ? word(pointer) : pointer;
    const constructor = type.constructors[tag];
    require(constructor, `invalid tag ${tag} for ${type.name}`);
    if (!type.cell) return `${constructor.name}{}`;
    incoming.set(pointer, (incoming.get(pointer) ?? 0) + 1);
    require(!active.has(pointer), 'cyclic result');
    if (cells.has(pointer)) {
      const old = cells.get(pointer);
      require(old.type === typeId, 'aliased cell has incompatible descriptors');
      return old.tree;
    }
    active.add(pointer);
    const fields = constructor.fields.map((field, i) => visit(word(pointer + 4 + 4 * i), field, depth + 1));
    active.delete(pointer);
    const tree = `${constructor.name}{${fields.join(',')}}`;
    cells.set(pointer, { pointer, type: typeId, kind: type.kind, tag, tree,
      state: word(pointer - 12), count: word(pointer - 8), layout: word(pointer - 4) });
    return tree;
  }
  const tree = visit(value, resultType, 0);
  const records = [...cells.values()].sort((a, b) => a.pointer - b.pointer)
    .map(({ tree: _tree, ...cell }) => ({ ...cell, incoming: incoming.get(cell.pointer) }));
  return { tree, reachable: cells.size, cells: records,
    ownership_valid: records.every(cell => cell.state === 1 &&
      (cell.kind === 'Data' ? cell.count === cell.incoming : cell.incoming === 1 && cell.count === 1)) };
}

function classify(exports, error) {
  const status = snapshot(exports).status;
  if (error instanceof WebAssembly.RuntimeError) {
    return { outcome: status === 3 ? 'Exhausted' : 'InternalFailure', status, message: error.message };
  }
  if (error instanceof RangeError && /stack/i.test(error.message)) {
    return { outcome: 'Exhausted', reason: 'call-stack', message: error.message };
  }
  throw error;
}

function invoke(exports, name, args = []) {
  require(typeof exports[name] === 'function', `missing export ${name}`);
  require(exports[name].length === args.length, `arity mismatch for ${name}`);
  try { return { outcome: 'Returned', value: exports[name](...args) >>> 0 }; }
  catch (error) { return classify(exports, error); }
}

function requiredHeap(exports) {
  for (const name of ['live', 'allocations', 'peak', 'pending', 'status', 'bump',
    'share', 'release', 'enqueue', 'clean', 'stack_limit', 'rc_limit']) {
    require(typeof exports[`__heap_${name}`] === 'function', `missing heap debug export ${name}`);
  }
  require(exports.__heap_memory instanceof WebAssembly.Memory, 'missing debug memory');
}

export function observe(exports, request) {
  if (request.types.some(type => type.cell)) requiredHeap(exports);
  const observations = [];
  for (const call of request.calls) {
    const before = snapshot(exports);
    const result = invoke(exports, call.export, call.arguments);
    const item = { export: call.export, arguments: call.arguments, before, result, after: snapshot(exports) };
    if (result.outcome === 'Returned') {
      try { item.decoded = decode(exports, result.value, call.result_type, request.types); }
      catch (error) { item.memory_failure = error.message; }
      if (request.types[call.result_type].cell) {
        item.release = invoke(exports, '__heap_release', [result.value]);
      }
      item.cleaned = snapshot(exports);
    }
    observations.push(item);
    if (result.outcome !== 'Returned') break;
  }
  return { mode: 'observe', observations };
}

function persistent(exports, request) {
  requiredHeap(exports);
  const initial = snapshot(exports);
  let completed = 0;
  const samples = [];
  for (let i = 0; i < request.count; i++) {
    const result = invoke(exports, request.export, request.arguments);
    const state = snapshot(exports);
    if (result.outcome !== 'Returned' || result.value !== request.tag || state.live !== 0 || state.pending !== 0) {
      return { mode: 'persistent', completed, failure: { result, state }, initial };
    }
    completed++;
    if (i === 0 || i === request.count - 1) samples.push(state);
  }
  return { mode: 'persistent', completed, initial, samples, final: snapshot(exports) };
}

function releaseBoundary(exports, request) {
  requiredHeap(exports);
  const made = invoke(exports, request.export, []);
  require(made.outcome === 'Returned', 'release fixture did not return');
  const decoded = decode(exports, made.value, request.result_type, request.types);
  const steps = [];
  function step(name, args) {
    const result = invoke(exports, name, args);
    const record = { name, arguments: args, result, state: snapshot(exports) };
    steps.push(record);
    return record;
  }
  const initial = snapshot(exports);
  step('__heap_stack_limit', [1]);
  step('__heap_enqueue', [made.value]);
  step('__heap_clean', [0]);
  step('__heap_clean', [1]);
  step('__heap_clean', [10000]);
  step('__heap_stack_limit', [4096]);
  step('__heap_clean', [10000]);
  return { mode: 'release-boundary', decoded, initial, steps };
}

function countBoundary(exports, request) {
  requiredHeap(exports);
  const made = invoke(exports, request.export, []);
  require(made.outcome === 'Returned', 'count fixture did not return');
  const initial = decode(exports, made.value, request.result_type, request.types);
  const before = snapshot(exports);
  const limit = invoke(exports, '__heap_rc_limit', [1]);
  const share = invoke(exports, '__heap_share', [made.value]);
  const after = decode(exports, made.value, request.result_type, request.types);
  const state = snapshot(exports);
  const restore = invoke(exports, '__heap_rc_limit', [2147483647]);
  const release = invoke(exports, '__heap_release', [made.value]);
  return { mode: 'count-boundary', initial, before, limit, share, after, state, restore, release,
    final: snapshot(exports) };
}

async function main() {
  const [module, requestPath] = process.argv.slice(2);
  require(module && requestPath, 'expected module and request JSON');
  const request = JSON.parse(await readFile(requestPath, 'utf8'));
  const exports = await instantiate(module);
  const handlers = { observe, persistent, 'release-boundary': releaseBoundary, 'count-boundary': countBoundary };
  const handler = handlers[request.mode ?? 'observe'];
  require(handler, 'unknown request mode');
  process.stdout.write(JSON.stringify(handler(exports, request)) + '\n');
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  main().catch(error => { process.stderr.write(`HostFailure\towned-wasm\t${error.message}\n`); process.exitCode = 5; });
}
