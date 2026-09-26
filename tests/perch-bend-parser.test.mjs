import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { analyzeBendSource, BEND_PARSER_PROFILE } from '../scripts/perch-bend.mjs';
import * as parser from '../vendor/bend-parser/bend.mts';
import baseSource from '../vendor/bend-parser/base-source.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const sourceSlice = (source, location) => Buffer.from(source).subarray(location.start.byte, location.end.byte).toString();
const analyze = async (source) => {
  const result = await analyzeBendSource(source);
  assert.equal(result.parser_status, 'parsed', result.parser_message);
  return result;
};

test('actual pinned parser, provenance, and Base source are available without the toolchain', () => {
  const pin = JSON.parse(fs.readFileSync(new URL('../vendor/bend-parser/upstream.json', import.meta.url), 'utf8'));
  assert.equal(pin.commit, '574b6d39a235b539eb19a5c532993a0abb3d11ad');
  assert.equal(createHash('sha256').update(baseSource).digest('hex'), pin.files['bend2/base.bend']);
  assert.equal(typeof parser.parse_book, 'function');
  assert.equal(typeof parser.parse_term, 'function');
  assert.equal('book_load' in parser, false);
  assert.equal('BEND_HUB' in parser, false);
});

test('multiline signatures, quantity binders, ADTs, nested matches, unsafe definitions, and local calls', async () => {
  const source = `import Base

type Box<q, -A: Kind(q)> is Kind(q):
  Box{value: A}

def identity(
  -A: Data,
  +value: A
) -> A:
  value

@unsafe
def unbox(-A: Data, value: Box<&2,A>) -> A:
  match value:
    case Box{+inner}:
      match inner:
        case result: identity(A,result)

def zero?() -> U32: 0
`;
  const result = await analyze(source);
  assert.deepEqual(result.declarations.map((entry) => entry.name), ['identity', 'unbox', 'zero']);
  assert.equal(sourceSlice(source, result.declarations[0].location), 'def identity(\n  -A: Data,\n  +value: A\n) -> A:\n  value');
  assert.match(sourceSlice(source, result.declarations[1].location), /^@unsafe\ndef unbox/);
  assert.equal(result.declarations[0].line, 6);
  assert.equal(result.declarations[0].end_line, 10);
  assert.ok(result.references.some((ref) => ref.kind === 'call' && ref.name === 'identity' && ref.source === 'bend:unbox'));
  assert.ok(result.declarations.every((entry) => entry.metrics === null));
  assert.equal(result.metrics, null);
  assert.equal(result.parser_metadata.profile, BEND_PARSER_PROFILE);
  assert.equal(result.parser_metadata.typechecked, false);
});

test('static call/value distinction includes zero-argument calls and excludes bound dynamic calls', async () => {
  const result = await analyze(`import Base
def target() -> U32: 1
def main(f: U32 -> U32) -> U32:
  saved = target
  x = target()
  f(x)
`);
  const refs = result.references.filter((ref) => ref.source === 'bend:main' && ref.name === 'target');
  assert.deepEqual(refs.map((ref) => ref.kind), ['value', 'call']);
  assert.ok(!result.references.some((ref) => ref.name === 'f' || ref.name === 'saved' || ref.name === 'x'));
});

test('law and local fill have one target, separate law range, and no intervening declaration leakage', async () => {
  const source = `import Base
law equal:
  for +n: U32
  {n == n : U32}
def other() -> U32: 7
# proof follows

def equal(n): {==}
`;
  const result = await analyze(source);
  const decl = result.declarations.find((entry) => entry.name === 'equal');
  assert.equal(result.declarations.filter((entry) => entry.name === 'equal').length, 1);
  assert.equal(decl.syntax_kind, 'bend_law_definition');
  assert.equal(sourceSlice(source, decl.location), 'def equal(n): {==}');
  assert.equal(sourceSlice(source, decl.law_location), 'law equal:\n  for +n: U32\n  {n == n : U32}');
  const shifted = await analyze('# additional comment\n' + source);
  assert.equal(shifted.declarations.find((entry) => entry.name === 'equal').id, decl.id);
});

test('UTF-8 byte offsets and columns preserve Unicode strings/comments and exclude trailing trivia', async () => {
  const source = '# 🦀\nimport Base\ndef hello() -> String: "é😀"\n# separate\ndef main() -> U32:\n  s = "😀"; U32.add(1,2) # trailing\n';
  const result = await analyze(source);
  assert.equal(sourceSlice(source, result.declarations[0].location), 'def hello() -> String: "é😀"');
  assert.equal(result.declarations[0].location.start.byte, Buffer.byteLength('# 🦀\nimport Base\n'));
  assert.equal(sourceSlice(source, result.declarations[1].location), 'def main() -> U32:\n  s = "😀"; U32.add(1,2)');
  const ref = result.references.find((entry) => entry.name === 'U32.add');
  assert.equal(ref.kind, 'call');
  assert.equal(ref.column, Buffer.byteLength('  s = "😀"; ') + 1);
  assert.equal(sourceSlice(source, ref.location), 'U32.add');
});

test('imported laws, constructor patterns, template calls parse with honest dependency diagnostics', async () => {
  const source = `import Base
import ./not-present.bend as M
import package-name@1.2.3.4/LAWS.bend as L

def L.proof(n):
  match n:
    case M.Zero{}: {==}
    case M.More{tail}: L.proof(tail)

def total(n: M.Number) -> U32:
  M.fold(~U32,~(x => x),n)
`;
  const result = await analyze(source);
  assert.deepEqual(result.declarations.map((entry) => entry.name), ['L.proof', 'total']);
  assert.ok(result.diagnostics.some((entry) => entry.message.includes('law existence')));
  assert.ok(result.diagnostics.some((entry) => entry.message.includes('constructor and datatype arities')));
  const imported = result.references.find((entry) => entry.kind === 'import' && entry.alias === 'M');
  assert.equal(imported.module, './not-present.bend');
  assert.equal(imported.imported_name, '*');
  assert.equal(sourceSlice(source, imported.location), './not-present.bend');
  assert.ok(result.references.some((entry) => entry.name === 'M.fold' && entry.kind === 'call'));
  assert.ok(result.references.some((entry) => entry.name === 'L.proof' && entry.kind === 'call'));
});

test('dependency-context failure differs from malformed local syntax', async () => {
  const external = await analyzeBendSource('import Base\nimport ./missing.bend as M\ndef t() -> Type: +M.Box<U32>\n');
  assert.equal(external.parser_status, 'unsupported');
  assert.equal(external.declarations.length, 0);
  const local = await analyzeBendSource('import Base\nimport ./missing.bend as M\ndef t() -> Type: +Bogus<U32>\n');
  assert.equal(local.parser_status, 'parse-error');
});

test('malformed Bend is rejected with no successful partial declaration list', async () => {
  const malformed = [
    'def f() -> U32 0',
    'def f(x): x',
    'def f() -> U32: 0\ndef f() -> U32: 1',
    'def f() -> String: "unterminated',
    'def f() -> U32: case x: 0',
    'import ./missing.bend',
    'import ./missing.txt as M',
    'import package@1.2.3/main.bend as M',
    'import ./missing.bend as M\nimport ./different.bend as M',
    'import Base\ndef f(n: Nat) -> Nat:\n  match n:\n    case Succ{}: 0n',
    'import Base\ndef f(n: Nat) -> Nat:\n  match n:\n    case Missing{}: 0n',
    'import ./missing.bend as L\ndef L.proof(n: U32): {==}',
    'import ./missing.bend as L\ndef L.proof(n): ???',
    'import Base\n@unknown def f() -> U32: 0',
    'import Base\ndef café() -> U32: 0',
  ];
  for (const source of malformed) {
    const result = await analyzeBendSource(source);
    assert.equal(result.parser_status, 'parse-error', source);
    assert.equal(result.declarations.length, 0, source);
    assert.ok(result.diagnostics.some((entry) => entry.kind === 'syntax'), source);
  }
});

test('analysis does not load imports, foreign code, network, or caches', async (t) => {
  let effects = 0;
  const forbidden = () => { effects++; throw new Error('forbidden side effect'); };
  for (const name of ['readFileSync', 'writeFileSync', 'realpathSync', 'existsSync', 'mkdirSync']) t.mock.method(fs, name, forbidden);
  t.mock.method(globalThis, 'fetch', forbidden);
  const result = await analyze(`import Base
import 0x0123456789abcdef0123456789abcdef/main.bend as M
import named@1.2.3.4/remote.bend as L

def L.proof(): {==}
def foreign() -> IO(Unit):
  import "never-execute.js"
`);
  assert.equal(result.declarations.length, 2);
  assert.equal(effects, 0);
});

test('every current nonignored package and research Bend source parses with bounded, exact source ranges', async () => {
  const paths = execFileSync('rg', ['--files', 'packages', 'research', '-g', '*.bend'], { cwd: root, encoding: 'utf8' }).trim().split('\n');
  assert.ok(paths.length >= 90, `expected meaningful corpus coverage, got ${paths.length}`);
  let declarationCount = 0;
  for (const path of paths) {
    const source = fs.readFileSync(root + path, 'utf8');
    const result = await analyzeBendSource(source);
    assert.equal(result.parser_status, 'parsed', `${path}: ${result.parser_message}`);
    assert.equal(new Set(result.declarations.map((entry) => entry.id)).size, result.declarations.length, path);
    for (const decl of result.declarations) {
      assert.ok(decl.location.start.byte < decl.location.end.byte, path);
      assert.ok(decl.location.end.byte <= Buffer.byteLength(source), path);
      assert.match(sourceSlice(source, decl.location), /^(?:@unsafe\s+)?(?:def|law)\s/, path);
      assert.equal(decl.line, decl.location.start.line, path);
      assert.equal(decl.end_line, decl.location.end.line, path);
    }
    declarationCount += result.declarations.length;
  }
  assert.ok(declarationCount >= 1000, `expected meaningful method coverage, got ${declarationCount}`);
});
