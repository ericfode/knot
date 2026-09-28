// Transport and dispatch only. The unchanged generic WGSL owns all transitions.
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {dirname, resolve} from 'node:path';
import {createHash} from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const runtime = resolve(root, 'research/adaptive-tasks/runtime2');
let gpu, device;
const buffers = [], errors = [];
class Boundary extends Error {
  constructor(status, reason) { super(reason); this.status = status; }
}
async function webgpu() {
  const locations = [resolve(root, 'research/adaptive-tasks/gpu/package.json'), resolve(root, '.local/gpu-2/package.json')];
  if (process.env.WEBGPU_NODE_MODULES) locations.unshift(resolve(process.env.WEBGPU_NODE_MODULES, '../package.json'));
  for (const location of locations) {
    let path;
    try { path = createRequire(location).resolve('webgpu'); }
    catch (error) { if (error.code === 'MODULE_NOT_FOUND') continue; throw error; }
    return import(pathToFileURL(path).href);
  }
  throw new Boundary('HostFailure', 'webgpu dependency unavailable');
}
async function main() {
  let input = '';
  for await (const chunk of process.stdin) input += chunk;
  const {bundle, words, layout, quantum, maxRounds} = JSON.parse(input);
  const {create, globals} = await webgpu(); Object.assign(globalThis, globals);
  gpu = create(['backend=metal']);
  const adapter = await gpu.requestAdapter({powerPreference: 'high-performance'});
  if (!adapter || adapter.info.isFallbackAdapter !== false) throw new Boundary('HostFailure', 'real Metal adapter unavailable');
  device = await adapter.requestDevice({requiredLimits: {
    maxStorageBufferBindingSize: adapter.limits.maxStorageBufferBindingSize,
    maxBufferSize: adapter.limits.maxBufferSize,
  }});
  device.addEventListener('uncapturederror', event => errors.push(event.error.message));
  const limit = Math.min(device.limits.maxBufferSize, device.limits.maxStorageBufferBindingSize, bundle.config.maxStorageBytes);
  const code = new Uint32Array(bundle.instructions.flat());
  if (layout.bytes > limit || Math.max(4, code.byteLength) > limit) throw new Boundary('Exhausted', 'adapter-storage');
  const shader = await readFile(resolve(runtime, 'runtime.wgsl'), 'utf8');
  const module = device.createShaderModule({code: shader});
  const compilation = await module.getCompilationInfo();
  if (compilation.messages.some(m => m.type === 'error')) throw new Boundary('InternalFailure', 'generic WGSL validation');
  const bindLayout = device.createBindGroupLayout({entries: [
    ...[0, 1, 2].map(binding => ({binding, visibility: GPUShaderStage.COMPUTE, buffer: {type: binding === 0 ? 'read-only-storage' : 'storage'}})),
    {binding: 3, visibility: GPUShaderStage.COMPUTE, buffer: {type: 'uniform', minBindingSize: 16}},
    {binding: 4, visibility: GPUShaderStage.COMPUTE, buffer: {type: 'read-only-storage'}},
  ]});
  const pipelineLayout = device.createPipelineLayout({bindGroupLayouts: [bindLayout]});
  device.pushErrorScope('validation');
  const pipelines = await Promise.all(['run', 'publish'].map(entryPoint =>
    device.createComputePipelineAsync({layout: pipelineLayout, compute: {module, entryPoint}})));
  const pipelineError = await device.popErrorScope();
  if (pipelineError) throw new Boundary('InternalFailure', pipelineError.message);
  function buffer(size, usage, data) {
    const value = device.createBuffer({size, usage}); buffers.push(value);
    if (data?.byteLength) device.queue.writeBuffer(value, 0, data);
    return value;
  }
  const storage = GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST;
  const a = buffer(layout.bytes, storage, new Uint32Array(words));
  const b = buffer(layout.bytes, storage), work = buffer(layout.bytes, storage);
  const program = buffer(Math.max(4, code.byteLength), storage, code);
  const step = buffer(16, GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST, new Uint32Array([quantum, 0, 0, 0]));
  const readback = [0, 1].map(() => buffer(layout.bytes, GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ));
  const groups = [[a, b], [b, a]].map(([from, to]) => device.createBindGroup({layout: bindLayout, entries: [
    {binding: 0, resource: {buffer: from}}, {binding: 1, resource: {buffer: work}},
    {binding: 2, resource: {buffer: to}}, {binding: 3, resource: {buffer: step}},
    {binding: 4, resource: {buffer: program}},
  ]}));
  let result, rounds = 0;
  device.pushErrorScope('validation');
  while (rounds < maxRounds) {
    const encoder = device.createCommandEncoder();
    for (const pipeline of pipelines) {
      const pass = encoder.beginComputePass(); pass.setPipeline(pipeline);
      pass.setBindGroup(0, groups[rounds % 2]); pass.dispatchWorkgroups(1); pass.end();
    }
    encoder.copyBufferToBuffer(work, 0, readback[0], 0, layout.bytes);
    encoder.copyBufferToBuffer(rounds % 2 === 0 ? b : a, 0, readback[1], 0, layout.bytes);
    device.queue.submit([encoder.finish()]);
    await Promise.all(readback.map(back => back.mapAsync(GPUMapMode.READ)));
    const raw = readback.map(back => { const data = new Uint32Array(back.getMappedRange().slice(0)); back.unmap(); return data; });
    if (!raw[0].every((word, i) => word === raw[1][i])) throw new Boundary('InternalFailure', 'publication differs from work state');
    result = Array.from(raw[1]); rounds++;
    if (result[25] >= 2 || result[21] !== 0) break;
  }
  await device.queue.onSubmittedWorkDone();
  const dispatchError = await device.popErrorScope();
  if (dispatchError || errors.length) throw new Boundary('HostFailure', dispatchError?.message ?? errors.join('; '));
  return {words: result, rounds, dispatches: 2 * rounds, observations: 2 * rounds, deviceExecution: true,
    ...(result[25] < 2 && result[21] === 0 ? {exhausted: 'round-budget'} : {}),
    shaderSha256: createHash('sha256').update(shader).digest('hex'),
    adapter: {backend: 'metal', vendor: adapter.info.vendor, architecture: adapter.info.architecture,
      device: adapter.info.device, description: adapter.info.description, isFallbackAdapter: adapter.info.isFallbackAdapter},
    limits: {maxStorageBufferBindingSize: device.limits.maxStorageBufferBindingSize, maxBufferSize: device.limits.maxBufferSize}};
}
try {
  const result = await main();
  console.log(JSON.stringify(result));
} catch (error) {
  console.log(JSON.stringify({status: error.status ?? 'HostFailure', reason: error.message}));
  process.exitCode = ({Invalid: 2, Unsupported: 3, Exhausted: 4, HostFailure: 5, InternalFailure: 6})[error.status] ?? 5;
} finally {
  if (device) {
    await device.queue.onSubmittedWorkDone().catch(() => {});
    for (const buffer of buffers) buffer.destroy();
    device.destroy();
  }
  gpu = null;
}
