"""Freeze or verify the literals fixture suite against the pinned seed.

    python3 tests/compiler-literals/regen.py          # verify (default)
    python3 tests/compiler-literals/regen.py --write  # regenerate expectations.json

Verification re-runs the pinned seed on every fixture and entry call, rebuilds
expectations.json in memory from PLAN and those observations, and fails on any
byte difference: seed or tool drift, an edited fixture, a fixture added or
removed, a changed plan entry, or a changed seed result. --write builds the
document twice and writes nothing unless both builds agree.

Expectations come only from the seed and from the reviewed literals in PLAN.
Nothing here runs or reads Knot.
"""
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURES = HERE / 'fixtures'
EXPECTATIONS = HERE / 'expectations.json'
CALLS = ROOT / '.local/compiler-literals/calls'
SEED_DIR = '.toolchain/bend-2.0.29-574b6d3'
SEED = ['bun', SEED_DIR + '/bend2/main.ts']
SEED_FILES = ['bend2/main.ts', 'bend2/bend.ts', 'bend2/base.bend']
ENV = {'BEND_NO_TELEMETRY': '1'}
TIMEOUT = 120

AGREE = {'outcome': 'agree', 'exit': 0,
         'meaning': "checks; the evaluator and the Wasm module return each call's seed tag"}
INVALID = {'outcome': 'Invalid', 'exit': 2, 'artifact': False, 'phase_code': 'open',
           'meaning': 'the seed rejects this book; Knot rejects it as Invalid and emits nothing'}


def unsupported(phase, code, why):
    return {'outcome': 'Unsupported', 'exit': 3, 'artifact': False,
            'diagnostic_prefix': f'Unsupported\t{phase}\t{code}\t', 'justification': why}


OPERATOR = ('Operator sugar is outside the literals increment, which reaches primitives through '
            'literals and Base calls; vetoable before implementation starts (FIXTURES.md).')

# The reviewed literal plan: fixture -> (feature, kind, covers, entries, Knot).
# Each entry is called on every combination of its enum parameters' constructors;
# main() is always called when the seed accepts the book.
PLAN = {
    'u32-literals': ('u32', 'positive', 'decimal literals 0 and 4294967295; 007 reads as 7',
                     ['is_max', 'is_seven'], AGREE),
    'u32-wraparound': ('u32', 'edge', 'add/sub/mul wrap modulo 2^32',
                       ['is_zero', 'is_max', 'is_one'], AGREE),
    'u32-unsigned-order': ('u32', 'edge', 'cmp and is_lt are unsigned: 2147483648 > 0',
                           ['compare', 'below'], AGREE),
    'u32-division': ('u32', 'edge', 'unsigned div/mod; x / 0 == 0 and x % 0 == x',
                     ['exact', 'is_zero'], AGREE),
    'u32-shifts': ('u32', 'edge', 'a shift by 32 clears every bit; shr is logical',
                   ['exact', 'is_zero'], AGREE),
    'u32-pattern': ('u32', 'positive', 'U32 literal patterns with a binder default',
                    ['classify'], AGREE),
    'u32-pattern-first-match': ('u32', 'edge', 'overlapping literal arms: the first match wins',
                                ['first_arm', 'wildcard_first'], AGREE),
    'u32-pattern-missing-default': ('u32', 'negative', 'literal arms without a default arm',
                                    [], INVALID),
    'u32-literal-overflow': ('u32', 'negative', 'the literal 4294967296', [], INVALID),
    'u32-hex': ('u32', 'negative', 'the hexadecimal literal 0xFF', [], INVALID),
    'u32-operators': ('u32', 'knot', 'annotated operators (a + b : U32) and (a < b : U32)',
                      ['check'], unsupported('parse', 'operator', OPERATOR)),
    'u32-operator-unannotated': (
        'u32', 'negative', 'an operator without a (.. : T) annotation', [],
        unsupported('parse', 'operator',
                    'Seed-invalid, but Knot does not check operator sugar in this increment; '
                    'D4 forbids an Invalid claim about a form it cannot check.')),
    'nat-literals': ('nat', 'positive', 'Nat literals 0n to 65536n, past 256n, and folded n+m',
                     ['agrees', 'is_zero', 'folded'], AGREE),
    'nat-recursion': ('nat', 'positive', 'structural recursion through 0n / 1n+p, depth 65536',
                      ['parity_of', 'deep'], AGREE),
    'nat-pattern-offset': ('nat', 'edge', '2n+p recursion; 256n+p is the largest offset pattern',
                           ['parity_of', 'at_least_256'], AGREE),
    'nat-pattern-offset-limit': ('nat', 'negative', '257n+p is Nat.add, not a pattern', [], INVALID),
    'nat-arithmetic': ('nat', 'edge', 'Nat.sub saturates at 0n', ['is_zero'], AGREE),
    'nat-literal-overflow': ('nat', 'negative', 'the literal 4294967296n', [], INVALID),
    'nat-u32-mismatch': ('nat', 'negative', 'a bare numeral is U32, never Nat', [], INVALID),
    'literal-without-base': ('base', 'negative', 'a literal without import Base', [], INVALID),
    'char-escapes': ('char', 'positive', "escapes \\n \\t \\r \\0 \\\\ \\' \\\"",
                     ['exact', 'is_space'], AGREE),
    'char-unicode-escapes': ('char', 'edge', '\\u{..}: case, padding, surrogates, past U+10FFFF',
                             ['exact', 'is_a'], AGREE),
    'char-lexer-traps': ('char', 'edge', "''' is an apostrophe; '\"', '#' and ' '",
                         ['exact', 'is_space'], AGREE),
    'char-pattern': ('char', 'positive', 'Char literal patterns with a wildcard default',
                     ['classify'], AGREE),
    'char-empty': ('char', 'negative', "the empty Char literal ''", [], INVALID),
    'char-bad-escape': ('char', 'negative', 'the unknown escape \\q', [], INVALID),
    'char-unicode-escape-width': ('char', 'negative', 'nine hex digits in \\u{..}', [], INVALID),
    'string-equality': ('string', 'positive', 'String.eq over literals and the empty string',
                        ['equal'], AGREE),
    'string-append': ('string', 'positive', 'String.append; "" is its identity on both sides',
                      ['spells_ab'], AGREE),
    'string-escapes': ('string', 'positive', 'escapes inside strings; "\\\\n" is two Chars',
                       ['check'], AGREE),
    'string-nul': ('string', 'edge', 'NUL inside a String is an ordinary Char', ['check'], AGREE),
    'string-unicode': ('string', 'edge', 'scalar counts; escaped surrogates stay two Chars',
                       ['check'], AGREE),
    'string-lexer-traps': ('string', 'edge', "# and ' inside strings; a raw newline is kept",
                           ['check'], AGREE),
    'string-pattern': ('string', 'positive', "a String literal pattern beside SCon{'a', t}",
                       ['classify'], AGREE),
    'string-unclosed': ('string', 'negative', 'a String literal without its closing quote',
                        [], INVALID),
    'string-raw-non-ascii': ('string', 'knot', 'raw UTF-8 text inside a String literal', [],
                             unsupported('lex', 'non-ascii',
                                         'Knot source stays ASCII (src/SPEC.md); non-ASCII text '
                                         'is written with \\u{..} escapes.')),
    'string-concat-operator': ('string', 'knot', 'the operator a ++ b', [],
                               unsupported('parse', 'operator', OPERATOR)),
    'conversions': ('conversion', 'positive', 'U32/Nat/Char conversions and show',
                    ['holds'], AGREE),
    'literal-views': ('views', 'edge', 'a literal equals its spelled Base constructor tree',
                      ['same'], AGREE),
    'f32-literal': ('f32', 'knot', 'an F32 literal, even unused', [],
                    unsupported('lex', 'f32-literal',
                                'F32 execution is outside the bootstrap profile '
                                '(BEND-SUBSET-STAGES S3); Base F32 operations are native claims.')),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seed(args):
    """Run the seed from the repository root; a timeout aborts and is never recorded."""
    command = [*SEED, *args]
    try:
        r = subprocess.run(command, cwd=ROOT, env={**os.environ, **ENV}, capture_output=True,
                           text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.exit(f'seed timed out after {TIMEOUT}s: {command}')
    for text in (r.stdout, r.stderr):
        for leak in (str(ROOT), '/Users/', '/private/', '/tmp/'):
            if leak in text:
                sys.exit(f'seed output leaks a local path ({leak}): {command}')
    return {'command': command, 'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}


def base_names():
    text = (ROOT / SEED_DIR / 'bend2/base.bend').read_text()
    names = set(re.findall(r'^(?:def|law) ([\w.]+)', text, re.M))
    names |= set(re.findall(r'^type ([\w.]+)', text, re.M))
    names |= set(re.findall(r'^  ([A-Z]\w*)\{', text, re.M))
    return names


def enums(source):
    found = {}
    for name, body in re.findall(r'^type (\w+) is (?:Type|Data):\n((?:  .*\n)+)', source, re.M):
        ctors = re.findall(r'^  (\w+)\{\}$', body, re.M)
        assert len(ctors) == len(body.splitlines()), f'{name} is not a nullary enum'
        found[name] = ctors
    return found


def signatures(source):
    found = {}
    for name, params, out in re.findall(r'^def (\w+)\((.*?)\) -> (\w+):', source, re.M):
        found[name] = ([p.split(':')[1].strip() for p in params.split(',')] if params else [], out)
    return found


def used_base(source, base, local):
    """Base names a fixture spells, ignoring comments and literal contents."""
    code = re.sub(r"'(?:\\u\{\w*\}|\\.|[^\\])'", "''", source)
    code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
    code = re.sub(r'^\s*#.*$', '', code, flags=re.M)
    tokens = set(re.findall(r'[A-Za-z_][\w.]*', code))
    return sorted(t for t in tokens if t in base and t not in local)


def call(name, fn, args, kinds, sigs):
    params, out = sigs[fn]
    assert out in kinds, f'{name}.{fn} must return a nullary enum declared in the fixture'
    assert all(t in kinds for t in params), f'{name}.{fn} takes a non-local-enum argument'
    record = {'export': fn, 'arguments': [kinds[t].index(a) for t, a in zip(params, args)],
              'argument_constructors': list(args), 'type': out}
    if fn == 'main':
        prefix, observed = '', seed([f'tests/compiler-literals/fixtures/{name}.bend'])
    else:
        prefix = f'../../../tests/compiler-literals/fixtures/{name}.'
        wrapper = CALLS / f'{name}-{fn}-{"-".join(args) or "0"}.bend'
        source = (f'import {prefix}bend as F\n\ndef main() -> F.{out}:\n'
                  f'  F.{fn}({", ".join(f"F.{a}{{}}" for a in args)})\n')
        wrapper.write_text(source)
        record['wrapper'] = {'path': str(wrapper.relative_to(ROOT)), 'source': source}
        observed = seed([record['wrapper']['path']])
    value = re.fullmatch(re.escape(prefix) + r'(\w+)\{\}\n', observed['stdout'])
    assert observed['exit'] == 0 and observed['stderr'] == '' and value, observed
    assert value.group(1) in kinds[out], observed
    record['constructor'] = value.group(1)
    record['tag'] = kinds[out].index(value.group(1))
    record['seed'] = observed
    return record


def fixture(name, base):
    feature, kind, covers, entries, knot = PLAN[name]
    path = FIXTURES / f'{name}.bend'
    source = path.read_text()
    kinds, sigs = enums(source), signatures(source)
    local = {*kinds, *sigs, *sum(kinds.values(), [])}
    assert not local & {n.split('.')[0] for n in base}, f'{name} reuses a Base name'
    entry = {'name': name, 'file': str(path.relative_to(ROOT)), 'sha256': sha256(path),
             'feature': feature, 'kind': kind, 'covers': covers,
             'base_names': used_base(source, base, local), 'enums': kinds}
    entry['seed_check'] = seed([entry['file'], '--check-only'])
    if entry['seed_check']['exit'] == 0:
        assert entry['seed_check']['stdout'] == 'All terms check.\n', entry['seed_check']
        assert knot is AGREE or knot['outcome'] == 'Unsupported', name
        entry['calls'] = [call(name, 'main', [], kinds, sigs)]
        for fn in entries:
            for args in product(*(kinds[t] for t in sigs[fn][0])):
                entry['calls'].append(call(name, fn, args, kinds, sigs))
        if knot is AGREE:
            assert len({c['constructor'] for c in entry['calls']}) > 1, f'{name} is constant'
    else:
        assert entry['seed_check']['exit'] == 1 and not entries, (name, entry['seed_check'])
        assert knot is INVALID or knot['outcome'] == 'Unsupported', name
        entry['seed_run'] = seed([entry['file']])
        assert entry['seed_run']['exit'] == 1, entry['seed_run']
    entry['knot' if knot in (AGREE, INVALID) else 'knot_expected'] = knot
    return entry


def build():
    names = sorted(p.stem for p in FIXTURES.glob('*.bend'))
    if names != sorted(PLAN):
        sys.exit(f'fixtures and PLAN differ: only on disk {sorted(set(names) - set(PLAN))}, '
                 f'only in PLAN {sorted(set(PLAN) - set(names))}')
    CALLS.mkdir(parents=True, exist_ok=True)
    bun = subprocess.run(['bun', '--version'], capture_output=True, text=True, check=True)
    base = base_names()
    return {
        'suite': 'compiler-literals',
        'increment': 'literals: campaign milestone 5 (docs/COMPILER-CAMPAIGN.md, D4, D7)',
        'generator': 'python3 tests/compiler-literals/regen.py --write',
        'seed': {'version': '2.0.29', 'commit': '574b6d39a235b539eb19a5c532993a0abb3d11ad',
                 'launcher': SEED, 'bun': bun.stdout.strip(),
                 'sha256': {f: sha256(ROOT / SEED_DIR / f) for f in SEED_FILES}},
        'environment': {'cwd': 'repository root', **ENV},
        'fixtures': [fixture(n, base) for n in names],
    }


def render(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + '\n'


def main():
    text = render(build())
    if sys.argv[1:] == ['--write']:
        if render(build()) != text:
            sys.exit('two seed passes disagree; nothing written')
        EXPECTATIONS.write_text(text)
        print(f'wrote {EXPECTATIONS.relative_to(ROOT)}')
        return
    if sys.argv[1:]:
        sys.exit(__doc__)
    frozen = EXPECTATIONS.read_text() if EXPECTATIONS.exists() else ''
    if text != frozen:
        diff = difflib.unified_diff(frozen.splitlines(), text.splitlines(),
                                    'expectations.json', 'seed now', lineterm='', n=2)
        print('\n'.join(list(diff)[:200]))
        sys.exit('seed observations differ from expectations.json')
    doc = json.loads(text)
    calls = sum(len(f.get('calls', [])) for f in doc['fixtures'])
    print(f'literals fixtures match the seed: {len(doc["fixtures"])} fixtures, {calls} calls')


if __name__ == '__main__':
    main()
