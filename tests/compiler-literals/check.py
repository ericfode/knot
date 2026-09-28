#!/usr/bin/env python3
"""Frozen seed observations versus both Knot lanes; no host language semantics."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

TIMEOUT_SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# The modules host query makes the seed name its five foreign-dependent CLI
# definitions; builds and mutant checks must report exactly that set.
HOST_CHECKS = json.loads((ROOT / 'tests/compiler-modules/host-check-expectations.json').read_text())['entries']
BUILD = ROOT / '.local/compiler-literals/gate'
RECEIPT = HERE / 'receipts/literals.json'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
BUNDLE = ROOT / 'tests/compiler-modules/bundle/lib'
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-literals-wasm-1'
PROOFS = ['src/literal-PROOF.bend', 'src/literal-core-PROOF.bend',
          'src/literal-matrix-PROOF.bend']
OUTCOMES = {0: 'success', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted',
            5: 'HostFailure', 6: 'InternalFailure'}
INTRINSICS = {
    'U32', 'Nat', 'Char', 'String',
    *('U32.' + x for x in ('add', 'sub', 'mul', 'div', 'mod', 'not', 'and', 'cmp',
                           'is_eq', 'is_ne', 'is_lt', 'is_le', 'is_gt', 'is_ge',
                           'shln', 'shrn', 'to_nat', 'from_nat', 'show')),
    *('Nat.' + x for x in ('add', 'sub', 'mul', 'cmp', 'is_eq', 'is_ne',
                           'is_lt', 'is_le', 'is_gt', 'is_ge', 'show')),
    *('Char.' + x for x in ('from_u32', 'to_u32', 'is_eq', 'is_space')),
    *('String.' + x for x in ('eq', 'append', 'reverse', 'length', 'is_empty')),
}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith('BEND_')}
    env.update(BEND_NO_TELEMETRY='1', BEND_LIB=str(BUNDLE),
               BEND_HUB=(ROOT / 'tests/compiler-modules/bundle/hub').as_uri(),
               BEND_ORIGIN='offline://disabled')
    return env


def run(argv, timeout=180 * TIMEOUT_SCALE):
    command = [str(x) for x in argv]
    try:
        r = subprocess.run(command, cwd=ROOT, env=environment(), capture_output=True,
                           text=True, timeout=timeout)
        return {'argv': command, 'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr,
                'outcome': OUTCOMES.get(r.returncode, 'unclassified-process-failure')}
    except subprocess.TimeoutExpired:
        return {'argv': command, 'exit': None, 'outcome': 'harness-timeout',
                'budget_seconds': timeout, 'stdout': '', 'stderr': ''}
    except OSError as error:
        return {'argv': command, 'exit': None, 'outcome': 'host-launch-failure',
                'stdout': '', 'stderr': str(error)}


def success(argv, timeout=180 * TIMEOUT_SCALE, stderr=''):
    r = run(argv, timeout)
    require(r['exit'] == 0 and r['stderr'] == stderr, r)
    return r


def built(entry, output):
    return success([*SEED, entry, '-o', output], stderr=HOST_CHECKS[Path(entry).name]['stdout'])


def reject(r, code, prefix=None):
    require(r['exit'] == code and r['stdout'] == '', r)
    require(r['stderr'].startswith(prefix or OUTCOMES[code] + '\t'), r)
    require(len(r['stderr'].strip().split('\t')) >= 3, r)


def observed(r):
    return {k: r[k] for k in ('exit', 'stdout', 'stderr')}


def value(r, call):
    require(r['exit'] == 0 and r['stderr'] == '', r)
    m = re.fullmatch(r'Evaluated\t([0-9]+)\t([0-9]+)\t([^\n]+)\n', r['stdout'])
    require(m and int(m[2]) == call['tag'] and m[3] == call['constructor'] + '{}', (call, r))


def displayed(r, call):
    """A result call prints its frozen display after the Evaluated identity, byte for byte."""
    require(r['exit'] == 0 and r['stderr'] == '', r)
    m = re.fullmatch(r'Evaluated\t[0-9]+\t[0-9]+\t(.*)\n', r['stdout'], re.S)
    require(m and m[1] == call['display'], (call, r))


def wasm(path, call):
    return run(['node', HOST, PROFILE, path, call['export'], *call['arguments']])


def wasm_value(r, path, call):
    require(r['exit'] == 0 and r['stderr'] == '', r)
    require(json.loads(r['stdout']) == {'validated': True, 'export': call['export'],
            'arguments': call['arguments'], 'result': call['tag'], 'bytes': path.stat().st_size}, (call, r))


def base_inventory():
    seed = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
    probe = BUILD / 'base.ts'
    probe.write_text(f'import * as B from {json.dumps(str(seed / "bend.ts"))};\n'
        'const book = B.book_nil();\n'
        f'await B.book_load(book, {json.dumps(str(seed / "base.bend"))}, "", new Map());\n'
        'B.book_valid(book);\nconsole.log(JSON.stringify(Object.keys(book.tlds)));\n')
    r = success(['bun', probe])
    names = json.loads(r['stdout'])
    require(len(names) == len(set(names)) == 466 and INTRINSICS <= set(names), names)
    return {'declarations': names, 'result': r}


def audit(r, base, pin):
    require(r['exit'] == 0 and r['stderr'] == '', r)
    rows = [line.split('\t') for line in r['stdout'].strip().splitlines()]
    require(all(len(row) == 2 for row in rows), r)
    allowed = {'BasePin', 'Module', 'BaseChecked', 'BaseIntrinsic', 'BaseUnchecked'}
    require(all(row[0] in allowed for row in rows), r)
    groups = {key: [name for kind, name in rows if kind == key] for key in allowed}
    require(groups['BasePin'] == [pin], r)
    inventories = [groups[x] for x in ('BaseChecked', 'BaseIntrinsic', 'BaseUnchecked')]
    flat = sum(inventories, [])
    require(len(flat) == len(set(flat)) == 466 and set(flat) == set(base['declarations']), r)
    require(set(groups['BaseIntrinsic']) <= INTRINSICS and
            not (set(groups['BaseChecked']) & INTRINSICS), r)
    return {'result': r, **{k: groups[k] for k in ('BaseChecked', 'BaseIntrinsic', 'BaseUnchecked')}}


def build_lanes(record):
    lanes = {}
    record['builds'] = []
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        lanes[lane] = {}
        for phase in ('check', 'eval', 'compile'):
            path = BUILD / (phase + suffix)
            path.unlink(missing_ok=True)
            r = built(ROOT / f'src/{phase}-cli.bend', path)
            record['builds'].append({'lane': lane, 'phase': phase, 'sha256': digest(path), 'result': r})
            lanes[lane][phase] = [*runtime, path, '--bundle', BUNDLE]
            if phase == 'check':
                lanes[lane]['audit'] = [*runtime, path, '--audit-bundle', BUNDLE]
    return lanes


def fixture(f, lanes, base, pin):
    source = ROOT / f['file']
    require(digest(source) == f['sha256'], ('fixture changed', f['file']))
    expected = f.get('knot', f.get('knot_expected'))
    accepted = expected['outcome'] == 'agree'
    item = {'name': f['name'], 'file': f['file'], 'expected': expected, 'lanes': {},
            'reference_calls': len(f.get('calls', []))}
    binaries = {}
    for lane, commands in lanes.items():
        output = BUILD / f'{f["name"]}-{lane}.wasm'
        marker = b'existing output must survive a rejected source\n'
        output.write_bytes(marker)
        check = run([*commands['check'], source])
        compiled = run([*commands['compile'], source, output])
        ev = {'check': check, 'compile': compiled, 'evaluations': [], 'wasm': []}
        if accepted:
            require(check['exit'] == 0 and check['stderr'] == '' and check['stdout'].startswith('Checked\n'), check)
            require(compiled['exit'] == 0 and compiled['stderr'] == '', compiled)
            binary = output.read_bytes()
            require(binary.startswith(b'\0asm\x01\0\0\0') and
                    compiled['stdout'] == f'Built\t{len(binary)}\n', compiled)
            binaries[lane] = binary
            ev['sha256'] = digest(output)
            ev['audit'] = audit(run([*commands['audit'], source]), base, pin)
            for call in f['calls']:
                result = run([*commands['eval'], source, call['export'], 1048576, *call['arguments']])
                value(result, call)
                executed = wasm(output, call)
                wasm_value(executed, output, call)
                observation = {'export': call['export'], 'arguments': call['arguments'], 'expected_tag': call['tag']}
                ev['evaluations'].append({**observation, 'result': result})
                ev['wasm'].append({**observation, 'result': executed})
        else:
            for r in (check, compiled):
                reject(r, expected['exit'], expected.get('diagnostic_prefix'))
            require(output.read_bytes() == marker, ('rejected source changed output', compiled))
            ev['artifact_preserved'] = True
            result = run([*commands['eval'], source, 'main', 1048576])
            reject(result, expected['exit'], expected.get('diagnostic_prefix'))
            ev['evaluations'].append({'result': result})
            output.unlink()
            absent = run([*commands['compile'], source, output])
            reject(absent, expected['exit'], expected.get('diagnostic_prefix'))
            require(not output.exists(), ('rejection emitted an artifact', absent))
            ev['no_artifact'] = absent
        item['lanes'][lane] = ev
    a, b = item['lanes'].values()
    for phase in ('check', 'compile'):
        require(observed(a[phase]) == observed(b[phase]), (f['name'], phase, a[phase], b[phase]))
    require([observed(r['result']) for r in a['evaluations']] ==
            [observed(r['result']) for r in b['evaluations']], (f['name'], 'evaluation lane mismatch'))
    if accepted:
        require(binaries['native'] == binaries['bun'], (f['name'], 'binary lane mismatch'))
        require(observed(a['audit']['result']) == observed(b['audit']['result']), (f['name'], 'audit lane mismatch'))
        item['byte_identical'] = True
    return item


def result_fixture(f, lanes):
    """Both lanes check and build identical modules and print every frozen display.

    The Node host observes enum results only (CONTRACT literals.wasm.host_boundary),
    so a primitive or record result makes no Wasm call here.
    """
    source = ROOT / f['file']
    require(digest(source) == f['sha256'], ('fixture changed', f['file']))
    item = {'name': f['name'], 'file': f['file'], 'expected': {'outcome': 'display'}, 'lanes': {},
            'reference_calls': len(f['calls']), 'wasm_calls': 'not observable: enum-only host boundary'}
    binaries = {}
    for lane, commands in lanes.items():
        output = BUILD / f'{f["name"]}-{lane}.wasm'
        output.unlink(missing_ok=True)
        check = run([*commands['check'], source])
        compiled = run([*commands['compile'], source, output])
        require(check['exit'] == 0 and check['stderr'] == '' and check['stdout'].startswith('Checked\n'), check)
        require(compiled['exit'] == 0 and compiled['stderr'] == '', compiled)
        binaries[lane] = output.read_bytes()
        require(binaries[lane].startswith(b'\0asm\x01\0\0\0') and
                compiled['stdout'] == f'Built\t{len(binaries[lane])}\n', compiled)
        ev = {'check': check, 'compile': compiled, 'sha256': digest(output), 'displays': []}
        for call in f['calls']:
            result = run([*commands['eval'], source, call['export'], 1048576, *call['arguments']])
            displayed(result, call)
            ev['displays'].append({'export': call['export'], 'arguments': call['arguments'],
                                   'expected_display': call['display'], 'result': result})
        item['lanes'][lane] = ev
    a, b = item['lanes'].values()
    for phase in ('check', 'compile'):
        require(observed(a[phase]) == observed(b[phase]), (f['name'], phase, a[phase], b[phase]))
    require([observed(r['result']) for r in a['displays']] ==
            [observed(r['result']) for r in b['displays']], (f['name'], 'display lane mismatch'))
    require(binaries['native'] == binaries['bun'], (f['name'], 'binary lane mismatch'))
    item['byte_identical'] = True
    return item


# Fixed before mutant execution. Compiler validation/build failure is never a kill,
# except a `fault` mutant's pinned Bun-lane fault on a book the native lane builds:
# that lane disagreement is its defect, and its control book must keep its bytes.
# A `verdict` mutant is killed when it changes a frozen book's classification.
MUTANTS = [
    {'name': 'signed-compare', 'file': 'primitive-wasm.bend',
     'old': 'A.select(A.binary(73,a,b)', 'new': 'A.select(A.binary(72,a,b)',
     'fixture': 'u32-unsigned-order', 'export': 'compare', 'arguments': [1, 0], 'wrong_tag': 0},
    {'name': 'trapping-div-zero', 'file': 'primitive-wasm.bend',
     'old': 'arm(R.WDiv{},divide(False{}))', 'new': 'arm(R.WDiv{},A.binary(110,1,2))',
     'fixture': 'u32-division', 'export': 'exact', 'arguments': [2], 'trap': 'divide by zero'},
    {'name': 'masked-shift', 'file': 'primitive-wasm.bend',
     'old': 'A.select(A.seq([A.get(3),A.i32(32),[79]]),A.i32(0),A.binary(op,1,3))',
     'new': 'A.binary(op,1,3)',
     'fixture': 'u32-shifts', 'export': 'exact', 'arguments': [1], 'wrong_tag': 0},
    {'name': 'merged-surrogates', 'file': 'literal.bend',
     'old': 'first_code(text),text}}', 'new': 'first_code(text),merge(text)}}',
     'prepend': '''def merge(codes: List<&2,U32>) -> List<&2,U32>:
  match codes:
    case Con{55357,Con{56832,tail}}: Con{128512,merge(tail)}
    case Con{head,tail}: Con{head,merge(tail)}
    case Nil{}: Nil{}

''',
     'fixture': 'string-unicode', 'export': 'check', 'arguments': [3], 'wrong_tag': 1, 'eval': True},
    {'name': 'offset-off-by-one', 'file': 'literal-matrix.bend',
     'old': '    case S.Offset{token,0,tail}: literal(tail)',
     'new': '''    case S.Offset{+token,256,tail}:
      S.Constructor{retoken("Succ",token),[S.Offset{token,254,tail}]}
    case S.Offset{token,0,tail}: literal(tail)''',
     'fixture': 'nat-pattern-offset', 'export': 'at_least_256', 'arguments': [3], 'wrong_tag': 1, 'eval': True},
    {'name': 'spaced-offset', 'file': 'parse.bend',
     'old': 'touches(S.at(token),S.here(tokens))', 'new': 'True{}',
     'fixture': 'offset-spaced-pattern', 'verdict': (0, 'Built\t')},
    {'name': 'invalid-u32-constructor', 'file': 'literal-matrix.bend',
     'old': 'C.unsupported(G.ConstructorRef,"u32-constructor",token)', 'new': 'G.find_constructor(types,token,0)',
     'fixture': 'u32-constructor-pattern', 'verdict': (2, 'Invalid\tcheck\tunknown-constructor\t')},
    {'name': 'append-reversed', 'file': 'primitive-eval.bend', 'lane': 'eval',
     'old': 'onto(onto(a,Nil{}),b)', 'new': 'onto(a,b)',
     'fixture': 'string-append', 'export': 'spells_ab', 'arguments': [2, 0], 'wrong_tag': 0},
    {'name': 'inferred-let-literal', 'file': 'check.bend',
     'old': 'annotated(wanted,token,target => expected(token,Some{target},value))',
     'new': 'expected(token,wanted,value)',
     'fixture': 'let-u32', 'verdict': (0, 'Built\t')},
    {'name': 'kept-zero-offset', 'file': 'parse.bend',
     'old': 'Parsed{offset(token,count,value),rest}', 'new': 'Parsed{S.Offset{token,count,value},rest}',
     'fixture': 'offset-zero', 'verdict': (2, 'Invalid\tcheck\tpattern-type\t')},
    {'name': 'internal-literal-scrutinee', 'file': 'scope.bend',
     'old': 'case S.Literal{token,kind,number,text}: C.invalid(C.Binding,"constructor-scrutinee",token)',
     'new': 'case S.Literal{token,kind,number,text}: C.internal(C.Binding,"scrutinee-node")',
     'fixture': 'scrutinee-u32', 'verdict': (6, 'InternalFailure\tcheck\tscrutinee-node')},
    {'name': 'unsupported-literal-pattern', 'file': 'check.bend',
     'old': 'case S.Literal{token,kind,number,text}: C.invalid(G.ConstructorRef,"pattern-type",token)',
     'new': 'case S.Literal{token,kind,number,text}: C.unsupported(G.ConstructorRef,"pattern-type",token)',
     'fixture': 'pattern-u32-on-enum', 'verdict': (3, 'Unsupported\tcheck\tpattern-type\t')},
    {'name': 'broad-unicode-escape', 'file': 'literal.bend',
     'old': r'''    case SCon{'\\',SCon{'u',SCon{'{',tail}}}: unicode(tail,0,0,"\\u{",token)
    case SCon{'\\',SCon{'U',SCon{'{',tail}}}: unicode(tail,0,0,"\\U{",token)
''',
     'new': r'''    case SCon{'\\',SCon{+u,SCon{'{',+tail}}}:
      S.choose(Result<S.Error,Glyph>,Bool.or(Char.is_eq(u,'u'),Char.is_eq(u,'U')),x =>
        unicode(tail,0,0,String.concat(["\\",SCon{u,SNil{}},"{"]),token),x => invalid(Glyph,token,"escape"))
''',
     'fixture': 'escape-brace', 'verdict': (2, 'Invalid\tlex\tescape\t')},
    {'name': 'unlifted-promoted-column', 'file': 'literal-matrix.bend',
     'old': 'promote(bindings,level(head),promoted(values))', 'new': 'promote(bindings,level(head),False{})',
     'fixture': 'promoted-column', 'verdict': (2, 'Invalid\tcheck\taffine-reuse\t')},
    {'name': 'refined-default-binder', 'file': 'literal-matrix.bend',
     'old': 'C.Binding{token,level,q,typ,param,None{}}', 'new': 'C.Binding{token,level,q,typ,param,known}',
     'fixture': 'affine-default-scrutinee', 'verdict': (0, 'Built\t')},
    {'name': 'all-leaf-invalid', 'file': 'check.bend',
     'old': 'run(n,Matrix{live,target,False{}},catalog,current,scope)',
     'new': 'run(n,MatrixLeaves{Con{live,rest},target},catalog,current,scope)',
     'fixture': 'dead-arm-u32-duplicate', 'verdict': (2, 'Invalid\tcheck\ttype-mismatch\t')},
    {'name': 'dead-before-live', 'file': 'check.bend',
     'old': '''run(n,Matrix{plan,target,False{}},catalog,current,scope),body =>
                S.bind(C.Checked,C.Checked,run(n,Matrix{plan,target,True{}},catalog,current,scope),u =>''',
     'new': '''run(n,Matrix{plan,target,True{}},catalog,current,scope),u =>
                S.bind(C.Checked,C.Checked,run(n,Matrix{plan,target,False{}},catalog,current,scope),body =>''',
     'fixture': 'live-arm-u32-default', 'verdict': (3, 'Unsupported\tcheck\tdead-arm\t')},
    {'name': 'invalid-own-primitive', 'file': 'literal-check.bend',
     'old': 'C.unsupported(U32,"literal-base-type",token)', 'new': 'C.invalid(U32,"literal-base-type",token)',
     'fixture': 'own-nat-literal', 'verdict': (2, 'Invalid\tcheck\tliteral-base-type\t')},
    {'name': 'invalid-own-pattern', 'file': 'check.bend',
     'old': 'arm_pattern(pat,types,type_id)', 'new': 'pattern(pat,types)',
     'fixture': 'own-nat-zero-pattern', 'verdict': (2, 'Invalid\tcheck\tpattern-type\t')},
    {'name': 'unspelled-own-target', 'file': 'literal-check.bend',
     'old': 'declares(G.find_constructor(types,name,0),id)', 'new': 'False{}',
     'fixture': 'own-n-literal-expr', 'verdict': (2, 'Invalid\tcheck\tunknown-type\t')},
    # Exhaustion mutant: Nat.add(kn,t) re-counts t at every level of a recursion,
    # so the frozen linear value becomes resource exhaustion in both lanes.
    {'name': 'offset-nat-add', 'file': 'check.bend', 'import': 'import ./primitive-op.bend as R\n',
     'old': '''S.bind(G.ConstructorRef,C.Checked,M.lookup(types,M.retoken("Succ",token)),+reference =>
            S.bind(List<&2,C.Parameter>,C.Checked,G.field_signature(reference,types),params =>
              S.bind(C.Checked,C.Checked,run(n,Expression{M.literal(tail),Some{id}},catalog,current,scope),inner =>
                offset(inner,count,reference,M.retoken("Succ",token),target,params))))))''',
     'new': 'run(n,Expression{S.Intrinsic{token,R.NAdd{},[S.Literal{token,1,count,Nil{}},tail]},Some{target}},'
            'catalog,current,scope)))',
     'fixture': 'offset-expression-depth', 'export': 'successor', 'arguments': [], 'exhausted': True, 'eval': True},
    # Count mutants: the offset wraps one successor too few, or every wrapped tail gains one.
    {'name': 'offset-one-short', 'file': 'check.bend',
     'old': 'N.successors(U32.to_nat(count),term', 'new': 'N.successors(U32.to_nat(U32.sub(count,1)),term',
     'fixture': 'offset-expression-width', 'export': 'wide_sum', 'arguments': [], 'wrong_tag': 0, 'eval': True},
    {'name': 'offset-unchecked-type', 'file': 'check.bend',
     'old': 'expected(token,Some{target},C.Checked{N.successors(U32.to_nat(count),term,token,type_id,tag,params),type_id,uses})',
     'new': 'Done{C.Checked{N.successors(U32.to_nat(count),term,token,type_id,tag,params),type_id,uses}}',
     'fixture': 'offset-expression-mismatch', 'verdict': (0, 'Built\t')},
    {'name': 'offset-extra-successor', 'file': 'literal-offset.bend',
     'old': '    case 0n: term', 'new': '    case 0n: C.Construct{token,type_id,tag,fields,[term]}',
     'fixture': 'offset-expression-depth', 'export': 'successor', 'arguments': [], 'wrong_tag': 0, 'eval': True},
    # Width mutant: one chunk per section is the same module wherever the stack
    # suffices, but the builder copies a chunk with a non-tail List.append, so on
    # the Bun lane a chunk's length is a stack depth.
    {'name': 'unbounded-chunk', 'file': 'literal-wasm.bend',
     'old': 'appended(A.runs(4096,data),B.empty(cap))', 'new': 'W.bytes(cap,data)',
     'fixture': 'module-width', 'control': 'u32-literals',
     'fault': 'bend: memory fault (machine stack overflow?)\n'},
    # Display mutants: the frozen wrong display is the kill; any other output is not.
    {'name': 'constructor-tag-display', 'file': 'eval.bend', 'lane': 'eval',
     'old': 'shape(L.kind(definition),definition,value)', 'new': 'shape(None{},definition,value)',
     'fixture': 'result-char', 'export': 'sample', 'arguments': [0], 'wrong_display': 'Chr{}'},
    {'name': 'quote-blind-escape', 'file': 'primitive-eval.bend', 'lane': 'eval',
     'old': 'S.choose(Maybe<&2,Char>,U32.is_eq(code,mark),',
     'new': 'S.choose(Maybe<&2,Char>,Bool.or(U32.is_eq(code,34),U32.is_eq(code,39)),',
     'fixture': 'result-char', 'export': 'sample', 'arguments': [4], 'wrong_display': "'\\\"'"},
    {'name': 'raw-delete', 'file': 'primitive-eval.bend', 'lane': 'eval',
     'old': 'Bool.and(U32.is_ge(code,32),U32.is_ne(code,127))', 'new': 'U32.is_ge(code,32)',
     'fixture': 'result-char', 'export': 'sample', 'arguments': [12], 'wrong_display': "'\x7f'"},
]


def killed_by_verdict(m, f, compiler, folder):
    """A classification kill: the mutant compiler's verdict on a frozen book changes.

    The mutant verdict is fixed in MUTANTS; a crash, timeout or any other
    verdict is not a kill.
    """
    output = folder / 'witness.wasm'
    compiled = run(['bun', compiler, '--bundle', BUNDLE, ROOT / f['file'], output])
    status, prefix = m['verdict']
    expected = f.get('knot', f.get('knot_expected'))
    stream = compiled['stdout'] if status == 0 else compiled['stderr']
    require(status != expected['exit'] and compiled['exit'] == status and stream.startswith(prefix), (m['name'], compiled))
    if status == 0:
        require(output.read_bytes().startswith(b'\0asm\x01\0\0\0') and
                compiled['stdout'] == f'Built\t{output.stat().st_size}\n', compiled)
    return {'compile': compiled, 'expected_exit': expected['exit']}


def killed_by_value(m, f, compiler, folder):
    call = next(c for c in f['calls'] if c['export'] == m['export'] and c['arguments'] == m['arguments'])
    output = folder / 'witness.wasm'
    compiled = success(['bun', compiler, '--bundle', BUNDLE, ROOT / f['file'], output])
    require(compiled['stdout'] == f'Built\t{output.stat().st_size}\n', compiled)
    result = wasm(output, call)
    if 'trap' in m:
        reject(result, 5, 'HostFailure\twasm\t' + m['trap'])
    elif m.get('exhausted'):
        reject(result, 4, 'Exhausted\twasm\tresource-limit')
    else:
        require(m['wrong_tag'] != call['tag'], m)
        wasm_value(result, output, {**call, 'tag': m['wrong_tag']})
    return {'expected_tag': call['tag'], 'compile': compiled, 'wasm': result}


def killed_by_fault(m, f, control, compiler, folder):
    """A lane kill: the mutant's Bun lane builds the control book's gate bytes and
    faults, leaving its output untouched, on the book both gate lanes built."""
    narrow = folder / 'control.wasm'
    same = success(['bun', compiler, '--bundle', BUNDLE, ROOT / control['file'], narrow])
    require(narrow.read_bytes() == (BUILD / f'{control["name"]}-bun.wasm').read_bytes(), (m['name'], 'control bytes'))
    output = folder / 'witness.wasm'
    marker = b'a faulted build leaves this file\n'
    output.write_bytes(marker)
    faulted = run(['bun', compiler, '--bundle', BUNDLE, ROOT / f['file'], output])
    require(faulted['exit'] == 1 and faulted['stdout'] == '' and faulted['stderr'] == m['fault'], (m['name'], faulted))
    require(output.read_bytes() == marker, (m['name'], 'fault changed output'))
    return {'control_build': same, 'faulted': faulted}


def evaluated_wrong(m, f, folder):
    call = next(c for c in f['calls'] if c['export'] == m['export'] and c['arguments'] == m['arguments'])
    shown = 'wrong_display' in m
    require(shown or m.get('exhausted') or m['wrong_tag'] != call['tag'], m)
    require(not shown or m['wrong_display'] != call['display'], m)
    evaluator = folder / 'eval.js'
    record = {'expected_display' if shown else 'expected_tag': call['display' if shown else 'tag'],
              'eval_build': built(folder / 'eval-cli.bend', evaluator)}
    evaluated = run(['bun', evaluator, '--bundle', BUNDLE, ROOT / f['file'],
                     call['export'], 1048576, *call['arguments']])
    if shown:
        displayed(evaluated, {**call, 'display': m['wrong_display']})
        return {**record, 'eval': evaluated}
    if m.get('exhausted'):
        reject(evaluated, 4, 'Exhausted\teval\tbudget\t')
        return {**record, 'eval': evaluated}
    wrong = re.fullmatch(r'Evaluated\t[0-9]+\t([0-9]+)\t[^\n]+\n', evaluated['stdout'])
    require(evaluated['exit'] == 0 and evaluated['stderr'] == '' and
            wrong and int(wrong[1]) == m['wrong_tag'], evaluated)
    return {**record, 'eval': evaluated}


def mutants(fixtures):
    by_name = {f['name']: f for f in fixtures}
    records = []
    for m in MUTANTS:
        folder = BUILD / 'mutants' / m['name']
        folder.mkdir(parents=True, exist_ok=True)
        for source in sorted((ROOT / 'src').glob('*.bend')):
            shutil.copy2(source, folder / source.name)
        shutil.copytree(ROOT / 'src/host', folder / 'host', dirs_exist_ok=True)
        path = folder / m['file']
        code = path.read_text()
        require(code.count(m['old']) == 1, (m['name'], 'mutation anchor not unique'))
        code = code.replace(m['old'], m['new'])
        if 'prepend' in m:
            code = code.replace('def decoded(', m['prepend'] + 'def decoded(')
        if 'import' in m:
            require(code.startswith('import Base\n'), (m['name'], 'import anchor'))
            code = code.replace('import Base\n', 'import Base\n' + m['import'], 1)
        path.write_text(code)
        f = by_name[m['fixture']]
        record = {**m, 'sha256': digest(path)}
        # Evaluator-only mutants change no emitted byte; their witness is the evaluator lane.
        entry = folder / ('eval-cli.bend' if m.get('lane') == 'eval' else 'compile-cli.bend')
        typed = success([*SEED, entry, '--check-only'])
        require(typed['stdout'] == HOST_CHECKS[entry.name]['stdout'], typed)
        record['typecheck'] = typed
        if m.get('lane') != 'eval':
            compiler = folder / 'compile.js'
            record['build'] = built(entry, compiler)
            if 'fault' in m:
                record.update(killed_by_fault(m, f, by_name[m['control']], compiler, folder))
            else:
                kill = killed_by_verdict if 'verdict' in m else killed_by_value
                record.update(kill(m, f, compiler, folder))
        if m.get('eval') or m.get('lane') == 'eval':
            record.update(evaluated_wrong(m, f, folder))
        record['killed'] = True
        records.append(record)
    return records


def boundaries(lanes):
    records = []
    source = HERE / 'fixtures/u32-literals.bend'
    for lane, commands in lanes.items():
        for name, args, status in [('zero-eval-budget', ['main', 0], 4),
                                   ('bad-eval-budget', ['main', 1048577], 5)]:
            r = run([*commands['eval'], source, *args])
            reject(r, status)
            records.append({'lane': lane, 'name': name, 'result': r})
        for name, depth, capacity in [('zero-emitter-budget', 0, 1048576),
                                       ('zero-output-budget', 4096, 0)]:
            path = BUILD / f'{lane}-{name}.wasm'
            marker = b'budget exhaustion preserves this file\n'
            path.write_bytes(marker)
            r = run([*commands['compile'], source, path, 65536, 512, 4096, depth, capacity])
            reject(r, 4)
            require(path.read_bytes() == marker, r)
            records.append({'lane': lane, 'name': name, 'artifact_preserved': True, 'result': r})
    return records


OFFSET_LIMITS = [  # count k: (evaluator status, compiler status, refusing phase)
    (2047, 0, 0, None), (2048, 0, 4, 'emit'), (4096, 0, 4, 'emit'), (4097, 4, 4, 'check')]


def offset_limits(lanes):
    """The count of `kn+t` up to 4096 checks and evaluates, and its module builds up to 2047
    successors (the emitter takes two of its 4096 levels for each); past 4096 is Exhausted check."""
    records = []
    yes = {'export': 'main', 'arguments': [], 'tag': 1, 'constructor': 'Yes'}
    for k, evaluates, compiles, phase in OFFSET_LIMITS:
        source = BUILD / f'offset-{k}.bend'
        source.write_text('import Base\n\ntype Answer is Type:\n  No{}\n  Yes{}\n\n'
                          'def answer(b: Bool) -> Answer:\n  match b:\n    case False{}: No{}\n    case True{}: Yes{}\n\n'
                          f'def f(t: Nat) -> Nat:\n  {k}n+t\n\n'
                          f'def main() -> Answer:\n  answer(Nat.is_eq(f(0n), {k}n))\n')
        for lane, commands in lanes.items():
            output = BUILD / f'{lane}-offset-{k}.wasm'
            marker = b'a refused offset preserves this file\n'
            output.write_bytes(marker)
            evaluated = run([*commands['eval'], source, 'main', 1048576])
            compiled = run([*commands['compile'], source, output])
            record = {'lane': lane, 'name': f'offset-{k}', 'eval': evaluated, 'compile': compiled}
            if evaluates:
                reject(evaluated, 4, 'Exhausted\tcheck\tbudget\t')
            else:
                value(evaluated, yes)
            if compiles:
                reject(compiled, 4, f'Exhausted\t{phase}\tbudget\t')
                require(output.read_bytes() == marker, compiled)
                record['artifact_preserved'] = True
            else:
                require(compiled['exit'] == 0 and compiled['stderr'] == '' and
                        compiled['stdout'] == f'Built\t{output.stat().st_size}\n', compiled)
                record['wasm'] = wasm(output, yes)
                wasm_value(record['wasm'], output, yes)
            records.append(record)
    return records


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'expectations.json').read_text())
    supplemental = json.loads((HERE / 'supplemental.json').read_text())
    regressions = json.loads((HERE / 'regressions.json').read_text())
    results = json.loads((HERE / 'results.json').read_text())
    inputs = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json', HOST,
              Path(__file__), HERE / 'expectations.json', HERE / 'regen.py', HERE / 'supplemental.json',
              HERE / 'supplemental.py', HERE / 'regressions.json', HERE / 'regressions.py',
              HERE / 'results.json', HERE / 'results.py', HERE / 'FIXTURES.md',
              ROOT / 'tests/compiler-modules/host-check-expectations.json', *sorted((ROOT / 'src/host').glob('*'))]
    inputs += sorted((HERE / 'fixtures').glob('*.bend')) + sorted((HERE / 'supplemental').glob('*.bend'))
    inputs += sorted((HERE / 'regressions').glob('*.bend')) + sorted((HERE / 'results').glob('*.bend'))
    record = {'status': 'incomplete', 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'seed': manifest['seed'], 'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}}
    try:
        record['reference_verification'] = success(['python3', HERE / 'regen.py'])
        record['supplemental_verification'] = success(['python3', HERE / 'supplemental.py'])
        record['regression_verification'] = success(['python3', HERE / 'regressions.py'])
        record['result_verification'] = success(['python3', HERE / 'results.py'])
        require(supplemental['seed_sha256'] == manifest['seed']['sha256'] == regressions['seed_sha256'] ==
                results['seed_sha256'], 'Seed identity differs')
        record['tools'] = {tool: success([tool, '--version'])['stdout'].strip() for tool in ('bun', 'node', 'python3')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        record['base'] = base_inventory()
        record['proofs'] = []
        for entry in PROOFS:
            r = success([*SEED, ROOT / entry])
            require(r['stdout'] == 'All terms check.\n', r)
            record['proofs'].append({'entry': entry, 'result': r})
        lanes = build_lanes(record)
        record['fixtures'] = []
        for f in [*manifest['fixtures'], *supplemental['fixtures'], *regressions['fixtures']]:
            record['fixtures'].append(fixture(f, lanes, record['base'], manifest['seed']['sha256']['bend2/base.bend']))
        record['results'] = [result_fixture(f, lanes) for f in results['fixtures']]
        record['boundaries'] = boundaries(lanes) + offset_limits(lanes)
        record['mutants'] = mutants([*manifest['fixtures'], *supplemental['fixtures'], *regressions['fixtures'],
                                     *results['fixtures']])
        require(all(digest(ROOT / path) == h for path, h in record['inputs'].items()), 'Inputs changed during literals gate')
        fs = record['fixtures']
        ls = [lane for f in fs for lane in f['lanes'].values()]
        record['counts'] = {
            'fixtures': len(fs), 'agree_fixtures': sum(f['expected']['outcome'] == 'agree' for f in fs),
            'invalid_fixtures': sum(f['expected']['outcome'] == 'Invalid' for f in fs),
            'unsupported_fixtures': sum(f['expected']['outcome'] == 'Unsupported' for f in fs),
            'reference_calls': sum(f['reference_calls'] for f in fs), 'execution_lanes': len(lanes),
            'check_observations': len(ls), 'compile_observations': len(ls),
            'eval_observations': sum(len(l['evaluations']) for l in ls),
            'agree_eval_observations': sum(len(l['wasm']) for l in ls),
            'wasm_observations': sum(len(l['wasm']) for l in ls),
            'byte_identity_pairs': sum(f.get('byte_identical', False) for f in fs),
            'artifact_preservation_probes': sum(l.get('artifact_preserved', False) for l in ls),
            'no_artifact_probes': sum('no_artifact' in l for l in ls),
            'trust_audits': sum('audit' in l for l in ls),
            'boundary_probes': len(record['boundaries']), 'proof_entries': len(record['proofs']),
            'proof_laws': 37, 'semantic_mutants': len(record['mutants']),
            'mutant_wasm_observations': sum('wasm' in m for m in record['mutants']),
            'mutant_verdict_observations': sum('verdict' in m for m in record['mutants']),
            'mutant_fault_observations': sum('faulted' in m for m in record['mutants']),
            'mutant_eval_observations': sum(m.get('eval') is not None for m in record['mutants']),
            'result_fixtures': len(record['results']),
            'result_calls': sum(r['reference_calls'] for r in record['results']),
            'result_display_observations': sum(len(l['displays']) for r in record['results']
                                               for l in r['lanes'].values()),
            'result_byte_identity_pairs': sum(r['byte_identical'] for r in record['results']),
        }
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Literals gate passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
