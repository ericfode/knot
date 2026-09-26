// Checked library generation by the pinned compiler, with no alternate backend.
import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
import {load} from '../../.toolchain/bend-2.0.29-574b6d3/bend2/main.ts';
const [, , source, output] = process.argv;
const result: any = await load(pathToFileURL(source).href, {}, () => {
  throw new Error('Only a Bend source file is accepted');
});
writeFileSync(output, result.source);
