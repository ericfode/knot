// Runtime adapters only; the pinned foreign body's query runs unmodified.
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const [source, encoded] = process.argv.slice(2);
const context = vm.createContext({
  require: createRequire(import.meta.url), process, Buffer,
  io_bytes: text => Buffer.from(text),
  io_done: value => [0, Number(value)],
  io_fail: code => [code, 0],
  io_eff() {}, CID: value => value, inspect: 'inspect',
});
vm.runInContext(fs.readFileSync(source, 'utf8'), context);
context.input = Buffer.from(encoded, 'hex').toString('utf8');
console.log(JSON.stringify(vm.runInContext('knot_path_identity(input)', context)));
