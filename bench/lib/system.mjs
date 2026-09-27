import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('../../', import.meta.url));
export const LOCAL = path.join(ROOT, '.local/bench');
export const SEED = path.join(ROOT, '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts');
// The same seed entry as scripts/bend-reference; Bun's automatic dotenv loading
// and the seed's daily network version check are disabled in this harness.
export const SEED_COMMAND = ['bun', '--no-env-file', SEED];
export const childEnv = { ...process.env, BEND_NO_TELEMETRY: '1', NODE_OPTIONS: '', CC: process.env.CC || 'clang' };
export const hash = data => createHash('sha256').update(data).digest('hex');
export const fileHash = file => hash(readFileSync(file));

export function run(argv, { timeout = 120000 } = {}) {
  const start = process.hrtime.bigint();
  const result = spawnSync(argv[0], argv.slice(1).map(String), {
    cwd: ROOT, env: childEnv, encoding: 'utf8', timeout, maxBuffer: 4 * 1024 * 1024,
  });
  const ms = Number(process.hrtime.bigint() - start) / 1e6;
  if (result.error || result.status !== 0) {
    throw new Error(`${argv.join(' ')}: ${result.error?.message || `exit ${result.status}, signal ${result.signal}`}` +
      `\n${result.stderr || result.stdout || ''}`);
  }
  return { argv: argv.map(String), ms, stdout: result.stdout.trim(), stderr: result.stderr.trim() };
}

export function hashes(directory, accept) {
  return Object.fromEntries(readdirSync(path.join(ROOT, directory), { recursive: true })
    .filter(accept).sort().map(name => [`${directory}/${name}`, fileHash(path.join(ROOT, directory, name))]));
}

export function sourceHashes() {
  return hashes('src', name => !name.includes('/') && name.endsWith('.bend'));
}

export function harnessHashes() {
  return hashes('bench', name => name.endsWith('.mjs') && !name.startsWith('tests/'));
}

export function fingerprint() {
  const contract = JSON.parse(readFileSync(path.join(ROOT, 'src/CONTRACT.json'), 'utf8'));
  const seedSources = hashes('.toolchain/bend-2.0.29-574b6d3/bend2', name => /\.(ts|js|bend|c|h)$/.test(name));
  const ccVersion = run([childEnv.CC, '--version']).stdout;
  if (!/clang version (\d+)/.test(ccVersion) || Number(ccVersion.match(/clang version (\d+)/)[1]) < 14) {
    throw new Error('CC must name clang >= 14, matching the native seed build');
  }
  return {
    machine: { cpuModel: os.cpus()[0]?.model || 'unknown', logicalCpus: os.cpus().length,
      platform: os.platform(), arch: os.arch(), release: os.release(), osVersion: os.version(), totalMemory: os.totalmem() },
    tools: { node: process.version, bun: run(['bun', '--version']).stdout,
      seed: { version: run([...SEED_COMMAND, 'version']).stdout, declaredCommit: contract.seed.commit,
        sourceSha256: hash(JSON.stringify(seedSources)) }, cc: { command: childEnv.CC, version: ccVersion } },
    git: { commit: run(['git', 'rev-parse', 'HEAD']).stdout,
      dirty: run(['git', 'status', '--porcelain', '--untracked-files=normal']).stdout.length > 0 },
    sourceHashes: sourceHashes(), harnessHashes: harnessHashes(),
    controls: { BEND_NO_TELEMETRY: '1', NODE_OPTIONS: '', bunNoEnvFile: true },
  };
}
