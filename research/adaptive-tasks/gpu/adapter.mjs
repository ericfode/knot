import { create, globals } from 'webgpu';
Object.assign(globalThis, globals);
let gpu = create(['backend=metal']);
const adapter = await gpu.requestAdapter({ powerPreference: 'high-performance' });
if (!adapter || adapter.info.isFallbackAdapter) throw new Error('Hardware Metal adapter unavailable');
const device = await adapter.requestDevice();
console.log(JSON.stringify({
  vendor: adapter.info.vendor, architecture: adapter.info.architecture,
  device: adapter.info.device, description: adapter.info.description,
  isFallbackAdapter: adapter.info.isFallbackAdapter,
  maxStorageBufferBindingSize: device.limits.maxStorageBufferBindingSize,
  maxComputeWorkgroupsPerDimension: device.limits.maxComputeWorkgroupsPerDimension,
}));
device.destroy();
gpu = null;
