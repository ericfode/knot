#!/usr/bin/env python3
"""Frozen seed observations of the merge books versus both Knot lanes, and mutants of their rules."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

TIMEOUT_SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only
WORKERS = 4  # independent observations run on this many threads; results keep their frozen order
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# The modules host query makes the seed name its five foreign-dependent CLI
# definitions; builds and mutant checks must report exactly that set.
HOST_CHECKS = json.loads((ROOT / 'tests/compiler-modules/host-check-expectations.json').read_text())['entries']
BUILD = ROOT / '.local/compiler-literals-integ/gate'
RECEIPT = HERE / 'receipts/literals-integ.json'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
BUNDLE = ROOT / 'tests/compiler-modules/bundle/lib'
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-literals-wasm-1'
OUTCOMES = {0: 'success', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted',
            5: 'HostFailure', 6: 'InternalFailure'}

# Fixed before mutant execution: each mutant changes one merge rule and must change the verdict of
# its witness book to exactly this one. A build failure, crash, timeout or any other verdict is no kill.
MUTANTS = [
    {'name': 'erased-let-dotted', 'file': 'parse.bend',
     'old': 'Bool.and(Bool.and(String.contains(S.text(name),"."),Bool.not(parameter_named(params,S.text(name)))),Bool.not(erased)),u =>',
     'new': 'Bool.and(Bool.and(String.contains(S.text(name),"."),Bool.not(parameter_named(params,S.text(name)))),True{}),u =>',
     'fixture': 'erased-dotted-let', 'verdict': (2, 'Invalid\tparse\tbinding-name\t')},
    {'name': 'case-heads-a-body', 'file': 'parse.bend',
     'old': 'Bool.and(Bool.or(S.matches(h,"case"),S.matches(h,"def")),U32.is_le(S.column(h),parent)),u =>',
     'new': 'Bool.and(S.matches(h,"def"),U32.is_le(S.column(h),parent)),u =>',
     'fixture': 'arm-body-case', 'verdict': (3, 'Unsupported\tparse\tterm-form\t')},
    {'name': 'def-heads-a-body', 'file': 'parse.bend',
     'old': 'Bool.and(Bool.or(S.matches(h,"case"),S.matches(h,"def")),U32.is_le(S.column(h),parent)),u =>',
     'new': 'Bool.and(S.matches(h,"case"),U32.is_le(S.column(h),parent)),u =>',
     'fixture': 'arm-body-def', 'verdict': (3, 'Unsupported\tparse\tterm-form\t')},
    {'name': 'spaced-plus-is-a-missing-comma', 'file': 'parse.bend',
     'old': 'Bool.and(Bool.not(pattern),Bool.and(S.matches(h,"+"),Bool.not(promotes(tokens)))),u => unsupported(tokens,"operator"),u =>',
     'new': 'Bool.and(Bool.not(pattern),Bool.and(S.matches(h,"+"),Bool.not(promotes(tokens)))),u => invalid(tokens,"argument-separator"),u =>',
     'fixture': 'spaced-plus-concat', 'verdict': (2, 'Invalid\tparse\targument-separator\t')},
    {'name': 'literal-column-checked', 'file': 'matrix.bend',
     'old': 'case 1n+n S.Literal{token,kind,number,text}: C.unsupported(Unit,"literal-column",token)',
     'new': 'case 1n+n S.Literal{token,kind,number,text}: Done{Unit{}}',
     'fixture': 'literal-column-u32', 'verdict': (0, 'Checked\n')},
    {'name': 'offset-column-checked', 'file': 'matrix.bend',
     'old': 'case 1n+n S.Offset{token,count,tail}: C.unsupported(Unit,"literal-column",token)',
     'new': 'case 1n+n S.Offset{token,count,tail}: Done{Unit{}}',
     'fixture': 'literal-column-offset', 'verdict': (0, 'Checked\n')},
    # Review round 1. A let names its own name for the body below it.
    {'name': 'let-binds-nothing-below', 'file': 'parse.bend',
     'old': 'binders(n,body,False{},Con{S.Parameter{token,q,token},params}))',
     'new': 'binders(n,body,False{},params))',
     'fixture': 'erased-dotted-rebind', 'verdict': (2, 'Invalid\tparse\tbinding-name\t')},
    {'name': 'let-value-ends-at-any-token', 'file': 'parse.bend',
     'old': 'S.bind(List<&2,S.Token>,Parsed,line_end(tokens),body =>',
     'new': 'S.bind(List<&2,S.Token>,Parsed,expect(tokens,"\\n"),body =>',
     'fixture': 'let-concat-typed', 'verdict': (2, 'Invalid\tparse\texpected-')},
    {'name': 'literal-starts-no-term', 'file': 'parse.bend',
     'old': 'Bool.or(S.identifier(head),Q.starts(S.text(head)))',
     'new': 'S.identifier(head)',
     'fixture': 'literal-column-late-u32', 'verdict': (2, 'Invalid\tparse\texpected-:\t')},
    {'name': 'literal-argument-is-a-missing-comma', 'file': 'parse.bend',
     'old': 'Bool.or(S.identifier(head),Q.starts(S.text(head)))',
     'new': 'S.identifier(head)',
     'fixture': 'arguments-literals', 'verdict': (2, 'Invalid\tparse\targument-separator\t')},
    {'name': 'parameter-shadows-nothing', 'file': 'parse.bend',
     'old': 'S.bind(Unit,Parsed,shadows(items,result),u =>\n        S.bind(Unit,Parsed,binders(65536n,body,False{},items),u => Done{Parsed{S.Function{token,items,result,body},rest}}))',
     'new': 'S.bind(Unit,Parsed,binders(65536n,body,False{},items),u => Done{Parsed{S.Function{token,items,result,body},rest}})',
     'fixture': 'parameter-shadows-own-type', 'verdict': (0, 'Checked\n')},
    {'name': 'parameter-shadows-every-name', 'file': 'parse.bend',
     'old': 'S.choose(Result<S.Error,Unit>,reads(name,Con{S.Parameter{name,q,typ},tail},result),u =>',
     'new': 'S.choose(Result<S.Error,Unit>,True{},u =>',
     'fixture': 'parameter-shadow-unused', 'verdict': (3, 'Unsupported\tparse\tparameter-shadow\t')},
    {'name': 'annotation-reads-no-binder', 'file': 'parse.bend',
     'old': 'Fail{S.Unsupported{"parse","annotation-shadow",S.at(typ)}}', 'new': 'Done{Unit{}}',
     'fixture': 'annotation-shadow-let', 'verdict': (0, 'Checked\n')},
    {'name': 'annotation-reads-every-name', 'file': 'parse.bend',
     'old': 'S.choose(Result<S.Error,Unit>,parameter_named(params,S.text(typ)),u =>', 'new': 'S.choose(Result<S.Error,Unit>,True{},u =>',
     'fixture': 'annotation-shadow-unread', 'verdict': (3, 'Unsupported\tparse\tannotation-shadow\t')},
    {'name': 'arm-binds-no-variable', 'file': 'parse.bend',
     'old': 'binders(n,body,False{},List.append(&2,S.Node,bound(n,head),params))', 'new': 'binders(n,body,False{},params)',
     'fixture': 'annotation-shadow-pattern', 'verdict': (0, 'Checked\n')},
    {'name': 'promotion-of-a-type-accepted', 'file': 'catalog.bend',
     'old': 'S.choose(Result<S.Error,Unit>,U32.is_eq(kind,3),u => C.invalid(Unit,"promoted-type",name),u =>',
     'new': 'S.choose(Result<S.Error,Unit>,False{},u => C.invalid(Unit,"promoted-type",name),u =>',
     'fixture': 'promoted-type-let', 'verdict': (0, 'Checked\n')},
    {'name': 'promotion-of-a-later-type-rejected', 'file': 'catalog.bend',
     'old': 'S.choose(U32,own,u => Bool.pick(U32,before,3,1),u =>',
     'new': 'S.choose(U32,own,u => 3,u =>',
     'fixture': 'promoted-type-later', 'verdict': (2, 'Invalid\tcheck\tpromoted-type\t')},
    {'name': 'row-width-unrouted', 'file': 'literal-matrix.bend',
     'old': 'Bool.and(rows_of_one(arms),scrutinee_kind(value,arms,types,scope))',
     'new': 'scrutinee_kind(value,arms,types,scope)',
     'fixture': 'row-wide-nat', 'verdict': (6, 'InternalFailure\tcheck\tpattern-node')},
    {'name': 'declaration-order-by-offset', 'file': 'check.bend',
     'old': 'function_body(signature,body,placed,index,depth)',
     'new': 'function_body(signature,body,catalog,index,depth)',
     'fixture': 'qualified-order-lib-first', 'verdict': (2, 'Invalid\tcheck\tunknown-constructor\t')},
]


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


def wasm(path, call):
    return run(['node', HOST, PROFILE, path, call['export'], *call['arguments']])


def wasm_value(r, path, call):
    require(r['exit'] == 0 and r['stderr'] == '', r)
    require(json.loads(r['stdout']) == {'validated': True, 'export': call['export'],
            'arguments': call['arguments'], 'result': call['tag'], 'bytes': path.stat().st_size}, (call, r))


def build_lanes(record):
    """Each lane is the seed's own build of the three CLIs of the working tree, in the order given."""
    BUILD.mkdir(parents=True, exist_ok=True)
    jobs = [(lane, suffix, runtime, phase) for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]
            for phase in ('check', 'eval', 'compile')]

    def build(job):
        lane, suffix, runtime, phase = job
        path = BUILD / (phase + suffix)
        path.unlink(missing_ok=True)
        r = built(ROOT / f'src/{phase}-cli.bend', path)
        return {'lane': lane, 'phase': phase, 'sha256': digest(path), 'result': r}
    with ThreadPoolExecutor(WORKERS) as pool:
        record['builds'] = list(pool.map(build, jobs))
    return {lane: {phase: [*runtime, BUILD / (phase + suffix), '--bundle', BUNDLE]
                   for phase in ('check', 'eval', 'compile')}
            for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]}


def fixture(f, lanes):
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
        item['byte_identical'] = True
    return item


PAD = '# ' + '0' * 300 + '\n'


def perturbed(name, pad_libs):
    """A copy of the modules fixtures in which every module of one kind starts with a comment."""
    target = BUILD / 'meta' / name
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(ROOT / 'tests/compiler-modules/fixtures', target)
    for path in target.rglob('*.bend'):
        if ('lib' in path.relative_to(target).parts[:-1]) == pad_libs:
            path.write_text(PAD + path.read_text())
    return target


def outcome(r):
    """What a comment must not change: the exit, the checked book, or a rejection's outcome, phase and code."""
    return r['exit'], r['stdout'] if r['exit'] == 0 else r['stderr'].split('\t')[:3]


def metamorphic(check):
    """Byte offsets order the tokens of one file: a comment before a module changes no verdict."""
    trees = {'plain': perturbed('plain', None), 'libs': perturbed('libs', True), 'entries': perturbed('entries', False)}
    entries = sorted(p.name for p in trees['plain'].glob('*.bend'))
    with ThreadPoolExecutor(WORKERS) as pool:
        seen = {kind: dict(zip(entries, pool.map(lambda e: run([*check, tree / e]), entries)))
                for kind, tree in trees.items()}
    pairs = []
    for kind in ('libs', 'entries'):
        for entry in entries:
            plain, padded = seen['plain'][entry], seen[kind][entry]
            require(plain['exit'] is not None and padded['exit'] is not None, (entry, kind, 'no verdict'))
            require(outcome(plain) == outcome(padded), (entry, kind, plain, padded))
            pairs.append({'entry': entry, 'padded': kind, 'exit': plain['exit']})
    return {'entries': len(entries), 'pairs': pairs}


def selfhost_twin(check):
    """The selfhost suite pins one row of the wrong width as `Invalid check pattern-arity`; it runs Knot
    single-file, where the book stops earlier at `Unsupported lex literal`, so the bundle entry is checked here."""
    expectations = json.loads((ROOT / 'tests/compiler-selfhost/expectations.json').read_text())
    name = 'fuel-string-columns-arity'
    pin = next(c for c in expectations['cases'] if c['name'] == name)['knot']
    require(pin['require'] == 'reject' and pin['exit'] == 2, pin)
    result = run([*check, ROOT / f'tests/compiler-selfhost/fixtures/{name}/main.bend'])
    reject(result, pin['exit'], pin['diagnostic'])
    return {'name': name, 'pin': pin['diagnostic'], 'result': result}


def mutant(m, by_name):
    folder = BUILD / 'mutants' / m['name']
    folder.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / 'src').glob('*.bend')):
        shutil.copy2(source, folder / source.name)
    shutil.copytree(ROOT / 'src/host', folder / 'host', dirs_exist_ok=True)
    path = folder / m['file']
    code = path.read_text()
    require(code.count(m['old']) == 1, (m['name'], 'mutation anchor not unique'))
    path.write_text(code.replace(m['old'], m['new']))
    f = by_name[m['fixture']]
    record = {**m, 'sha256': digest(path)}
    typed = success([*SEED, folder / 'check-cli.bend', '--check-only'])
    require(typed['stdout'] == HOST_CHECKS['check-cli.bend']['stdout'], typed)
    record['typecheck'] = typed
    compiler = folder / 'check.js'
    record['build'] = built(folder / 'check-cli.bend', compiler)
    status, prefix = m['verdict']
    expected = f.get('knot', f.get('knot_expected'))
    witness = run(['bun', compiler, '--bundle', BUNDLE, ROOT / f['file']])
    stream = witness['stdout'] if status == 0 else witness['stderr']
    require(status != expected['exit'] and witness['exit'] == status and stream.startswith(prefix), (m['name'], witness))
    record.update({'witness': witness, 'expected_exit': expected['exit'], 'killed': True})
    return record


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'expectations.json').read_text())
    inputs = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json', HOST,
              Path(__file__), HERE / 'expectations.json', HERE / 'freeze.py', HERE / 'README.md',
              ROOT / 'tests/compiler-literals/regen.py', ROOT / 'tests/compiler-modules/host-check-expectations.json',
              *sorted((ROOT / 'src/host').glob('*')), *sorted((HERE / 'fixtures').rglob('*.bend'))]
    record = {'status': 'incomplete', 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}}
    try:
        record['verification'] = success(['python3', HERE / 'freeze.py'])
        record['tools'] = {tool: success([tool, '--version'])['stdout'].strip() for tool in ('bun', 'node', 'python3')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        lanes = build_lanes(record)
        with ThreadPoolExecutor(WORKERS) as pool:
            record['fixtures'] = list(pool.map(lambda f: fixture(f, lanes), manifest['fixtures']))
            by_name = {f['name']: f for f in manifest['fixtures']}
            record['mutants'] = list(pool.map(lambda m: mutant(m, by_name), MUTANTS))
        record['metamorphic'] = metamorphic(lanes['native']['check'])
        record['selfhost_twin'] = selfhost_twin(lanes['native']['check'])
        require(all(digest(ROOT / path) == h for path, h in record['inputs'].items()),
                'Inputs changed during the integration gate')
        fs = record['fixtures']
        ls = [lane for f in fs for lane in f['lanes'].values()]
        record['counts'] = {
            'fixtures': len(fs), 'agree_fixtures': sum(f['expected']['outcome'] == 'agree' for f in fs),
            'invalid_fixtures': sum(f['expected']['outcome'] == 'Invalid' for f in fs),
            'unsupported_fixtures': sum(f['expected']['outcome'] == 'Unsupported' for f in fs),
            'reference_calls': sum(f['reference_calls'] for f in fs), 'execution_lanes': len(lanes),
            'check_observations': len(ls), 'compile_observations': len(ls),
            'eval_observations': sum(len(l['evaluations']) for l in ls),
            'wasm_observations': sum(len(l['wasm']) for l in ls),
            'byte_identity_pairs': sum(f.get('byte_identical', False) for f in fs),
            'artifact_preservation_probes': sum(l.get('artifact_preserved', False) for l in ls),
            'no_artifact_probes': sum('no_artifact' in l for l in ls),
            'metamorphic_pairs': len(record['metamorphic']['pairs']), 'selfhost_twins': 1,
            'semantic_mutants': len(record['mutants']),
            'mutant_verdict_observations': sum('witness' in m for m in record['mutants']),
        }
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Literals integration gate passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
