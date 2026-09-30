#!/usr/bin/env python3
"""Compare the frozen seed corpus with two Bend compiler lanes and Node Wasm."""
from __future__ import annotations

import datetime
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys

from prechecks.check import replay as precheck_replay, rows as precheck_rows

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-generics/gate'
RECEIPT = HERE / 'receipts/generics.json'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-fields-wasm-1'
COMPILE = ROOT / 'tests/compiler-fields-wasm/compile.bend'
ABI_EXPECTATIONS = HERE / 'abi-expectations.json'
HOST_EXPECTATIONS = HERE / 'host-boundaries/host-expectations.json'
ABI_HOST = BUILD / 'abi.mjs'
ABI_SOURCE = '''import fs from 'node:fs/promises';
const [path, ...names] = process.argv.slice(2);
try {
  const bytes = await fs.readFile(path);
  if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
  const module = await WebAssembly.compile(bytes);
  if (WebAssembly.Module.imports(module).length) throw new Error('unexpected imports');
  const instance = await WebAssembly.instantiate(module);
  const arities = {};
  for (const name of names) {
    if (!Object.hasOwn(instance.exports, name) || typeof instance.exports[name] !== 'function') {
      throw new Error('missing function export: ' + name);
    }
    arities[name] = instance.exports[name].length;
  }
  console.log(JSON.stringify({validated: true, arities, bytes: bytes.length}));
} catch (error) {
  console.error('HostFailure\\tabi\\t' + error.message);
  process.exitCode = 5;
}
'''
SOURCES = (HERE, HERE / 'supplemental', HERE / 'boundaries', HERE / 'dispatch-boundaries',
           HERE / 'bare-families', HERE / 'value-arguments', HERE / 'empty-families',
           HERE / 'def-references', HERE / 'type-level-names', HERE / 'marked-binders',
           HERE / 'pattern-order', HERE / 'spacing', HERE / 'token-gaps', HERE / 'host-boundaries')
PROOFS = ('src/PROOF.bend', 'src/types-PROOF.bend', 'src/type-erasure-PROOF.bend',
          'src/catalog-PROOF.bend', 'src/generic-catalog-PROOF.bend',
          'src/type-parse-PROOF.bend', 'src/parse-order-PROOF.bend', 'src/parse-layout-PROOF.bend',
          'src/generics-PROOF.bend')
MARKER = b'Existing artifact: semantic rejection must preserve these bytes.\n'
# Harness hang guard only, as in the other gates; the runner scales it under load.
TIMEOUT_SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1',
       'BEND_HUB': 'offline://disabled', 'BEND_ORIGIN': 'offline://disabled'}

# Each replacement is unique, independently typechecked, and exercised against
# an unchanged frozen witness. Implementation anchors are filled with the
# mechanism; an incomplete mutation inventory cannot produce a passing gate.
MUTANTS = (
    {'name': 'skipped-substitution', 'file': 'generic-catalog.bend',
     'old': 'T.normalize(T.subst(value,substitutions))',
     'new': 'T.normalize(value)',
     'witness': 'box-unbox', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\ttype-mismatch\t'}},
    {'name': 'erased-argument-live', 'file': 'type-erasure.bend',
     'old': 'case G.Parameter{token,q,typ}: C.Parameter{token,q,type_id(typ)}',
     'new': 'case G.Parameter{token,+q,typ}: C.Parameter{token,Bool.pick(U32,U32.is_eq(q,0),1,q),type_id(typ)}',
     'witness': 'box-unbox', 'phase': 'abi', 'exports': ['unbox'],
     'actual': {'exit': 0, 'arities': {'unbox': 2}}},
    {'name': 'wrong-quantity-meet', 'file': 'types.bend',
     'old': 'case QMany{}: b', 'new': 'case QMany{}: QMany{}',
     'witness': 'meet-not-reusable', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'missing-arity-check', 'file': 'generic-catalog.bend',
     'old': 'C.invalid(List<&2,S.Node>,"type-arity",token)',
     'new': 'Done{List.take(&2,S.Node,nodes,U32.to_nat(arity))}',
     'witness': 'type-arity', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'bare-quantity-default', 'file': 'generic-catalog.bend',
     'old': 'reference => bare(reference,token,',
     'new': 'reference => apply_start(reference,token,Nil{},1,',
     'witness': 'bare-family-parameter', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'term-argument-invalid', 'file': 'type-parse.bend',
     'old': 'Fail{S.Unsupported{"parse","term-argument",S.at(h)}}',
     'new': 'Fail{S.Invalid{"parse","term-argument",S.at(h)}}',
     'witness': 'value-argument-parameter', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tterm-argument\t'}},
    {'name': 'empty-family-invalid', 'file': 'generic-catalog.bend',
     'old': 'C.unsupported(Family,"empty-datatype",token)',
     'new': 'C.invalid(Family,"empty-datatype",token)',
     'witness': 'empty-generic-absurd', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tempty-datatype\t'}},
    {'name': 'empty-datatype-invalid', 'file': 'catalog.bend',
     'old': 'C.unsupported(C.Datatype,"empty-datatype",name)',
     'new': 'C.invalid(C.Datatype,"empty-datatype",name)',
     'witness': 'empty-type', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tempty-datatype\t'}},
    {'name': 'def-reference-free', 'file': 'scope.bend',
     'old': 'unbound(B,F,function(token),token,"def-reference",Fail{error})',
     'new': 'Fail{error}',
     'witness': 'def-reference-live', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tfree-name\t'}},
    {'name': 'type-level-definition-unknown', 'file': 'generic-catalog.bend',
     'old': 'dependent-type",token))\n    case Some{Definition{name}}: C.unsupported(Typed,"type-level-definition",token)',
     'new': 'dependent-type",token))\n    case Some{Definition{name}}: next(Unit{})',
     'witness': 'definition-field-later', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tunknown-type\t'}},
    {'name': 'marked-binder-quantity', 'file': 'type-parse.bend',
     'old': 'S.choose(Result<S.Error,Parsed>,U32.is_eq(quantity,1),u =>',
     'new': 'S.choose(Result<S.Error,Parsed>,True{},u =>',
     'witness': 'marked-reusable-binder', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'pattern-order-forward', 'file': 'generic-catalog.bend',
     'old': 'S.choose(Result<S.Error,ConstructorRef>,visible(token,declaration(reference)),u =>',
     'new': 'S.choose(Result<S.Error,ConstructorRef>,True{},u =>',
     'witness': 'later-family-parameter', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'quantity-gap-glued', 'file': 'type-parse.bend',
     'old': 'glued(token,value)', 'new': 'True{}',
     'witness': 'quantity-gap-argument', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'meet-gap-glued', 'file': 'type-parse.bend',
     'old': 'Bool.and(glued(a,b),glued(b,c))', 'new': 'True{}',
     'witness': 'meet-gap', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'close-gap-glued', 'file': 'type-parse.bend',
     'old': 'u => Bool.not(flush(from,h))', 'new': 'u => False{}',
     'witness': 'close-gap-parameter', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'term-token-gap-glued', 'file': 'parse.bend',
     'old': 'T.glued(left,right)', 'new': 'True{}',
     'witness': 'arrow-gap-generic', 'phase': 'check',
     'also_witnesses': ['arrow-gap-typed-result', 'term-brace-gap-generic',
                        'pattern-brace-gap-generic', 'arrow-gap-monomorphic',
                        'term-brace-gap-monomorphic', 'pattern-brace-gap-monomorphic'],
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'abstract-type-zero', 'file': 'type-erasure.bend',
     'old': 'case T.Bound{index}: 4294967295', 'new': 'case T.Bound{index}: 0',
     'witness': 'abstract-entry', 'phase': 'host', 'entry': 'identity', 'ordinals': [1],
     'actual': {'exit': 0, 'stdout': 'Evaluated\t0\t1\tGreen{}\n'}},
    {'name': 'late-pattern-parsed', 'file': 'parse-cli.bend',
     'old': 'O.validate(4096n,value)', 'new': 'Done{Unit{}}',
     'witness': 'late-box-pattern', 'also_witnesses': ['late-flag-pattern'], 'phase': 'parse',
     'actual': {'exit': 0, 'contains': 'Parsed\t'}},
    {'name': 'tilde-type-unsupported', 'file': 'type-parse.bend',
     'old': 'S.matches(h,"~"),u =>', 'new': 'False{},u =>',
     'witness': 'tilde-type-argument', 'phase': 'check',
     'actual': {'exit': 3, 'diagnostic': 'Unsupported\tparse\ttype-expression\t'}},
    {'name': 'double-equals-unsupported', 'file': 'parse.bend',
     'old': 'Bool.or(S.matches(h,"="),\n        Bool.or(S.matches(h,"\\n"),',
     'new': 'Bool.or(False{},\n        Bool.or(S.matches(h,"\\n"),',
     'witness': 'double-binding-equals', 'phase': 'check',
     'actual': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tterm-form\t'}},
    {'name': 'multiline-result-invalid', 'file': 'parse.bend',
     'old': 'Bool.or(S.matches(colon,":"),\n              Bool.and(S.matches(colon,"\\n"),starts(S.skip_lines(Con{colon,body}),":")))',
     'new': 'S.matches(colon,":")',
     'witness': 'multiline-result-control', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tfunction-result\t'}},
    {'name': 'constructor-event-unordered', 'file': 'parse-order.bend',
     'old': 'U32.is_lt(p,r)', 'new': 'True{}',
     'witness': 'late-box-pattern', 'also_witnesses': ['late-flag-pattern'], 'phase': 'parse',
     'actual': {'exit': 0, 'contains': 'Parsed\t'}},
    {'name': 'datatype-colon-layout-invalid', 'file': 'parse.bend',
     'old': 'expect(S.skip_lines(tail),":")', 'new': 'expect(tail,":")',
     'witness': 'enum-colon-layout', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-:\t'}},
    {'name': 'generic-colon-layout-invalid', 'file': 'parse.bend',
     'old': 'type_then(T.expression(n,tokens),kind => rest =>\n        S.bind(List<&2,S.Token>,Parsed,expect(S.skip_lines(rest),":"),body =>',
     'new': 'type_then(T.expression(n,tokens),kind => rest =>\n        S.bind(List<&2,S.Token>,Parsed,expect(rest,":"),body =>',
     'witness': 'generic-colon-layout', 'also_witnesses': ['generic-kind-layout'], 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-:\t'}},
    {'name': 'result-arrow-layout-invalid', 'file': 'parse.bend',
     'old': 'run(n,FunctionTail{name,params},S.skip_lines(rest))',
     'new': 'run(n,FunctionTail{name,params},rest)',
     'witness': 'named-arrow-layout', 'also_witnesses': ['applied-arrow-layout'], 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tfunction-result\t'}},
    {'name': 'matched-parent-inferred', 'file': 'generics.bend',
     'old': 'case Binding{name,level,q,typ,param,Some{term}} None{}: C.invalid(Checked,"annotation-required",token)',
     'new': 'case Binding{name,level,q,typ,param,Some{term}} None{}: occurrence(binding,token,env,next)',
     'witness': 'matched-parent-alias-untyped', 'also_witnesses': ['matched-enum-alias-untyped'],
     'phase': 'check', 'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'declaration-name-layout-invalid', 'file': 'parse.bend',
     'old': 'layout_head(S.skip_lines(Con{name,tail}),actual => after =>',
     'new': 'layout_head(Con{name,tail},actual => after =>',
     'witness': 'function-layout-46', 'also_witnesses': ['datatype-layout-37'], 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tdeclaration-name\t'}},
    {'name': 'function-open-layout-invalid', 'file': 'parse.bend',
     'old': 'expect(S.skip_lines(tokens),"(")', 'new': 'expect(tokens,"(")',
     'witness': 'function-layout-47', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-(\t'}},
    {'name': 'generic-is-layout-invalid', 'file': 'parse.bend',
     'old': 'expect(S.skip_lines(rest),"is")', 'new': 'expect(rest,"is")',
     'witness': 'datatype-layout-39', 'also_witnesses': ['datatype-layout-44'], 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-is\t'}},
    {'name': 'parameter-start-layout-invalid', 'file': 'parse.bend',
     'old': 'layout_head(S.skip_lines(tokens),+h => +t =>',
     'new': 'layout_head(tokens,+h => +t =>',
     'witness': 'function-layout-49', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tparameter\t'}},
    {'name': 'parameter-tail-layout-invalid', 'file': 'parse.bend',
     'old': 'layout_head(S.choose(List<&2,S.Token>,parameters,u => S.skip_lines(tokens),u => tokens),+h => +t =>',
     'new': 'layout_head(tokens,+h => +t =>',
     'witness': 'function-layout-50', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\targument-separator\t'}},
    {'name': 'result-start-layout-invalid', 'file': 'parse.bend',
     'old': 'Bool.or(S.matches(typ,"\\n"),Bool.or(T.unsupported_suffix(rest),',
     'new': 'Bool.or(False{},Bool.or(T.unsupported_suffix(rest),',
     'witness': 'result-layout-30', 'also_witnesses': ['function-layout-52'], 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\tfunction-result\t'}},
    {'name': 'applied-type-layout-invalid', 'file': 'type-parse.bend',
     'old': 'Bool.not(starts(S.skip_lines(rest),"<"))',
     'new': 'Bool.not(starts(rest,"<"))',
     'witness': 'type-delimiter-21', 'phase': 'check',
     'actual': {'exit': 2, 'diagnostic': 'Invalid\tparse\targument-separator\t'}},
    {'name': 'newline-header-close-glued', 'file': 'type-parse.bend',
     'old': 'apart(rest,S.skip_lines(end))', 'new': 'apart(rest,end)',
     'witness': 'newline-kind-header-close', 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'newline-named-header-close-glued', 'file': 'parse.bend',
     'old': 'T.apart(Con{typ,Nil{}},S.skip_lines(rest))', 'new': 'False{}',
     'witness': 'newline-named-header-close', 'phase': 'parse',
     'actual': {'exit': 0, 'contains': 'Parsed\t'}},
    {'name': 'newline-is-glue', 'file': 'type-parse.bend',
     'old': 'Bool.and(Bool.not(S.matches(h,"\\n")),glued(h,mark))', 'new': 'glued(h,mark)',
     'witness': 'newline-header-close', 'also_witnesses': ['newline-kind-header-close'], 'phase': 'check',
     'actual': {'exit': 0, 'contains': 'Checked\n'}},
    {'name': 'template-tail-layout-unguarded', 'file': 'parse.bend',
     'old': 'Bool.and(parameters,starts(S.skip_lines(t),"~"))',
     'new': 'Bool.and(parameters,starts(t,"~"))',
     'witness': 'reported-template-second',
     'also_witnesses': ['reported-template-third', 'template-tail-layout',
                        'template-tail-comments', 'template-tail-bare-quantity'],
     'phase': 'check',
     'actual': {'exit': 3, 'diagnostic': 'Unsupported\tparse\ttemplate-binder\t'}},
)
MUTANT_NAMES = {'skipped-substitution', 'erased-argument-live',
                'wrong-quantity-meet', 'missing-arity-check', 'bare-quantity-default',
                'term-argument-invalid', 'empty-family-invalid', 'empty-datatype-invalid',
                'def-reference-free', 'type-level-definition-unknown', 'marked-binder-quantity',
                'pattern-order-forward', 'quantity-gap-glued', 'meet-gap-glued', 'close-gap-glued',
                'term-token-gap-glued', 'abstract-type-zero', 'late-pattern-parsed',
                'tilde-type-unsupported', 'double-equals-unsupported', 'multiline-result-invalid',
                'constructor-event-unordered', 'datatype-colon-layout-invalid',
                'generic-colon-layout-invalid', 'result-arrow-layout-invalid',
                'matched-parent-inferred', 'declaration-name-layout-invalid',
                'function-open-layout-invalid', 'generic-is-layout-invalid',
                'parameter-start-layout-invalid', 'parameter-tail-layout-invalid',
                'result-start-layout-invalid', 'applied-type-layout-invalid',
                'newline-header-close-glued', 'newline-named-header-close-glued', 'newline-is-glue',
                'template-tail-layout-unguarded'}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=60):
    command = [str(x) for x in argv]
    try:
        process = subprocess.run(command, cwd=ROOT, env=ENV, text=True,
                                 capture_output=True, timeout=timeout * TIMEOUT_SCALE)
    except subprocess.TimeoutExpired:
        return {'argv': command, 'exit': None, 'outcome': 'harness-timeout',
                'stdout': '', 'stderr': ''}
    result = {'argv': command, 'exit': process.returncode,
              'stdout': process.stdout, 'stderr': process.stderr}
    outcomes = {0: 'success', 2: 'invalid', 3: 'unsupported', 4: 'exhausted',
                5: 'host-failure', 6: 'internal-failure'}
    result['outcome'] = outcomes.get(process.returncode, 'process-failure')
    return result


def successful(argv, timeout=60):
    result = run(argv, timeout)
    require(result['exit'] == 0 and result['stderr'] == '', result)
    return result


def build(entry, executable):
    """Reuse only byte-verified builds of this entry, sources and host toolchain."""
    cache = BUILD / 'build-cache'
    cache.mkdir(exist_ok=True)
    library = Path(ENV.get('BEND_LIB', str(Path.home() / '.bend/lib')))
    sources = set((ROOT / 'src').glob('*.bend')) | set(entry.parent.glob('*.bend')) | {entry, COMPILE}
    sources.update((ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / name)
                   for name in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend'))
    for package in library.glob('0x*'):
        sources.update(p for p in package.rglob('*') if p.is_file() and
                       p.suffix in ('.bend', '.c', '.h', '.ts', '.js', '.wasm') and
                       not any(part == '.env' or part.startswith('.env.') for part in p.parts))
    native = executable.suffix != '.js'
    identity = {'entry': str(entry), 'native': native,
                'sources': {str(p): digest(p) for p in sorted(sources)},
                'bun': successful(['bun', '--version'])['stdout'],
                'host': {k: ENV.get(k) for k in ('CC', 'SDKROOT', 'DEVELOPER_DIR')}}
    if native:
        identity['clang'] = successful([ENV.get('CC', 'clang'), '--version'])['stdout']
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    artifact, receipt = cache / key, cache / (key + '.json')
    command = [*SEED, entry, '-o', executable]
    if artifact.is_file() and receipt.is_file():
        saved = json.loads(receipt.read_text())
        if saved['sha256'] == digest(artifact):
            shutil.copy2(artifact, executable)
            return {**saved['result'], 'argv': [str(x) for x in command], 'cached': True}
    result = successful(command, timeout=120)
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temporary:
        staging = Path(temporary.name)
    shutil.copy2(executable, staging)
    staging.replace(artifact)
    receipt.write_text(json.dumps({'sha256': digest(artifact), 'result': result}) + '\n')
    return {**result, 'cached': False}


def host_controls(rows):
    controls = json.loads(HOST_EXPECTATIONS.read_text())['controls']
    indexed = {row['case']['name']: row for row in rows}
    require(controls, 'nonempty host controls')
    for control in controls:
        require(indexed[control['case']]['case']['knot']['require'] == 'agree', control)
        require(control['exit'] == 5 and control['diagnostic'] ==
                'HostFailure\tinvoke\tabstract-signature\n', control)
    return controls


def host_result(actual, control):
    require(actual['exit'] == control['exit'] and actual['stdout'] == ''
            and actual['stderr'] == control['diagnostic'], (control, actual))


def host_observations(rows, lanes):
    indexed = {row['case']['name']: row for row in rows}
    observations = []
    for control in host_controls(rows):
        for lane, commands in lanes.items():
            actual = run([*commands['eval'], indexed[control['case']]['source'],
                          control['entry'], 1048576, *control['ordinals']])
            host_result(actual, control)
            observations.append({'control': control, 'lane': lane, 'result': actual})
    return observations


def checked(result):
    require(result['exit'] == 0 and result['stderr'] == ''
            and result['stdout'].startswith('Checked\n'), result)


def rejection(result, requirement):
    expected = requirement.get('exit')
    statuses = (expected,) if expected is not None else (
        (3,) if requirement['require'] in ('unsupported', 'agree-or-unsupported') else (2, 3))
    require(result['exit'] in statuses and result['stdout'] == '', (requirement, result))
    prefix = {2: 'Invalid', 3: 'Unsupported'}[result['exit']]
    require(re.match(prefix + r'\t[a-z]+\t[a-z-]+\t', result['stderr']), result)
    if 'diagnostic' in requirement:
        require(result['stderr'].startswith(requirement['diagnostic']), (requirement, result))


def evaluated(result, call):
    wanted = call['result']
    expression = (r'Evaluated\t[0-9]+\t' + str(wanted['tag']) + r'\t'
                  + re.escape(wanted['constructor']) + r'\{\}\n')
    require(result['exit'] == 0 and result['stderr'] == ''
            and re.fullmatch(expression, result['stdout']), (wanted, result))


def wasm_result(result, call, output):
    require(result['exit'] == 0 and result['stderr'] == '', result)
    observed = json.loads(result['stdout'])
    require(observed == {'validated': True, 'export': call['entry'],
                         'arguments': call['ordinals'], 'result': call['result']['tag'],
                         'bytes': output.stat().st_size}, (call, observed))


def compiled(result, output):
    require(result['exit'] == 0 and result['stderr'] == '', result)
    require(output.read_bytes().startswith(b'\0asm\x01\0\0\0'), ('Wasm header', result))
    require(result['stdout'] == f'Built\t{output.stat().st_size}\n', result)


def abi_result(result, controls, output):
    require(result['exit'] == 0 and result['stderr'] == '', result)
    expected = {'validated': True, 'arities': {row['export']: row['arity'] for row in controls},
                'bytes': output.stat().st_size}
    require(json.loads(result['stdout']) == expected, (expected, result))


def abi_controls(rows):
    controls = json.loads(ABI_EXPECTATIONS.read_text())['controls']
    require(controls and len({(row['case'], row['export']) for row in controls}) == len(controls),
            'distinct, nonempty ABI controls')
    indexed = {row['case']['name']: row for row in rows}
    for control in controls:
        row = indexed[control['case']]
        require(row['case']['knot']['require'] == 'agree', ('ABI needs a mandatory agreement', control))
        require(row['reference']['source_sha256'] == control['source_sha256'], control)
        require(control['declaration'] in row['source'].read_text().splitlines(), control)
        require(type(control['arity']) is int and control['arity'] >= 0 and control['justification'], control)
    return controls


def abi_observations(controls, lanes):
    records = []
    for name in dict.fromkeys(row['case'] for row in controls):
        selected = [row for row in controls if row['case'] == name]
        for lane in lanes:
            output = BUILD / f'{name}-{lane}.wasm'
            result = run(['node', ABI_HOST, output, *[row['export'] for row in selected]])
            abi_result(result, selected, output)
            records.append({'case': name, 'lane': lane, 'controls': selected, 'result': result})
    return records


def corpus():
    rows, names = [], set()
    for directory in SOURCES:
        document = json.loads((directory / 'expectations.json').read_text())
        observations = {row['case']: row for row in document['observations']['fixtures']}
        require(len(observations) == len(document['cases']), 'fixture observation inventory')
        for case in document['cases']:
            name = case['name']
            require(name not in names, ('duplicate fixture name', name))
            names.add(name)
            source = directory / case['file']
            reference = observations[name]
            require(digest(source) == reference['source_sha256'], (name, 'frozen source hash'))
            rows.append({'case': case, 'source': source, 'reference': reference})
    return rows


def fixture(row, lanes):
    case, source, reference = row['case'], row['source'], row['reference']
    requirement = case['knot']
    record = {'name': case['name'], 'requirement': requirement,
              'source': str(source.relative_to(ROOT)), 'source_sha256': digest(source),
              'seed_calls': len(reference['calls']), 'lanes': {}, 'status': 'incomplete'}
    modules, dispositions = {}, []
    for lane, commands in lanes.items():
        output = BUILD / f'{case["name"]}-{lane}.wasm'
        output.write_bytes(MARKER)
        actual = {'check': run([*commands['check'], source]),
                  'compile': run([*commands['compile'], source, output]), 'calls': []}
        record['lanes'][lane] = actual
        try:
            agrees = requirement['require'] == 'agree' or (
                requirement['require'] == 'agree-or-unsupported' and actual['check']['exit'] == 0)
            if agrees:
                checked(actual['check'])
                compiled(actual['compile'], output)
                require(reference['calls'], (case['name'], 'agreement has no frozen calls'))
                actual['module_sha256'] = digest(output)
                actual['disassembly'] = successful(['wasm2wat', output])
                for call in reference['calls']:
                    result = {'entry': call['entry'], 'ordinals': call['ordinals'],
                              'expected': call['result'],
                              'eval': run([*commands['eval'], source, call['entry'],
                                           1048576, *call['ordinals']]),
                              'wasm': run(['node', HOST, PROFILE, output, call['entry'],
                                           *call['ordinals']])}
                    actual['calls'].append(result)
                    evaluated(result['eval'], call)
                    result['evaluator_agreed'] = True
                    wasm_result(result['wasm'], call, output)
                    result['wasm_agreed'] = True
                modules[lane] = output.read_bytes()
                disposition = 'agreed'
            else:
                actual['eval'] = run([*commands['eval'], source, 'main', 1048576])
                for phase in ('check', 'eval', 'compile'):
                    rejection(actual[phase], requirement)
                require(output.read_bytes() == MARKER, (case['name'], 'rejection changed output'))
                actual['artifact_preserved'] = True
                disposition = 'rejected' if requirement['require'] == 'reject' else 'unsupported'
            actual['disposition'] = disposition
            dispositions.append(disposition)
        except (AssertionError, ValueError) as error:
            # A required capability remains a failure, even when Unsupported is
            # the honest source classification. Retain the unavailable needs.
            blocked = requirement['require'] == 'agree' and any(
                actual[phase]['exit'] == 3 for phase in ('check', 'compile'))
            actual['status'] = 'blocked' if blocked else 'failed'
            actual['failure'] = repr(error)
            if blocked:
                actual['requires'] = case.get('requires', case.get('needs', []))
            dispositions.append(actual['status'])
    if modules and len(modules) == len(lanes):
        require(len(set(modules.values())) == 1, (case['name'], 'native/Bun Wasm bytes differ'))
        record['module_bytes_identical'] = True
    record['status'] = dispositions[0] if len(set(dispositions)) == 1 else 'failed'
    return record


def observe_literal(actual, expected):
    require(actual['exit'] == expected['exit'], (expected, actual))
    if 'diagnostic' in expected:
        require(actual['stdout'] == '' and actual['stderr'].startswith(expected['diagnostic']),
                (expected, actual))
    else:
        require(actual['stderr'] == '', (expected, actual))
    if 'stdout' in expected:
        require(actual['stdout'] == expected['stdout'], (expected, actual))
    if 'contains' in expected:
        require(expected['contains'] in actual['stdout'], (expected, actual))
    if 'result' in expected:
        require(json.loads(actual['stdout'])['result'] == expected['result'], (expected, actual))
    if 'arities' in expected:
        require(json.loads(actual['stdout'])['arities'] == expected['arities'], (expected, actual))


def mutation(spec, rows, controls, sources=None):
    name, phase = spec['name'], spec['phase']
    require(phase in ('parse', 'check', 'eval', 'wasm', 'abi', 'host'), (name, 'mutation phase'))
    row = rows[spec['witness']]
    directory = BUILD / name
    directory.mkdir(exist_ok=True)
    for source in (sources or ROOT / 'src').glob('*.bend'):
        shutil.copy2(source, directory / source.name)
    target = directory / spec['file']
    original = target.read_text()
    require(original.count(spec['old']) == 1, (name, 'mutation anchor is not unique'))
    target.write_text(original.replace(spec['old'], spec['new']))
    if phase in ('wasm', 'abi'):
        entry = directory / 'fields-compile.bend'
        entry.write_text(COMPILE.read_text().replace('../../src/', './'))
    else:
        entry = directory / f'{"eval" if phase == "host" else phase}-cli.bend'
    typecheck = successful([*SEED, entry, '--check-only'])
    require(typecheck['stdout'] == 'All terms check.\n', typecheck)
    record = {**spec, 'source_sha256': digest(target), 'typecheck': typecheck, 'lanes': {}}
    call, selected = None, None
    if phase == 'abi':
        selected = [control for control in controls if control['case'] == spec['witness']
                    and control['export'] in spec['exports']]
        require(len(selected) == len(spec['exports']), (name, 'ABI witness must be frozen'))
        record['expected'] = selected
    elif phase == 'host':
        selected = [control for control in host_controls(list(rows.values()))
                    if control['case'] == spec['witness'] and control['entry'] == spec['entry']
                    and control['ordinals'] == spec['ordinals']]
        require(len(selected) == 1, (name, 'host witness must be frozen'))
        record['expected'] = selected[0]
    elif phase not in ('parse', 'check'):
        calls = [call for call in row['reference']['calls'] if call['entry'] == spec['entry']
                 and call['ordinals'] == spec['ordinals']]
        require(len(calls) == 1, (name, 'mutant witness must be one frozen call'))
        call = calls[0]
        record['expected'] = call['result']
    else:
        record['expected'] = row['case']['parse'] if phase == 'parse' else row['case']['knot']
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        executable = directory / ('mutant' + suffix)
        built = build(entry, executable)
        command = [*runtime, executable]
        item = {'build': built, 'sha256': digest(executable)}
        if phase in ('parse', 'check'):
            actual = run([*command, row['source']])
        elif phase == 'eval':
            actual = run([*command, row['source'], call['entry'], 1048576, *call['ordinals']])
        elif phase == 'host':
            actual = run([*command, row['source'], spec['entry'], 1048576, *spec['ordinals']])
        else:
            output = directory / f'{lane}.wasm'
            output.write_bytes(MARKER)
            item['compile'] = run([*command, row['source'], output])
            compiled(item['compile'], output)
            if phase == 'abi':
                actual = run(['node', ABI_HOST, output, *spec['exports']])
            else:
                actual = run(['node', HOST, PROFILE, output, call['entry'], *call['ordinals']])
        item['actual'] = actual
        observe_literal(actual, spec['actual'])
        require(actual['exit'] in (0, 2, 3), (name, 'host failure or exhaustion is not a semantic kill'))
        try:
            if phase == 'parse':
                observe_literal(actual, row['case']['parse'])
            elif phase == 'check':
                if row['case']['knot']['require'] == 'agree':
                    checked(actual)
                else:
                    rejection(actual, row['case']['knot'])
            elif phase == 'eval':
                evaluated(actual, call)
            elif phase == 'wasm':
                wasm_result(actual, call, output)
            elif phase == 'host':
                host_result(actual, selected[0])
            else:
                abi_result(actual, selected, output)
        except AssertionError:
            item['outcome'] = 'semantic-kill'
        else:
            raise AssertionError((name, lane, 'mutant survived'))
        item['additional_kills'] = []
        for witness in spec.get('also_witnesses', []):
            twin = rows[witness]
            observed = run([*command, twin['source']])
            observe_literal(observed, spec['actual'])
            try:
                if phase == 'parse':
                    observe_literal(observed, twin['case']['parse'])
                else:
                    rejection(observed, twin['case']['knot'])
            except AssertionError:
                item['additional_kills'].append({'witness': witness, 'actual': observed,
                                                 'outcome': 'semantic-kill'})
            else:
                raise AssertionError((name, lane, witness, 'mutant survived'))
        record['lanes'][lane] = item
    return record


def coverage(record):
    fixtures = record['fixtures']
    lane_rows = [lane for row in fixtures for lane in row['lanes'].values()]
    probes = record.get('prechecks', {})
    return {
        'fixtures': len(fixtures), 'seed_calls': sum(row['seed_calls'] for row in fixtures),
        'seed_valid': sum(row['requirement']['require'] != 'reject' for row in fixtures),
        'seed_invalid': sum(row['requirement']['require'] == 'reject' for row in fixtures),
        'agreed_fixtures': sum(row['status'] == 'agreed' for row in fixtures),
        'rejected_fixtures': sum(row['status'] == 'rejected' for row in fixtures),
        'unsupported_fixtures': sum(row['status'] == 'unsupported' for row in fixtures),
        'blocked_fixtures': sum(row['status'] == 'blocked' for row in fixtures),
        'check_observations': len(lane_rows), 'compile_observations': len(lane_rows),
        'evaluator_agreements': sum(call.get('evaluator_agreed', False)
                                    for row in lane_rows for call in row['calls']),
        'wasm_agreements': sum(call.get('wasm_agreed', False)
                              for row in lane_rows for call in row['calls']),
        'negative_phase_observations': 3 * sum('eval' in row for row in lane_rows),
        'preserved_artifacts': sum(row.get('artifact_preserved', False) for row in lane_rows),
        'byte_identical_modules': sum(row.get('module_bytes_identical', False) for row in fixtures),
        'abi_module_probes': len(record['abi']),
        'abi_arity_observations': sum(len(row['controls']) for row in record['abi']),
        'execution_lanes': len({lane for row in fixtures for lane in row['lanes']}),
        'proof_entries': len(record['proofs']),
        'host_refusals': len(record.get('host', [])),
        'mutants': len(record['mutants']),
        'mutant_lane_kills': sum(len(row['lanes']) for row in record['mutants']),
        'additional_mutant_witness_kills': sum(len(lane.get('additional_kills', []))
                                              for row in record['mutants'] for lane in row['lanes'].values()),
        'precheck_fixtures': len(probes.get('fixtures', [])),
        **{'precheck_' + key: probes.get(key, 0) for key in (
            'seed_parse_observations', 'seed_check_observations', 'seed_runs',
            'lane_observations', 'preserved_artifacts', 'evaluator_agreements',
            'wasm_agreements', 'byte_identical_modules', 'seed_constructor_observations',
            'boxed_module_validations')},
    }


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'profile': 'knot-generics-1',
              'fixtures': [], 'proofs': [], 'mutants': [], 'abi': [], 'host': []}
    try:
        inputs = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
                  ROOT / 'src/CONTRACT.json', HOST, COMPILE, ABI_EXPECTATIONS, HOST_EXPECTATIONS, Path(__file__)]
        for directory in SOURCES:
            inputs += [directory / 'expectations.json', directory / 'regen.py',
                       *sorted((directory / 'fixtures').glob('*.bend'))]
        inputs += [HERE / 'prechecks' / name for name in
                   ('expectations.json', 'reported-expectations.json', 'review-r0-expectations.json',
                    'review-r0-layout-guards.json', 'review-r0-named-guard.json',
                    'template-tail-expectations.json', 'TEMPLATE-TAIL.md', 'seed-parse.ts', 'seed-value.ts',
                    'check.py', 'README.md', 'SPEC.md', 'REPORTED.md')]
        inputs += sorted((HERE / 'prechecks/fixtures').glob('*.bend'))
        record['inputs'] = {str(path.relative_to(ROOT)): digest(path) for path in inputs}
        record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
                           for tool in ('bun', 'node', 'python3', 'wasm2wat')}
        with ThreadPoolExecutor(max_workers=4) as pool:
            record['reference'] = list(pool.map(lambda directory: successful(['python3', directory / 'regen.py']), SOURCES))
        rows = corpus()
        controls = abi_controls(rows)
        ABI_HOST.write_text(ABI_SOURCE)
        record['abi_host_sha256'] = digest(ABI_HOST)
        record['seed_revision'] = json.loads((HERE / 'expectations.json').read_text())['seed']['revision']
        for proof in PROOFS:
            result = successful([*SEED, ROOT / proof])
            require(result['stdout'] == 'All terms check.\n', result)
            record['proofs'].append({'entry': proof, 'result': result})
        record['builds'], lanes = [], {}
        jobs = []
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            lanes[lane] = {}
            for phase in ('parse', 'check', 'eval', 'compile'):
                entry = COMPILE if phase == 'compile' else ROOT / f'src/{phase}-cli.bend'
                executable = BUILD / (phase + suffix)
                lanes[lane][phase] = [*runtime, executable]
                jobs.append((lane, phase, entry, executable))
        def build_cli(job):
            lane, phase, entry, executable = job
            return {'lane': lane, 'phase': phase, 'result': build(entry, executable),
                    'sha256': digest(executable)}
        with ThreadPoolExecutor(max_workers=2) as pool:
            record['builds'] = list(pool.map(build_cli, jobs))
        for row in rows:
            record['fixtures'].append(fixture(row, lanes))
        failed = [(row['name'], row['status']) for row in record['fixtures']
                  if row['status'] not in ('agreed', 'rejected', 'unsupported')]
        require(not failed, ('fixture failures', failed))
        record['prechecks'] = precheck_replay(sys.modules[__name__], lanes)
        record['abi'] = abi_observations(controls, lanes)
        record['host'] = host_observations(rows, lanes)
        require({spec['name'] for spec in MUTANTS} == MUTANT_NAMES and len(MUTANTS) == len(MUTANT_NAMES),
                'Each required semantic mutant must be configured exactly once')
        indexed = {row['case']['name']: row for row in rows}
        indexed.update({row['case']['name']: row for row in precheck_rows(sys.modules[__name__])[1]})
        with ThreadPoolExecutor(max_workers=2) as pool:
            record['mutants'] = list(pool.map(lambda spec: mutation(spec, indexed, controls), MUTANTS))
        require(all(digest(ROOT / path) == expected for path, expected in record['inputs'].items()),
                'Inputs changed during gate')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        record['counts'] = coverage(record)
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    counts = record['counts']
    print(f"Generics gate passed: {counts['fixtures']} fixtures, {counts['seed_calls']} seed calls, "
          f"{counts['evaluator_agreements']} evaluator and {counts['wasm_agreements']} Node agreements, "
          f"{counts['negative_phase_observations']} negative phase observations, "
          f"{counts['preserved_artifacts']} preserved artifacts, "
          f"{counts['byte_identical_modules']} byte-identical module pairs, "
          f"{counts['abi_arity_observations']} independent ABI arity observations, "
          f"{counts['proof_entries']} complete proof entries, "
          f"{counts['mutants']} type-correct mutants killed in both lanes. {RECEIPT}")


if __name__ == '__main__':
    main()
