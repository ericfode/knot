#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { LOCAL, ROOT } from './lib/system.mjs';

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

export function runtimePrograms() {
  const fixed = JSON.parse(readFileSync(path.join(ROOT, 'bench/expectations.json'), 'utf8'));
  const flag = 'type Flag is Data:\n  Off{}\n  On{}\n';
  const programs = [];
  for (const size of fixed.sizes) {
    const add = (family, profile, source, constructor) => programs.push({
      name: `${family}-${size}`, family, size, profile, source, entry: 'main', args: [],
      expected: fixed[family][size], constructor,
      program: `.local/bench/generated/${family}-${size}.bend`,
    });
    const peano = 'Succ{'.repeat(size + 1) + 'Zero{}' + '}'.repeat(size + 1);
    add('peano', 'knot-fields-wasm-1', flag +
      'type Peano is Data:\n  Zero{}\n  Succ{pred: Peano}\n' +
      'def parity(n: Peano) -> Flag:\n  match n:\n    case Zero{}: Off{}\n' +
      '    case Succ{p}:\n      match p:\n        case Zero{}: On{}\n        case Succ{q}: parity(q)\n' +
      `def main() -> Flag:\n  parity(${peano})\n`, 'On');
    // Chunks bound surface nesting without shortening the runtime list.
    const chunks = ['def cells0() -> Cells:\n  Empty{}\n'];
    for (let part = 1; part <= size / 32; part++) {
      const start = size - part * 32;
      const cells = Array.from({ length: 32 }, (_, j) => `Cell{${start + j === size - 1 || j % 2 === 0 ? 'On' : 'Off'}{},`).join('') +
        `cells${part - 1}()` + '}'.repeat(32);
      chunks.push(`def cells${part}() -> Cells:\n  ${cells}\n`);
    }
    add('cells', 'knot-fields-wasm-1', flag +
      'type Cells is Type:\n  Empty{}\n  Cell{value: Flag, tail: Cells}\n' +
      'def last(xs: Cells, value: Flag) -> Flag:\n  match xs:\n    case Empty{}: value\n' +
      '    case Cell{head,tail}: last(tail,head)\n' +
      chunks.join('') + `def main() -> Flag:\n  last(cells${size / 32}(),Off{})\n`, 'On');
    const tags = Array.from({ length: size }, (_, i) => `  T${i}{}`).join('\n');
    const arms = Array.from({ length: size }, (_, i) => `    case T${i}{}: T${(i + 1) % size}{}`).join('\n');
    add('wide', 'knot-enum-1', `type Tag is Type:\n${tags}\ndef rotate(x: Tag) -> Tag:\n  match x:\n${arms}\n` +
      `def main() -> Tag:\n  rotate(T${size - 2}{})\n`, `T${size - 1}`);
    const calls = Array.from({ length: size }, (_, i) => `def step${i + 1}(x: Flag) -> Flag:\n  step${i}(flip(x))\n`).join('');
    add('inline', 'knot-enum-1', flag +
      'def flip(x: Flag) -> Flag:\n  match x:\n    case Off{}: On{}\n    case On{}: Off{}\n' +
      'def step0(x: Flag) -> Flag:\n  x\n' + calls + `def main() -> Flag:\n  step${size}(On{})\n`, 'On');
  }
  return programs;
}

export function generate(family = 'scaling') {
  const directory = path.join(LOCAL, 'generated');
  mkdirSync(directory, { recursive: true });
  const programs = family === 'runtime' ? runtimePrograms() : generatedPrograms();
  for (const program of programs) writeFileSync(path.join(directory, `${program.name}.bend`), program.source);
  return programs;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(`Generated ${generate(process.argv.includes('--runtime') ? 'runtime' : 'scaling').length} deterministic programs under .local/bench/generated/`);
}
