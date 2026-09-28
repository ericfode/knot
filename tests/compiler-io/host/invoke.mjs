// Receipt channel stays outside the guest sandbox and its observable streams.
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
process.exitCode = 5;
const [host, modulePath, sandbox, argumentsPath, receipt] = process.argv.slice(2);
const {runIO} = await import(pathToFileURL(host));
const args = JSON.parse(fs.readFileSync(argumentsPath, 'utf8')).map(a =>
  typeof a === 'string' ? a : Buffer.from(a.hex, 'hex'));
const outcome = await runIO({modulePath, sandbox, args});
fs.writeFileSync(receipt, JSON.stringify(outcome));
process.exitCode = outcome.exit;
