#!/usr/bin/env python3
"""Drive the seed, two Bend builds and Node; decode with wasm2wat. No emitter."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
TIMEOUT_SCALE = float(__import__('os').environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-fields-wasm/gate'
GENERATED = HERE / 'generated'
RECEIPT = HERE / 'receipts/fields-wasm.json'
SEED = ROOT / 'scripts/bend-reference'
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-fields-wasm-1'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=60*TIMEOUT_SCALE):
    try:
        result = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                                capture_output=True, timeout=timeout)
        return {'argv': [str(x) for x in argv], 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def diagnostic(result, status, prefix):
    require(result['exit'] == status and result['stderr'].startswith(prefix)
            and result['stdout'] == '', (prefix, result))


def compiled(command, source, output, budgets=()):
    output.unlink(missing_ok=True)
    result = successful([*command, source, output, *budgets])
    require(result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
    return result


def sections(data):
    require(data[:8] == b'\0asm\x01\0\0\0', 'binary header')
    at, ids = 8, []
    while at < len(data):
        ids.append(data[at]); at += 1
        length = 0
        for shift in range(0, 35, 7):
            byte = data[at]; at += 1
            length |= (byte & 127) << shift
            if byte < 128:
                break
        else:
            raise AssertionError('section LEB width')
        require(length <= 4294967295 and at + length <= len(data), 'section size')
        at += length
    require(at == len(data), 'section boundary')
    return ids


def instructions(wat, heap):
    allowed = {'local.get', 'local.set', 'i32.const', 'call', 'i32.eq', 'if', 'else', 'end'}
    if heap:
        allowed |= {'global.get', 'global.set', 'i32.load', 'i32.store', 'i32.add',
                    'i32.sub', 'i32.gt_u', 'unreachable'}
    observed, traps = set(), 0
    for line in wat.splitlines():
        line = line.strip()
        if not line or line == ')' or line.startswith(('(module', '(type', '(func',
                '(export', '(local', '(memory', '(global', ';;')):
            continue
        opcode = line.split()[0].rstrip(')')
        require(opcode in allowed, ('instruction outside profile', line))
        observed.add(opcode); traps += opcode == 'unreachable'
    require(traps == int(heap), ('arena is the only unreachable', traps, heap))
    require(wat.count('(memory ') == int(heap) and wat.count('(global ') == int(heap), 'heap sections')
    if heap:
        require('(memory (;0;) 1 1)' in wat, 'one fixed memory page')
        require('(global (;0;) (mut i32) (i32.const 0))' in wat, 'initial bump')
    exports = re.findall(r'\(export "[^"]+" \(func (\d+)\)\)', wat)
    functions = re.findall(r'^  \(func ', wat, re.M)
    require([int(i) for i in exports] == list(range(len(functions) - int(heap))), 'index-stable function exports')
    return sorted(observed)


MUTANTS = [
    ('swapped-field-offsets', 'memory(cap,54,offset)',
     'memory(cap,54,Bool.pick(U32,U32.is_eq(offset,4),8,4))', 'pair', 'direct', [0, 1], 0),
    ('stored-erased-slot',
     'u => lower(n,Cell{tail,params,slots,tag},heap,functions,locals,next,cap),u =>',
     'u => lower(n,Cell{tail,params,Con{next,slots},tag},heap,functions,locals,U32.add(next,1),cap),u =>',
     'erased', 'observe', [0, 1], 1),
    ('wrong-cell-tag', 'constant(cap,tag),memory(cap,54,0)',
     'constant(cap,0),memory(cap,54,0)', 'erased', 'ghost', [], 1),
    ('no-pointer-bump', 'instruction(cap,32,0),W.bytes(cap,[106])',
     'constant(cap,0),W.bytes(cap,[106])', 'aliasing', 'observe', [0, 1], 0),
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    manifest = json.loads((HERE / 'cases.json').read_text())
    baseline = json.loads((HERE / 'enum-baseline.json').read_text())
    expectations = json.loads((HERE / 'expectations.json').read_text())
    cases = {c['name']: c for c in manifest['cases']}
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'profile': 'knot-fields-wasm-1',
              'seed_revision': manifest['seed_revision']}
    try:
        paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
                 ROOT / 'src/CONTRACT.json', HOST, *sorted(HERE.glob('*.bend')),
                 *sorted(HERE.glob('*.json')), *sorted(HERE.glob('*.mjs')), Path(__file__),
                 *sorted((HERE / 'fixtures').glob('*.bend')), *[ROOT / f for f in baseline]]
        record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in paths}
        record['seed'] = {f: digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / f)
                          for f in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')}
        record['tools'] = {t: successful([t, '--version'])['stdout'].strip()
                           for t in ('bun', 'node', 'python3', 'wasm2wat')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        require(len(baseline) == 25, 'frozen enum corpus')
        frozen = [(c['name'], call, digest(HERE / c['file'])) for c in cases.values() for call in c['calls']]
        require(frozen == [(o['case'], o['call'], o['source_sha256']) for o in expectations['observations']], 'expectations or fixtures drifted')
        record['proof'] = successful([SEED, HERE / 'PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['new_laws'] = 5
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            lanes[lane] = {}
            for phase, entry in [('compile', HERE / 'compile.bend'), ('eval', ROOT / 'src/eval-cli.bend')]:
                output = BUILD / (phase + suffix)
                result = successful([SEED, entry, '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'result': result, 'sha256': digest(output)})
                lanes[lane][phase] = [*runtime, output]
        record['enum_preservation'] = []
        for source, expected in baseline.items():
            for lane, commands in lanes.items():
                output = BUILD / f'enum-{Path(source).stem}-{lane}.wasm'
                result = compiled(commands['compile'], ROOT / source, output)
                require(digest(output) == expected, ('enum bytes changed', source, lane))
                require(sections(output.read_bytes()) == [1, 3, 7, 10], 'enum section contract')
                record['enum_preservation'].append({'source': source, 'lane': lane, 'compile': result, 'sha256': digest(output)})
        record['fixtures'], modules = [], {}
        for case in cases.values():
            name, path = case['name'], HERE / case['file']
            item = {'name': name, 'reference': [], 'lanes': {}}
            for i, call in enumerate(case['calls']):
                wrapper = BUILD / f'{name}-reference-{i}.bend'
                imported = os.path.relpath(path, wrapper.parent)
                wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.{case["type"]}:\n  {call["seed"]}\n')
                result = successful([SEED, wrapper])
                expected = imported.removesuffix('.bend') + '.' + case['constructors'][call['tag']] + '{}'
                require(result['stdout'].strip() == expected, (expected, result))
                item['reference'].append({'call': call, 'result': result})
            modules[name] = {}
            for lane, commands in lanes.items():
                output = BUILD / f'{name}-{lane}.wasm'
                built = compiled(commands['compile'], path, output, case.get('compile_budgets', []))
                modules[name][lane] = output
                observations = []
                for call in case['calls']:
                    evaluated = run([*commands['eval'], path, call['export'], 1048576, *call['arguments']])
                    if 'eval_exhausted' in case:
                        diagnostic(evaluated, 4, case['eval_exhausted'])
                    else:
                        expected = f'Evaluated\t{case["type_id"]}\t{call["tag"]}\t{case["constructors"][call["tag"]]}{{}}'
                        require(evaluated['exit'] == 0 and evaluated['stdout'].strip() == expected, (expected, evaluated))
                    wasm = run(['node', HOST, PROFILE, output, call['export'], *call['arguments']])
                    if name == 'arena-overflow':
                        diagnostic(wasm, 4, manifest['arena']['diagnostic'])
                    else:
                        require(wasm['exit'] == 0 and json.loads(wasm['stdout'])['result'] == call['tag'], (call, wasm))
                    observations.append({'call': call, 'evaluator': evaluated, 'wasm': wasm})
                item['lanes'][lane] = {'compile': built, 'sha256': digest(output), 'observations': observations}
                if lane == 'native':
                    heap = name not in ('deep-call', 'deep-stack')
                    require(sections(output.read_bytes()) == ([1, 3, 5, 6, 7, 10] if heap else [1, 3, 7, 10]), 'section profile')
                    wat = successful(['wasm2wat', output])['stdout']
                    item['instructions'] = instructions(wat, heap)
                    item['sections'] = sections(output.read_bytes())
                    shutil.copy2(output, GENERATED / (name + '.wasm'))
                    (GENERATED / (name + '.wat')).write_text(wat)
                else:
                    require(output.read_bytes() == modules[name]['native'].read_bytes(), (name, 'native/Bun byte mismatch'))
            record['fixtures'].append(item)
        record['boundaries'] = []
        for lane in lanes:
            # A shallow positive control separates Node startup from invocation exhaustion.
            for name, status in [('pair', 0), ('deep-stack', 4)]:
                result = run(['node', *manifest['stack']['node_flags'], HOST, PROFILE, modules[name][lane], 'main'])
                if status == 4:
                    diagnostic(result, 4, manifest['stack']['diagnostic'])
                else:
                    require(result['exit'] == 0 and json.loads(result['stdout'])['result'] == 1, result)
                record['boundaries'].append({'name': 'stack-' + name, 'lane': lane, 'result': result})
            for name, export, count, tag, args in [('arena-overflow', 'f0', 8192, 1, []),
                    ('erased', 'ghost', 16384, 1, []), ('erased', 'empty', 16384, 0, []),
                    ('pair', 'direct', 5461, 0, [0, 1])]:
                result = successful(['node', HERE / 'arena.mjs', modules[name][lane], export, count, tag, *args])
                require(json.loads(result['stdout']) == {'successful': count, 'overflow': count + 1, 'repeatedOverflow': True}, result)
                record['boundaries'].append({'name': 'arena-' + export, 'lane': lane, 'result': result})
            pair = modules['pair'][lane]
            bad = BUILD / 'invalid.wasm'; bad.write_bytes(b'not wasm')
            for label, args in [('missing-file', [PROFILE, BUILD / 'absent.wasm', 'main']),
                    ('invalid-module', [PROFILE, bad, 'main']),
                    ('unknown-profile', ['--profile=missing', pair, 'main']),
                    ('missing-export', [PROFILE, pair, 'absent']),
                    ('wrong-arity', [PROFILE, pair, 'direct', 0]),
                    ('argument-range', [PROFILE, pair, 'direct', 256, 0]),
                    ('unreachable-outside-fields-profile', [modules['arena-overflow'][lane], 'main'])]:
                result = run(['node', HOST, *args]); diagnostic(result, 5, 'HostFailure\twasm\t')
                record['boundaries'].append({'name': label, 'lane': lane, 'result': result})
            for label, budgets in [('emitter-depth', [65536, 512, 512, 0, 65536]),
                                   ('output-capacity', [65536, 512, 512, 4096, 32])]:
                output = BUILD / f'{label}-{lane}.wasm'; output.write_bytes(b'stale')
                result = run([*lanes[lane]['compile'], HERE / cases['pair']['file'], output, *budgets])
                diagnostic(result, 4, 'Exhausted\temit\t')
                require(output.read_bytes() == b'stale', 'exhaustion changed output')
                record['boundaries'].append({'name': label, 'lane': lane, 'result': result, 'artifact_preserved': True})
        record['mutants'] = []
        for name, old, new, witness, export, args, expected in MUTANTS:
            directory = BUILD / name; directory.mkdir(exist_ok=True)
            for source in (ROOT / 'src').glob('*.bend'):
                shutil.copy2(source, directory / source.name)
            target = directory / 'wasm.bend'; source = target.read_text()
            require(source.count(old) == 1, (name, 'unique mutation'))
            target.write_text(source.replace(old, new))
            entry = directory / 'entry.bend'
            entry.write_text((HERE / 'compile.bend').read_text().replace('../../src/', './'))
            checked = successful([SEED, entry, '--check-only'])
            require(checked['stdout'].strip() == 'All terms check.', checked)
            item = {'name': name, 'old': old, 'new': new, 'source_sha256': digest(target),
                    'typecheck': checked, 'witness': witness, 'export': export,
                    'arguments': args, 'expected_tag': expected, 'lanes': {}}
            require(any(c['export'] == export and c['arguments'] == args and c['tag'] == expected
                        for c in cases[witness]['calls']), 'mutant expectation must be frozen')
            for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
                executable = directory / ('mutant' + suffix)
                built = successful([SEED, entry, '-o', executable])
                output = directory / f'{lane}.wasm'
                emission = compiled([*runtime, executable], HERE / cases[witness]['file'], output)
                successful(['wasm2wat', output])
                actual = successful(['node', HOST, PROFILE, output, export, *args])
                require(json.loads(actual['stdout'])['result'] != expected, (name, 'mutant survived'))
                item['lanes'][lane] = {'build': built, 'emission': emission, 'actual': actual, 'outcome': 'semantic-kill'}
            record['mutants'].append(item)
        record['generated'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(GENERATED.iterdir())}
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'inputs changed during gate')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print(f"Fields Wasm gate passed: {len(cases)} fixtures, {len(expectations['observations'])} seed calls, "
          f"{2 * len(expectations['observations'])} evaluator and {2 * len(expectations['observations'])} Node observations, "
          f"{len(record['enum_preservation'])} frozen enum-byte checks, {len(record['boundaries'])} boundary probes, "
          f"{len(record['mutants'])} type-correct mutants killed in both lanes; 5 new checked laws. {RECEIPT}")


if __name__ == '__main__':
    main()
