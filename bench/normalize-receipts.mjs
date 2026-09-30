#!/usr/bin/env node
import { readFileSync, realpathSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { gunzipSync, gzipSync } from 'node:zlib';
import { receiptJSON } from './lib/receipt.mjs';
import { ROOT } from './lib/system.mjs';

// Explicit bench-owned receipt paths only; never scan fixtures or other gates.
const { values, positionals } = parseArgs({ options: { check: { type: 'boolean' } }, allowPositionals: true });
if (!positionals.length) throw new Error('Usage: node bench/normalize-receipts.mjs [--check] bench/receipts/FILE.json[.gz] ...');
for (const name of positionals) {
  const file = path.resolve(ROOT, name);
  if (!/^.+\.json(?:\.gz)?$/.test(file) || !realpathSync(file).startsWith(path.join(ROOT, 'bench/receipts') + path.sep)) {
    throw new Error(`Not a bench-owned JSON receipt: ${name}`);
  }
  const compressed = file.endsWith('.gz');
  const before = readFileSync(file);
  const payload = compressed ? gunzipSync(before) : before;
  const after = Buffer.from(receiptJSON(JSON.parse(payload)));
  if (payload.equals(after)) {
    console.log(`${name}: portable`);
  } else if (values.check) {
    console.error(`${name}: nonportable`);
    process.exitCode = 1;
  } else {
    writeFileSync(file, compressed ? gzipSync(after) : after);
    console.log(`${name}: normalized`);
  }
}
