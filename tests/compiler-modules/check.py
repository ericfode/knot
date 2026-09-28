#!/usr/bin/env python3
"""Drive the frozen seed oracle, Bend CLIs and Wasm; no language semantics."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-modules/gate'
BUNDLE = HERE / 'bundle/lib'
RECEIPT = HERE / 'receipts/modules.json'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
HOST = ROOT / 'scripts/run-wasm.mjs'
PROOFS = ['src/load-PROOF.bend', 'src/qualify-PROOF.bend', 'src/base-load-PROOF.bend',
          'src/base-pin-PROOF.bend']
OUTCOMES = {2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted',
            5: 'HostFailure', 6: 'InternalFailure'}
# Literal review of the frozen fixtures and pinned Bool definitions, before
# running the loader audit. All user definitions contribute Base roots.
BASE_SLICES = {
    'base-bool': {'Bool', 'Bool.not', 'Bool.and', 'Bool.or', 'Bool.xor'},
    'base-transitive': {'Bool', 'Bool.not'},
    'base-after-module': {'Bool'},
}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment(bundle=BUNDLE):
    env = {k: v for k, v in os.environ.items() if not k.startswith('BEND_')}
    env.update(BEND_NO_TELEMETRY='1', BEND_LIB=str(bundle),
               BEND_HUB=(HERE / 'bundle/hub').as_uri(), BEND_ORIGIN='offline://disabled')
    return env


def run(argv, timeout=180, bundle=BUNDLE, cwd=ROOT):
    command = [str(x) for x in argv]
    try:
        result = subprocess.run(command, cwd=cwd, env=environment(bundle), text=True,
                                capture_output=True, timeout=timeout)
        return {'argv': command, 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': command, 'exit': None, 'outcome': 'harness-timeout',
                'budget_seconds': timeout, 'stdout': '', 'stderr': ''}
    except OSError as error:
        return {'argv': command, 'exit': None, 'outcome': 'host-launch-failure',
                'stdout': '', 'stderr': str(error)}


def successful(argv, timeout=180, bundle=BUNDLE, cwd=ROOT):
    result = run(argv, timeout, bundle, cwd)
    require(result['exit'] == 0, result)
    return result


def rejection(result, status, prefix=None):
    require(result['exit'] == status and result['stdout'] == '', result)
    parts = result['stderr'].strip().split('\t')
    require(len(parts) >= 3 and parts[0] == OUTCOMES[status]
            and parts[1] and parts[2], result)
    if prefix:
        require(result['stderr'].startswith(prefix), (prefix, result))
    return '\t'.join(parts[:3])


def observe(result, fixture):
    """Return True only for acceptance permitted by the frozen obligation."""
    obligation = fixture['knot']['obligation']
    if obligation == 'reject':
        expected = fixture['knot']
        rejection(result, expected['exit'], expected.get('diagnostic_prefix', expected['outcome'] + '\t'))
    elif obligation == 'knot_expected':
        expected = fixture['knot_expected']
        rejection(result, expected['exit'], expected['diagnostic_prefix'])
    elif obligation == 'match-seed':
        if result['exit'] == 0:
            require(result['stderr'] == '', result)
            return True
        require(fixture['knot']['requires'], (fixture['file'], result))
        # An unsupported feature has a specific phase/code. Exhaustion and
        # host/internal failures never stand in for a language judgment.
        rejection(result, 3)
    else:
        raise AssertionError(('unknown frozen obligation', fixture['file'], obligation))
    return False


def value(result, call):
    match = re.fullmatch(r'Evaluated\t([0-9]+)\t([0-9]+)\t([^\n]+)\n?', result['stdout'])
    require(match and int(match[2]) == call['tag']
            and match[3] == call['constructor'] + '{}', (call, result))
    return {'type_id': int(match[1]), 'tag': int(match[2]), 'constructor': call['constructor']}


def observation(result):
    return {key: result[key] for key in ('exit', 'stdout', 'stderr')}


def base_reference(manifest):
    """Ask the pinned seed for its Base inventory; do not parse Bend in Python."""
    seed_dir = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
    probe = BUILD / 'base-reference.ts'
    probe.write_text(
        f'import * as Bend from {json.dumps(str(seed_dir / "bend.ts"))};\n'
        'const book = Bend.book_nil();\n'
        f'await Bend.book_load(book, {json.dumps(str(seed_dir / "base.bend"))}, "", new Map());\n'
        'Bend.book_valid(book);\n'
        'console.log(JSON.stringify({declarations: Object.keys(book.tlds), '
        'constructors: Object.keys(book.ctrs), holes: book.hols}));\n')
    result = successful(['bun', probe])
    inventory = json.loads(result['stdout'])
    require(inventory['holes'] == 0 and len(inventory['declarations']) == 466
            and len(inventory['constructors']) == 38, inventory)
    require(len(set(inventory['declarations'])) == 466, 'Duplicate seed Base declarations')
    require(digest(seed_dir / 'base.bend') == manifest['seed']['sha256']['base.bend'],
            'Base changed after seed verification')
    return {'sha256': digest(seed_dir / 'base.bend'), **inventory, 'result': result}


def supplemental_reference(manifest):
    supplement = json.loads((HERE / 'regressions.json').read_text())
    require(supplement['seed'] == manifest['seed'], 'Supplemental seed identity differs')
    files = {p.relative_to(HERE).as_posix() for p in (HERE / 'regressions').glob('*.bend')}
    require(files == set(supplement['sources']) == {f['file'] for f in supplement['fixtures']},
            'Supplemental fixture set differs from freeze')
    require(all(digest(HERE / name) == identity for name, identity in supplement['sources'].items()),
            'Supplemental fixture changed after seed freeze')
    records = []
    for fixture in supplement['fixtures']:
        for call in fixture['calls']:
            result = run([*SEED, HERE / call['run']])
            require(observation(result) == observation(call), (call, result))
            records.append({'file': fixture['file'], 'run': call['run'], 'result': result})
    return supplement['fixtures'], records


def probe_reference(manifest):
    supplement = json.loads((HERE / 'probes.json').read_text())
    require(supplement['seed'] == manifest['seed'], 'Probe seed identity differs')
    files = {p.relative_to(HERE).as_posix() for p in (HERE / 'probes').rglob('*.bend')}
    require(files == set(supplement['sources']), 'Probe source set differs from freeze')
    require(all(digest(HERE / name) == identity for name, identity in supplement['sources'].items()),
            'Probe source changed after expectation freeze')
    records = []
    for fixture in supplement['fixtures']:
        for call in fixture['calls']:
            result = run([*SEED, HERE / call['run']], bundle=HERE / fixture.get('bundle', 'bundle/lib'))
            normalized = {**result, **{key: result[key].replace(str(ROOT), '<ROOT>')
                                      for key in ('stdout', 'stderr')}}
            require(observation(normalized) == observation(call), (call, result))
            records.append({'name': fixture['name'], 'run': call['run'], 'result': result})
    return supplement['fixtures'], records


def review_reference(manifest, round):
    supplement = json.loads((HERE / f'{round}.json').read_text())
    require(supplement['seed'] == manifest['seed'], 'Review seed identity differs')
    source = HERE / round
    files = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    require(files == set(supplement['sources']), 'Review source set differs from freeze')
    require(all(digest(source / name) == identity for name, identity in supplement['sources'].items()),
            'Review fixture changed after expectation freeze')
    target = BUILD / round
    shutil.copytree(source, target, dirs_exist_ok=True)
    for name, relative in supplement.get('symlinks', {}).items():
        link = target / name
        if link.is_symlink():
            link.unlink()
        require(not link.exists(), ('Review link path is occupied', name))
        link.symlink_to(relative, target_is_directory=True)
    case = supplement.get('case_alias')
    require(case is None or ((target / case['alias']).exists()
            and os.path.samefile(target / case['canonical'], target / case['alias'])),
            'Review case-alias probe requires a case-insensitive filesystem')
    records, fixtures = [], []
    for frozen in supplement['fixtures']:
        fixture = json.loads(json.dumps(frozen))
        fixture['file'] = os.path.relpath(target / frozen['file'], HERE)
        if 'loaded_files' in fixture:
            fixture['loaded_files'] = [os.path.relpath(target / name, HERE)
                                       for name in fixture['loaded_files']]
        for call in fixture['calls']:
            entry = target / call['run']
            result = run([*SEED, entry])
            normalized = {**result, **{key: result[key].replace(str(ROOT), '<ROOT>')
                                      for key in ('stdout', 'stderr')}}
            require(observation(normalized) == observation(call), (call, result))
            records.append({'name': fixture['name'], 'run': call['run'], 'result': result})
            call['run'] = os.path.relpath(entry, HERE)
        fixtures.append(fixture)
    return fixtures, records


def adapter_drift(root, pins, host):
    """Files of the foreign path query whose bytes differ from the pins, are missing or unpinned."""
    drift = {path for path, identity in pins.items()
             if not (root / path).is_file() or digest(root / path) != identity}
    present = {p.relative_to(root).as_posix() for p in (root / host).rglob('*') if p.is_file()}
    return sorted(drift | (present - set(pins)))


def adapter_pins():
    """The seed-built CLIs run these bytes; census pins only the Bend wrapper."""
    frozen = json.loads((HERE / 'review-round3.json').read_text())['adapter_pins']
    pins, host = frozen['pins'], frozen['host_directory']
    require(pins == json.loads((HERE / 'host-check-expectations.json').read_text())['host_query_sha256'],
            'Adapter pins differ from the host-check expectations')
    reference = json.loads((ROOT / 'tests/compiler-io-abi-2/expectations.json').read_text())['reference_sha256']
    for path, copy in frozen['references'].items():
        require(pins[path] == reference[Path(copy['file']).name] == digest(ROOT / copy['file']),
                ('Loader adapter differs from the knot-io-2 reference body', path))
    drift = adapter_drift(ROOT, pins, host)
    require(drift == [], ('Host adapter bytes differ from their pins', drift))
    controls = []
    for control in frozen['controls']:
        scratch = BUILD / 'adapter-controls' / control['name']
        if scratch.exists():
            shutil.rmtree(scratch)
        for path in pins:
            (scratch / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, scratch / path)
        if 'change' in control:
            target = scratch / control['change']['file']
            data = bytearray(target.read_bytes())
            data[control['change']['offset']] ^= control['change']['xor']
            target.write_bytes(bytes(data))
        if 'remove' in control:
            (scratch / control['remove']).unlink()
        if 'add' in control:
            (scratch / control['add']).write_text('// unpinned host file\n')
        observed = adapter_drift(scratch, pins, host)
        require(observed == control['drift'], (control, observed))
        controls.append({'name': control['name'], 'drift': observed})
    return {'pins': pins, 'controls': controls}


def pin_controls(record):
    expected = json.loads((HERE / 'pin-expectations.json').read_text())
    paths = []
    for index, vector in enumerate(expected['vectors']):
        path = BUILD / f'pin-vector-{index}.txt'
        path.write_bytes(vector['text'].encode('ascii'))
        require(digest(path) == vector['sha256'], ('hashlib differs from frozen vector', vector))
        paths.append((f'vector-{index}', path, vector['sha256']))
    source = ROOT / expected['base']['path']
    require(source.stat().st_size == expected['base']['bytes']
            and digest(source) == expected['base']['sha256'], 'Pinned Base identity changed')
    paths.append(('base', source, expected['base']['sha256']))
    corrupted = BUILD / 'base-corrupted.bend'
    corrupted.write_bytes(source.read_bytes() + b'\n')
    unicode = BUILD / 'pin-non-ascii.txt'
    unicode.write_text('\u00e9')
    record['pin_builds'], record['pin'] = [], []
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        output = BUILD / ('pin' + suffix)
        built = successful([*SEED, HERE / 'pin.bend', '-o', output])
        record['pin_builds'].append({'lane': lane, 'result': built, 'sha256': digest(output)})
        for name, path, identity in paths:
            result = successful([*runtime, output, path])
            require(result['stdout'] == identity + '\n' and result['stderr'] == '', result)
            record['pin'].append({'lane': lane, 'kind': 'digest', 'name': name,
                                  'expected_sha256': identity, 'result': result})
        result = successful([*runtime, output, '--verify', source])
        require(result['stdout'] == 'Verified\n' and result['stderr'] == '', result)
        record['pin'].append({'lane': lane, 'kind': 'verify', 'result': result})
        for name, args in [('mismatch', ['--verify', corrupted]), ('non-ascii', [unicode])]:
            result = run([*runtime, output, *args])
            rejection(result, 5, 'HostFailure\tload\tbase-pin')
            record['pin'].append({'lane': lane, 'kind': name, 'result': result})


def build_lanes(record):
    lanes = {}
    record['builds'] = []
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        lanes[lane] = {}
        for phase in ('check', 'eval', 'compile'):
            output = BUILD / (phase + suffix)
            output.unlink(missing_ok=True)
            built = successful([*SEED, ROOT / f'src/{phase}-cli.bend', '-o', output])
            record['builds'].append({'lane': lane, 'phase': phase, 'result': built,
                                     'sha256': digest(output)})
            lanes[lane][phase] = [*runtime, output, '--bundle', BUNDLE]
            lanes[lane]['plain-' + phase] = [*runtime, output]
            if phase == 'check':
                lanes[lane]['audit'] = [*runtime, output, '--audit-bundle', BUNDLE]
    return lanes


def tampered_base(lanes, expected):
    # Exercise the real loader against a private corrupted Base. The pinned
    # seed, frozen bundle and compiler sources remain untouched.
    cwd = BUILD / 'tampered-base-root'
    target = cwd / expected['base']['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / expected['base']['path']).read_bytes() + b'\n')
    source = HERE / 'fixtures/base-bool.bend'
    records = []
    for lane, commands in lanes.items():
        for phase in ('check', 'eval', 'compile'):
            output = BUILD / f'tampered-{lane}.wasm'
            marker = b'existing artifact survives Base pin failure\n'
            output.write_bytes(marker)
            extra = [] if phase == 'check' else ['main', 65536] if phase == 'eval' else [output]
            result = run([*commands[phase], source, *extra], cwd=cwd)
            rejection(result, 5, 'HostFailure\tload\tbase-pin')
            require(output.read_bytes() == marker, ('Base pin failure changed output', result))
            records.append({'lane': lane, 'phase': phase, 'result': result,
                            'artifact_preserved': phase == 'compile'})
    return records


def audit(result, fixture, base):
    require(result['exit'] == 0 and result['stderr'] == '', result)
    rows = {'BasePin': [], 'Module': [], 'BaseChecked': [], 'BaseUnchecked': []}
    for line in result['stdout'].splitlines():
        if not line:
            continue
        pair = line.split('\t')
        require(len(pair) == 2 and pair[0] in rows and pair[1], ('malformed loader audit', result))
        rows[pair[0]].append(pair[1])
    require(rows['BasePin'] == [base['sha256']], ('wrong Base identity', result))
    if 'loaded_files' in fixture:
        expected = {str((HERE / path).resolve()) for path in fixture['loaded_files']}
    else:
        expected = {str((HERE / fixture['file']).resolve())}
        for module in fixture['modules']:
            if module == 'Base':
                continue
            expected.add(str(((HERE if module.startswith('fixtures/') else BUNDLE) / module).resolve()))
    require(len(rows['Module']) == len(expected) and set(rows['Module']) == expected,
            ('module identity or load-once mismatch', expected, result))
    checked, unchecked = rows['BaseChecked'], rows['BaseUnchecked']
    if 'Base' in fixture['modules']:
        require(len(checked) + len(unchecked) == len(base['declarations'])
                and set(checked).isdisjoint(unchecked)
                and set(checked + unchecked) == set(base['declarations']),
                ('incomplete Base trust partition', result))
        require(checked == [name for name in base['declarations'] if name in checked]
                and unchecked == [name for name in base['declarations'] if name in unchecked],
                ('Base inventory order differs from pinned source', result))
        wanted = fixture.get('checked_base', BASE_SLICES.get(Path(fixture['file']).stem))
        if wanted is not None:
            require(set(checked) == set(wanted), ('wrong checked Base slice', wanted, result))
    else:
        require(not checked and not unchecked, ('Base loaded without an import', result))
    return {'result': result, 'modules': rows['Module'],
            'checked_base': checked, 'unchecked_base': unchecked}


def single_file(fixture, commands, source, name, lane):
    """The same source through the single-file CLIs, which have no qualification pass."""
    judged = {'file': fixture['file'], 'knot': {'obligation': 'match-seed',
                                                'requires': fixture['knot'].get('requires', [])}}
    if 'exit' in fixture['plain']:
        judged = {'file': fixture['file'], 'knot': {'obligation': 'knot_expected'},
                  'knot_expected': fixture['plain']}
    output = BUILD / f'{name}-{lane}-plain.wasm'
    output.unlink(missing_ok=True)
    results = {'check': run([*commands['check'], source])}
    for index, call in enumerate(fixture['calls']):
        args = [arg['tag'] for arg in call['arguments']]
        results[f'eval-{index}'] = run([*commands['eval'], source, call['export'], 65536, *args])
        if observe(results[f'eval-{index}'], judged):
            value(results[f'eval-{index}'], call)
    results['compile'] = run([*commands['compile'], source, output])
    if observe(results['check'], judged):
        require(results['check']['stdout'].startswith('Checked\n'), results['check'])
    if observe(results['compile'], judged):
        for call in fixture['calls']:
            answer = json.loads(successful(['node', HOST, output, call['export']])['stdout'])
            require(answer['validated'] and answer['result'] == call['tag'], (call, answer))
    return results


def fixture_observations(fixture, lanes, base):
    name = fixture.get('name', Path(fixture['file']).stem)
    source = HERE / fixture['file']
    if fixture.get('entry_mode') == 'relative':
        source = source.relative_to(ROOT)
    bundle = HERE / fixture.get('bundle', 'bundle/lib')
    if fixture.get('bundle_mode') == 'relative':
        bundle = bundle.relative_to(ROOT)
    item = {'name': name, 'file': fixture['file'], 'knot': fixture['knot'],
            'reference': fixture['calls'], 'lanes': {}}
    outputs = {}
    for lane, commands in lanes.items():
        plain = {phase: commands['plain-' + phase] for phase in ('check', 'eval', 'compile')}
        commands = {phase: [*argv[:-1], bundle] for phase, argv in commands.items() if '-' not in phase}
        checked = run([*commands['check'], source])
        if observe(checked, fixture):
            require(checked['stdout'].startswith('Checked\n'), checked)
        evaluated = []
        for call in fixture['calls']:
            args = [arg['tag'] for arg in call['arguments']]
            result = run([*commands['eval'], source, call['export'], 65536, *args])
            entry = {'export': call['export'], 'arguments': call['arguments'], 'result': result}
            if observe(result, fixture):
                entry['value'] = value(result, call)
            evaluated.append(entry)
        output = BUILD / f'{name}-{lane}.wasm'
        marker = b'existing output must survive rejected module compilation\n'
        output.write_bytes(marker)
        compiled = run([*commands['compile'], source, output])
        accepted = observe(compiled, fixture)
        evidence = {'check': checked, 'evaluations': evaluated, 'compile': compiled,
                    'wasm': [], 'artifact_preserved': not accepted}
        if checked['exit'] == 0:
            evidence['audit'] = audit(run([*commands['audit'], source]), fixture, base)
        if accepted:
            binary = output.read_bytes()
            require(binary.startswith(b'\0asm\x01\0\0\0'), compiled)
            require(compiled['stdout'].strip() == f'Built\t{len(binary)}', compiled)
            evidence['sha256'] = digest(output)
            outputs[lane] = binary
            for call in fixture['calls']:
                args = [arg['tag'] for arg in call['arguments']]
                result = successful(['node', HOST, output, call['export'], *args])
                answer = json.loads(result['stdout'])
                require(answer == {'validated': True, 'export': call['export'],
                                   'arguments': args, 'result': call['tag'],
                                   'bytes': len(binary)}, (call, result))
                evidence['wasm'].append({'export': call['export'], 'arguments': args,
                                         'expected_tag': call['tag'], 'result': result})
        else:
            require(output.read_bytes() == marker, ('rejection changed output', compiled))
        if 'plain' in fixture:
            evidence['plain'] = single_file(fixture, plain, source, name, lane)
        item['lanes'][lane] = evidence
    native, bun = item['lanes']['native'], item['lanes']['bun']
    for phase in ('check', 'compile'):
        require(observation(native[phase]) == observation(bun[phase]),
                (fixture['file'], phase, 'native/Bun observations differ', native[phase], bun[phase]))
    require([observation(row['result']) for row in native['evaluations']] ==
            [observation(row['result']) for row in bun['evaluations']],
            (fixture['file'], 'native/Bun evaluation differs'))
    if 'plain' in fixture:
        require([observation(r) for r in native['plain'].values()] ==
                [observation(r) for r in bun['plain'].values()],
                (fixture['file'], 'native/Bun single-file observations differ'))
    if 'audit' in native:
        require('audit' in bun and
                observation(native['audit']['result']) == observation(bun['audit']['result']),
                (fixture['file'], 'native/Bun trust inventories differ'))
    if outputs:
        require(set(outputs) == {'native', 'bun'} and outputs['native'] == outputs['bun'],
                (fixture['file'], 'native/Bun Wasm bytes differ'))
        item['byte_identical'] = True
    return item


# Each unique substitution is independently typechecked before its witness is
# run. The intended wrong result must be a completed language observation.
MUTANTS = [
    {'name': 'diamond-loaded-twice', 'file': 'load.bend',
     'old': '''def known(path: String, state: State) -> Bool:
  match state:
    case State{done,active,reversed,globals,base,has_base}: I.member(path,done)''',
     'new': '''def known(path: String, state: State) -> Bool:
  False{}''',
     'witness': 'diamond', 'actual': {'exit': 2}},
    {'name': 'relative-to-entry', 'file': 'imports.bend',
     'old': '''def resolve(+importer: String, +namespace: String, +bundle: String, +path: String) -> Result<S.Error,Target>:
  +target = S.choose(String,hashed(path),u => join(bundle,path),u => join(directory(importer),path))''',
     'new': '''def entry_directory(parts: List<&2,String>, path: String) -> String:
  match parts:
    case Nil{}: path
    case Con{head,tail}: entry_directory(tail,directory(path))

def entry_root(+importer: String, +namespace: String) -> String:
  S.choose(String,String.eq(directory(namespace),""),u => directory(importer),u =>
    entry_directory(String.split(directory(namespace),'/'),directory(importer)))

def resolve(+importer: String, +namespace: String, +bundle: String, +path: String) -> Result<S.Error,Target>:
  +target = S.choose(String,hashed(path),u => join(bundle,path),u => join(entry_root(importer,namespace),path))''',
     'witness': 'nested-paths',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tload\tmissing-module\t'}},
    {'name': 'absent-hash-accepted', 'file': 'load.bend',
     'old': 'Fail{S.Invalid{"load","missing-module",S.At{0,0,0,0}}}',
     'new': 'Done{""}',
     'witness': 'hash-absent-package', 'actual': {'exit': 0}},
    {'name': 'cycle-ignored', 'file': 'load.bend',
     'old': 'Stopped{S.Invalid{"load","cycle",S.At{0,0,0,0}}}',
     'new': 'Advance{tail,state}',
     'witness': 'import-cycle', 'actual': {'exit': 0}},
    {'name': 'alias-reexported', 'file': 'qualify.bend',
     'old': '''def fallback(+qualified: String, +bare: String, +names: Names) -> String:
  Bool.pick(String,Bool.or(known(qualified,names),Bool.not(known(bare,names))),qualified,bare)''',
     'new': '''def last_member(text: String, +current: String) -> String:
  match text:
    case SNil{}: current
    case SCon{+c,+tail}:
      S.choose(String,U32.is_eq(Char.to_u32(c),46),u => last_member(tail,""),u => last_member(tail,String.append(current,SCon{c,SNil{}})))

def leaked(globals: List<&2,String>, +member: String, +otherwise: String) -> String:
  match globals:
    case Nil{}: otherwise
    case Con{+head,+tail}:
      S.choose(String,String.eq(last_member(head,""),member),u => head,u => leaked(tail,member,otherwise))

def fallback(+qualified: String, +bare: String, +names: Names) -> String:
  match names:
    case Names{ns,aliases,+globals,own}:
      S.choose(String,known(qualified,names),u => qualified,u => leaked(globals,last_member(bare,""),qualified))''',
     'witness': 'alias-not-reexported', 'actual': {'exit': 0}},
    {'name': 'path-identity-ignored', 'file': 'path-host.bend',
     'old': 'S.choose(Result<S.Error,Unit>,canonical,u => Done{Unit{}},u =>',
     'new': 'S.choose(Result<S.Error,Unit>,True{},u => Done{Unit{}},u =>',
     'witness': 'symlink-directory',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tcheck\ttype-mismatch\t'}},
    {'name': 'qualified-freshness-ignored', 'file': 'qualify.bend',
     'old': 'Bool.or(contains(globals,S.text(token)),contains(globals,prefix(ns,S.text(token))))',
     'new': 'contains(globals,S.text(token))',
     'witness': 'base-first-collision', 'actual': {'exit': 0}},
    {'name': 'base-collision-ignored', 'file': 'load.bend',
     'old': 'S.choose(Result<S.Error,State>,collides(globals,names),u =>',
     'new': 'S.choose(Result<S.Error,State>,False{},u =>',
     'witness': 'base-last-collision', 'actual': {'exit': 0}},
    {'name': 'pattern-constructor-ignored', 'file': 'qualify.bend',
     'old': 'Bool.and(known(S.text(resolved),names),contains(ctors,S.text(resolved)))',
     'new': 'False{}',
     'witness': 'local-ctor-binder', 'actual': {'exit': 0}},
    {'name': 'foreign-body-uses-column', 'file': 'imports.bend',
     'old': 'foreign(parts),u =>\n          Fail{S.Unsupported',
     'new': 'Bool.not(String.starts_with(line,"import")),u =>\n          Fail{S.Unsupported',
     'witness': 'foreign-column-zero',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tload\timport-after-declaration\t'}},
    {'name': 'host-symlink-ignored', 'file': 'host/path-identity.js',
     'old': 'if (stat.isSymbolicLink()) return io_done(false);',
     'new': 'if (false) return io_done(false);',
     'witness': 'symlink-directory',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tcheck\ttype-mismatch\t'}},
    {'name': 'host-case-ignored', 'file': 'host/path-identity.js',
     'old': 'if (!exact) return io_done(false);',
     'new': 'if (false) return io_done(false);',
     'witness': 'case-alias',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tcheck\ttype-mismatch\t'}},
    {'name': 'pattern-global-ctors-dropped', 'file': 'qualify.bend',
     'old': 'Nil{},\n          ctors),result))',
     'new': 'Nil{},\n          Nil{}),result))',
     'witness': 'base-ctor-binder', 'actual': {'exit': 0}},
    {'name': 'promoted-constructor-ignored', 'file': 'qualify.bend',
     'old': 'pattern(token,S.Promotion{token},names,ctors)',
     'new': 'Done{Qualified{S.Promotion{token},[S.text(token)]}}',
     'witness': 'local-promoted-ctor-binder', 'actual': {'exit': 0}},
    {'name': 'source-budget-counts-characters', 'file': 'load.bend',
     'old': '+cost = width(Char.to_u32(c))',
     'new': '+cost : Nat = 1n',
     'witness': 'multibyte-entry-tail',
     'actual': {'exit': 3, 'diagnostic_prefix': 'Unsupported\tload\theader-character\t'}},
    {'name': 'import-comment-splits-anywhere', 'file': 'imports.bend',
     'old': '+parts = words(line,"",Nil{})',
     'new': "+parts = words(first(split(line,'#')),\"\",Nil{})",
     'witness': 'hash-glued-base', 'actual': {'exit': 0}},
    {'name': 'alias-keeps-glued-comment', 'file': 'imports.bend',
     'old': "aliased(path,as,first(split(alias,'#')),at)",
     'new': 'aliased(path,as,alias,at)',
     'witness': 'hash-alias-comment',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tload\timport-alias\t'}},
    {'name': 'header-character-ignored', 'file': 'imports.bend',
     'old': 'Bool.and(open,Bool.not(printable(line)))',
     'new': 'False{}',
     'witness': 'header-bom',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tload\timport-after-declaration\t'}},
    {'name': 'constructor-order-ignored', 'file': 'qualify.bend',
     'old': 'Nil{},\n          ctors),result))',
     'new': 'Nil{},\n          List.append(&2,String,ctors,prefixed(namespace,ctors_in(items)))),result))',
     'witness': 'later-ctor-binder',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tcheck\tconstructor-pattern-binder\t'}},
    {'name': 'let-binder-unchecked', 'file': 'qualify.bend',
     'old': 'then(pattern(token,S.Variable{token},names,ctors),binder => binders =>',
     'new': 'then(done(S.Variable{token}),binder => binders =>',
     'witness': 'let-base-ctor', 'actual': {'exit': 0}},
    {'name': 'file-let-binder-unchecked', 'file': 'check.bend',
     'old': 'named(ctors,S.text(token))',
     'new': 'False{}',
     'witness': 'let-single-ctor', 'plain': True, 'actual': {'exit': 0}},
    {'name': 'file-constructor-order-ignored', 'file': 'check.bend',
     'old': 'def file(depth: Nat, +root: S.Node) -> Result<S.Error,C.Book>:\n  S.bind(Unit,C.Book,rebinds(65536n,[root],Nil{}),u => check(depth,root))',
     'new': 'def declared(nodes: List<&2,S.Node>) -> List<&2,String>:\n  match nodes:\n    case Nil{}: Nil{}\n    case Con{S.Datatype{token,data,children},tail}: List.append(&2,String,constructor_names(children),declared(tail))\n    case Con{S.Sequence{items},tail}: List.append(&2,String,declared(items),declared(tail))\n    case Con{other,tail}: declared(tail)\n\ndef file(depth: Nat, +root: S.Node) -> Result<S.Error,C.Book>:\n  S.bind(Unit,C.Book,rebinds(65536n,[root],declared([root])),u => check(depth,root))',
     'witness': 'field-later-ctor', 'plain': True,
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tcheck\tconstructor-pattern-binder\t'}},
    {'name': 'file-arm-binders-unchecked', 'file': 'check.bend',
     'old': 'S.bind(Unit,Unit,fresh(binders(pat),ctors),u => rebinds(n,Con{body,rest},ctors))',
     'new': 'rebinds(n,Con{body,rest},ctors)',
     'witness': 'arm-earlier-ctor', 'plain': True,
     'actual': {'exit': 3, 'diagnostic_prefix': 'Unsupported\tcheck\tvariable-pattern\t'}},
    {'name': 'field-binder-book-wide', 'file': 'patterns.bend',
     'old': 'def fields(nodes: List<&2,S.Node>, parameters: List<&2,C.Parameter>, +parent: U32,\n  +types: List<&2,C.Datatype>, +scope: E.Scope, +origin: S.Token) -> Result<S.Error,Fields>:\n  match nodes parameters:\n    case Nil{} Nil{}: Done{Fields{scope,Nil{},Nil{}}}\n    case Con{node,+tail} Con{C.Parameter{name,+q,+type_id},+rest}:\n      binder(node,+token => mark =>\n        +actual = quantity(q,parent,mark)\n        S.bind(C.Datatype,Fields,G.type_at(types,type_id),definition =>\n          S.bind(Unit,Fields,G.quantity(token,actual,definition),u =>\n            add(scope,token,actual,type_id,bound => binding => term =>\n              S.bind(Fields,Fields,fields(tail,rest,parent,types,bound,origin),remaining => Done{prepend(binding,term,remaining)})))))\n    case _ _: C.invalid(Fields,"pattern-arity",origin)\n\n',
     'new': 'def book_constructor(types: List<&2,C.Datatype>, +name: S.Token) -> Bool:\n  match types:\n    case Nil{}: False{}\n    case Con{C.Datatype{token,data,ctors},tail}:\n      Bool.or(Maybe.is_some(&2,U32,G.constructor_tag(ctors,name,0)),book_constructor(tail,name))\n\ndef fields(nodes: List<&2,S.Node>, parameters: List<&2,C.Parameter>, +parent: U32,\n  +types: List<&2,C.Datatype>, +scope: E.Scope, +origin: S.Token) -> Result<S.Error,Fields>:\n  match nodes parameters:\n    case Nil{} Nil{}: Done{Fields{scope,Nil{},Nil{}}}\n    case Con{node,+tail} Con{C.Parameter{name,+q,+type_id},+rest}:\n      binder(node,+token => mark =>\n        S.choose(Result<S.Error,Fields>,book_constructor(types,token),u => C.invalid(Fields,"constructor-pattern-binder",token),u =>\n        +actual = quantity(q,parent,mark)\n        S.bind(C.Datatype,Fields,G.type_at(types,type_id),definition =>\n          S.bind(Unit,Fields,G.quantity(token,actual,definition),u =>\n            add(scope,token,actual,type_id,bound => binding => term =>\n              S.bind(Fields,Fields,fields(tail,rest,parent,types,bound,origin),remaining => Done{prepend(binding,term,remaining)}))))))\n    case _ _: C.invalid(Fields,"pattern-arity",origin)\n\n',
     'witness': 'field-cross-module-ctor',
     'actual': {'exit': 2, 'diagnostic_prefix': 'Invalid\tcheck\tconstructor-pattern-binder\t'}},
]
REQUIRED_MUTANTS = {'diamond-loaded-twice', 'alias-reexported',
                    'relative-to-entry', 'absent-hash-accepted', 'cycle-ignored',
                    'path-identity-ignored', 'qualified-freshness-ignored', 'base-collision-ignored',
                    'pattern-constructor-ignored', 'foreign-body-uses-column',
                    'host-symlink-ignored', 'host-case-ignored',
                    'pattern-global-ctors-dropped', 'promoted-constructor-ignored',
                    'source-budget-counts-characters', 'import-comment-splits-anywhere',
                    'alias-keeps-glued-comment', 'header-character-ignored',
                    'constructor-order-ignored', 'let-binder-unchecked', 'file-let-binder-unchecked',
                    'file-constructor-order-ignored', 'file-arm-binders-unchecked', 'field-binder-book-wide'}


def mutants(fixtures):
    require({m['name'] for m in MUTANTS} >= REQUIRED_MUTANTS, 'Missing module semantic mutants')
    by_name = {fixture.get('name', Path(fixture['file']).stem): fixture for fixture in fixtures}
    records = []
    for mutant in MUTANTS:
        name = mutant['name']
        directory = BUILD / name
        directory.mkdir(exist_ok=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        shutil.copytree(ROOT / 'src/host', directory / 'host', dirs_exist_ok=True)
        target = directory / mutant['file']
        source = target.read_text()
        require(source.count(mutant['old']) == 1, (name, 'mutation must be unique'))
        target.write_text(source.replace(mutant['old'], mutant['new']))
        if target.suffix == '.js':
            successful(['node', '--check', target])
        entry = directory / 'check-cli.bend'
        typecheck = successful([*SEED, entry, '--check-only'])
        require(observation(typecheck) == json.loads((HERE / 'host-check-expectations.json').read_text())['observation'], typecheck)
        output = directory / 'mutant.js'
        built = successful([*SEED, entry, '-o', output])
        fixture = by_name[mutant['witness']]
        mode = [] if mutant.get('plain') else ['--bundle', BUNDLE]
        result = run(['bun', output, *mode, HERE / fixture['file']])
        if mutant.get('plain'):
            fixture = {'file': fixture['file'], 'knot': {'obligation': 'knot_expected'},
                       'knot_expected': fixture['plain']}
        expected = mutant['actual']
        require(result['exit'] == expected['exit'], (mutant, result))
        if expected['exit'] == 0:
            require(result['stdout'].startswith('Checked\n') and result['stderr'] == '', result)
        else:
            rejection(result, expected['exit'], expected.get('diagnostic_prefix'))
        try:
            observe(result, fixture)
        except AssertionError:
            pass
        else:
            raise AssertionError((name, 'mutant survived its frozen witness', result))
        records.append({**mutant, 'sha256': digest(target), 'typecheck': typecheck,
                        'build': built, 'result': result, 'outcome': 'semantic-kill'})
    return records


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'expectations.json').read_text())
    paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
             ROOT / 'src/CONTRACT.json', HOST, Path(__file__), HERE / 'expectations.json',
             HERE / 'FIXTURES.md', HERE / 'regen.py', HERE / 'regressions.json',
             HERE / 'host-check-expectations.json',
             HERE / 'probes.json', HERE / 'pin.bend', HERE / 'pin-expectations.json',
             HERE / 'review-round2.json', HERE / 'review-round3.json', *sorted((ROOT / 'src/host').glob('*')),
             ROOT / 'tests/compiler-io-abi-2/expectations.json',
             *sorted((ROOT / 'tests/compiler-io-abi-2/reference').glob('*'))]
    paths += [p for folder in ('fixtures', 'calls', 'bundle', 'regressions', 'probes', 'review-round2', 'review-round3')
              for p in sorted((HERE / folder).rglob('*')) if p.is_file()]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'seed': manifest['seed'],
              'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}}
    try:
        record['reference_verification'] = successful(['python3', HERE / 'regen.py'])
        supplemental, record['supplemental_reference'] = supplemental_reference(manifest)
        probes, record['probe_reference'] = probe_reference(manifest)
        review, record['review_reference'] = review_reference(manifest, 'review-round2')
        round3, record['round3_reference'] = review_reference(manifest, 'review-round3')
        review += round3
        record['adapters'] = adapter_pins()
        record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
                           for tool in ('bun', 'node', 'python3')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        record['base_reference'] = base_reference(manifest)
        record['proofs'] = []
        for entry in PROOFS:
            result = successful([*SEED, ROOT / entry])
            require(result['stdout'].strip() == 'All terms check.', result)
            record['proofs'].append({'entry': entry, 'result': result})
        lanes = build_lanes(record)
        pin_controls(record)
        record['tampered_base'] = tampered_base(lanes, json.loads((HERE / 'pin-expectations.json').read_text()))
        record['fixtures'] = []
        for fixture in [*manifest['fixtures'], *supplemental, *probes, *review]:
            record['fixtures'].append(fixture_observations(fixture, lanes, record['base_reference']))
        record['mutants'] = mutants([*manifest['fixtures'], *review])
        require(all(digest(ROOT / path) == identity for path, identity in record['inputs'].items()),
                'Inputs changed during modules gate')
        seed_dir = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
        require(all(digest(seed_dir / name) == identity
                    for name, identity in manifest['seed']['sha256'].items()),
                'Pinned seed changed during modules gate')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    fixtures = record['fixtures']
    lane_records = [lane for fixture in fixtures for lane in fixture['lanes'].values()]
    calls = sum(len(fixture['reference']) for fixture in fixtures)
    evaluations = sum(len(lane['evaluations']) for lane in lane_records)
    wasm = sum(len(lane['wasm']) for lane in lane_records)
    preserved = sum(lane['artifact_preserved'] for lane in lane_records)
    pairs = sum(fixture.get('byte_identical', False) for fixture in fixtures)
    audits = sum('audit' in lane for lane in lane_records)
    print(f'Modules gate passed: {len(fixtures)} fixtures, {calls} seed calls, '
          f'{len(lane_records)} checks, {evaluations} evaluations, {len(lane_records)} compilations, '
          f'{wasm} Wasm observations, {pairs} byte-identity pairs, '
          f'{preserved} preserved outputs, {audits} trust audits, '
          f'{len(record["pin"])} pin observations, {len(record["tampered_base"])} tampered-Base observations, '
          f'{len(record["mutants"])} semantic mutants')


if __name__ == '__main__':
    main()
