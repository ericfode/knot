#!/usr/bin/env node
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { LOCAL } from './lib/system.mjs';

export const SIZES = [16, 64, 128];

// Formulas are cross-checks for the independent evaluator, never inferred from
// emitted Wasm. No randomness, timestamps, imports, fields, or recursion.
export function generatedPrograms() {
  const programs = [];
  for (const size of SIZES) {
    const tags = Array.from({ length: size }, (_, i) => `  T${i}{}`).join('\n');
    programs.push({ name: `enum-${size}`, entry: 'identity', args: [size - 1], expected: size - 1,
      source: `type Tag is Type:\n${tags}\n\ndef identity(x: Tag) -> Tag:\n  x\n` });
    const arms = Array.from({ length: size }, (_, i) => `    case T${i}{}: T${(i + 1) % size}{}`).join('\n');
    programs.push({ name: `match-${size}`, entry: 'rotate', args: [size - 2], expected: size - 1,
      source: `type Tag is Type:\n${tags}\n\ndef rotate(x: Tag) -> Tag:\n  match x:\n${arms}\n` });
    const calls = Array.from({ length: size }, (_, i) =>
      `def step${i + 1}(x: Flag) -> Flag:\n  step${i}(flip(x))\n`).join('\n');
    programs.push({ name: `calls-${size}`, entry: `step${size}`, args: [1], expected: 1,
      source: 'type Flag is Type:\n  Off{}\n  On{}\n\ndef flip(x: Flag) -> Flag:\n  match x:\n' +
        '    case Off{}: On{}\n    case On{}: Off{}\n\ndef step0(x: Flag) -> Flag:\n  x\n\n' + calls });
  }
  return programs.map(p => ({ ...p, program: `.local/bench/generated/${p.name}.bend` }));
}

export function generate() {
  const directory = path.join(LOCAL, 'generated');
  mkdirSync(directory, { recursive: true });
  const programs = generatedPrograms();
  for (const program of programs) writeFileSync(path.join(directory, `${program.name}.bend`), program.source);
  return programs;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(`Generated ${generate().length} deterministic programs under .local/bench/generated/`);
}
