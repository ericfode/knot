#!/usr/bin/env python3
"""Run frozen oracle, seed-built Bend models, proofs and semantic mutants offline."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

from reference import run as reference
from traces import cases, fixtures

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = ROOT / '.local/data-lifetime'
RECEIPTS = HERE / 'receipts'
SEED = ['bun', '--no-env-file', str(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts')]
ENV = dict(os.environ, BEND_NO_TELEMETRY='1', PYTHONDONTWRITEBYTECODE='1')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def run(argv, timeout=120):
    try:
        p = subprocess.run(list(map(str, argv)), cwd=ROOT, env=ENV,
                           text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('Exhausted host-timeout: ' + str(argv)) from error
    except OSError as error:
        raise RuntimeError('HostFailure launch: ' + str(argv)) from error
    return dict(argv=[str(x).replace(str(ROOT) + '/', '') for x in argv],
                exit=p.returncode, stdout=p.stdout, stderr=p.stderr)


def success(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def command(op):
    name, *args = op
    sequence = lambda xs: '[' + ','.join(map(str, xs)) + ']'
    if name == 'alloc':
        dst, kind, tag, *slots = args
        return f'M.Alloc{{{dst},{kind},{tag},{sequence(slots)}}}'
    if name == 'take':
        return f'M.Take{{{args[0]},{sequence(args[1:])}}}'
    if name == 'clean':
        return f'M.Clean{{{args[0]}n}}'
    tag = dict(share='Share', move='Transfer', release='Release', pin='Pin', ack='Ack', cycle='Cycle')[name]
    return f'M.{tag}' + '{' + ','.join(map(str, args)) + '}'


def entry(folder, corpus):
    folder.mkdir(parents=True, exist_ok=True)
    for path in HERE.glob('*.bend'):
        shutil.copy2(path, folder / path.name)
    lines = ['import Base', 'import ./model.bend as M', 'import ./observe.bend as O']
    for i, case in enumerate(corpus):
        for policy in 'AB':
            lines += [f'\ndef case_{i}_{policy}() -> IO(Unit):', '  do IO<Unit>:',
                      f'    IO.print("CASE {case["name"]} {policy}")',
                      '    O.run([' + ','.join(map(command, case['ops'])) + '],',
                      f'      M.Store{{M.initial({int(policy == "B")},{case.get("capacity",100000)},{case.get("ceiling",100000)})}})']
    lines += ['\ndef main() -> IO(Unit):', '  do IO<Unit>:']
    lines += [f'    case_{i}_{p}()' for i in range(len(corpus)) for p in 'AB']
    path = folder / 'entry.bend'
    path.write_text('\n'.join(lines) + '\n')
    return path


def observations(stdout):
    result, key = {}, None
    for line in stdout.splitlines():
        if line.startswith('CASE '):
            _, name, policy = line.split()
            key = (name, policy)
            require(key not in result, ('duplicate case', key))
            result[key] = []
        else:
            require(key is not None and len(line.split('|')) == 8, ('bad observation', line))
            result[key].append(line)
    return result


def compare(actual, expected):
    require(actual.keys() == expected.keys(), 'missing/extra trace')
    differences = []
    for key, want in expected.items():
        got = actual[key]
        require(len(got) == len(want), ('incomplete trace', key, len(got), len(want)))
        for step, (a, b) in enumerate(zip(got, want)):
            if a != b:
                differences.append(dict(case=key[0], policy=key[1], step=step, expected=b, actual=a))
                break
    return differences


def values(wire):
    """Forget allocation identities and policy counts; retain ordered values/holders."""
    fields = wire.split('|')
    cells = {}
    for text in fields[3].split(';') if fields[3] else []:
        ref, kind, tag, count, children = text.split(':')
        cells[int(ref)] = (int(kind), int(tag), [int(c) for c in children.split(',') if c])

    def tree(ref):
        kind, tag, children = cells[ref]
        return [kind, tag, [tree(c) for c in children]]

    def holders(text):
        return sorted((int(s), tree(int(r))) for s, r in
                      (h.split(':') for h in text.split(',') if h))

    return holders(fields[2]), holders(fields[5])


def cross_policy(corpus, expected):
    compared, exhausted = 0, []
    for case in corpus:
        comparable = True
        for step, (a, b) in enumerate(zip(expected[(case['name'], 'A')], expected[(case['name'], 'B')])):
            sa, sb = int(a.split('|')[0]), int(b.split('|')[0])
            if sa != sb and case['ops'][step][0] != 'clean':
                require(3 in (sa, sb), ('non-resource policy disagreement', case['name'], step))
                comparable = False
                exhausted.append(dict(case=case['name'], step=step, A=sa, B=sb))
            if comparable:
                require(values(a) == values(b), ('policy value disagreement', case['name'], step))
                compared += 1
        if case.get('family') or case['name'] in ('suspend-join-resume', 'cancel-roots'):
            for policy in 'AB':
                final = expected[(case['name'], policy)][-1].split('|')
                require(all(final[i] == '' for i in (2, 3, 4, 5)), ('cleanup did not finish', case['name'], policy))
    return dict(value_and_holder_pairs=compared, resource_divergences=exhausted)


# Function bounds make each mutation anchor unique and reviewable.
MUTANTS = [
    ('copy-aliases-original', 'shared', 'copy(heap,id)', 'Done{Allocation{heap,id}}', 'copied Data identity'),
    ('copy-reverses-fields', 'assemble', 'allocate(heap,kind,tag,[a,b])', 'allocate(heap,kind,tag,[b,a])', 'field order'),
    ('retain-forgets-count', 'retained', 'U32.add(refs,1)', 'refs', 'balanced acquire'),
    ('count-wrap-permitted', 'retained', 'U32.is_lt(refs,ceiling)', 'True{}', 'count ceiling'),
    ('first-release-frees', 'release_cell', 'U32.is_eq(refs,1)', 'True{}', 'surviving Data holder'),
    ('never-reclaim', 'release_cell', 'free(charged(charged_heap,3n,length(children)),value)', 'charged(charged_heap,3n,length(children))', 'last-release progress'),
    ('cleanup-loses-tail', 'clean_step', 'queued(heap,tail)', 'queued(heap,Nil{})', 'pending work preservation'),
    ('zero-budget-loses-work', 'clean', 'case 0n _: (heap,3)', 'case 0n _: (queued(heap,Nil{}),3)', 'exhaustion preservation'),
    ('ignore-reader-barrier', 'clean',
     'case 1n+n Heap{p,l,c,next,cs,rs,q,Con{h,t},m,d}: (heap,3)',
     'case 1n+n Heap{p,l,c,next,cs,rs,q,Con{h,t},m,d}: continue_clean(clean_step(heap),heap,next => clean(n,next))',
     'reader completion before reuse'),
    ('double-drop-type', 'dropped', 'Con{tag,d}', 'Con{tag,Con{7,d}}', 'serial 7 disposed twice'),
    ('rejection-loses-owner', 'commit', '(original,error)', '(with_roots(original,Nil{}),error)', 'failure ownership'),
    ('take-retains-parent', 'opened', 'Done{free(charged_heap,value)}', 'Done{charged_heap}', 'consume releases parent cell'),
    ('open-forgets-child-acquire', 'opened', 'acquire_all(children,charged_heap)', 'Done{charged_heap}', 'shared parent opening'),
    ('copy-type-owner', 'shared', 'U32.is_eq(k,1)', 'True{}', 'Type sharing Unsupported'),
    ('omit-suspended-root', 'move', 'Con{Holder{dst,ref},omit(src,rs)}',
     'Bool.pick(List<&2,Holder>,U32.is_eq(dst,10),omit(src,rs),Con{Holder{dst,ref},omit(src,rs)})',
     'suspended frame remains an owning holder'),
    ('omit-partial-join-root', 'move', 'Con{Holder{dst,ref},omit(src,rs)}',
     'Bool.pick(List<&2,Holder>,U32.is_eq(dst,20),omit(src,rs),Con{Holder{dst,ref},omit(src,rs)})',
     'delivered join slot remains an owning holder'),
]


def mutate(path, function, old, new):
    source = path.read_text()
    start = source.index('def ' + function + '(')
    end = source.find('\ndef ', start + 1)
    end = len(source) if end == -1 else end
    block = source[start:end]
    require(block.count(old) == 1, ('nonunique mutation anchor', function, old))
    path.write_text(source[:start] + block.replace(old, new) + source[end:])


def quantity_controls(folder):
    results = []
    for name, body, negative in [
        ('move-store', 'def use(s: M.Store) -> M.Store:\n  s\n', False),
        ('duplicate-store', 'def use(s: M.Store) -> M.Store & M.Store:\n  (s,s)\n', True),
        ('copy-snapshot', 'def use(+s: M.Heap) -> M.Heap & M.Heap:\n  (s,s)\n', False),
        ('move-token', 'type Token is Type:\n  Token{serial: U32}\ndef use(t: Token) -> Token:\n  t\n', False),
        ('duplicate-token', 'type Token is Type:\n  Token{serial: U32}\ndef use(t: Token) -> Token & Token:\n  (t,t)\n', True),
    ]:
        path = folder / (name + '.bend')
        path.write_text('import Base\nimport ./model.bend as M\n' + body)
        result = run([*SEED, path, '--check-only'])
        require(result['exit'] == 1 and 'consumed more than once' in result['stderr'] if negative
                else result['exit'] == 0 and result['stdout'].strip() == 'All terms check.', result)
        results.append(dict(name=name, expected='Invalid quantity' if negative else 'Checked', result=result))
    return results


def source_controls():
    corpus = json.loads((HERE / 'source-expectations.json').read_text())['cases']
    record = dict(scope='Source value observations only; store models are outside Knot implementation profile.', cases=[], builds=[])
    lanes = {}
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
        lanes[lane] = {}
        for phase in ('eval', 'compile'):
            path = BUILD / (phase + suffix)
            record['builds'].append(success([*SEED, ROOT / f'src/{phase}-cli.bend', '-o', path]))
            lanes[lane][phase] = [*runtime, path]
    for case in corpus:
        path = HERE / 'fixtures' / case['file']
        seed = success([*SEED, path])
        require(seed['stdout'].strip() == case['seed'], (case, seed))
        row = dict(file=case['file'], sha256=digest(path), seed=seed, lanes={})
        for lane, commands in lanes.items():
            evaluated = success([*commands['eval'], path, 'main', 4096])
            # Seed pretty-printing inserts spaces; Knot's tree protocol does not.
            want = f"Evaluated\t{case['type']}\t{case['tag']}\t{case['seed'].replace(', ', ',')}"
            require(evaluated['stdout'].strip() == want, (case, evaluated))
            output = BUILD / (case['file'] + '-' + lane + '.wasm')
            sentinel = b'no field module has been built\n'
            output.write_bytes(sentinel)
            compiled = run([*commands['compile'], path, output])
            require(compiled['exit'] == 3 and 'Unsupported\tcheck\tconstructor-fields\t' in compiled['stderr'], compiled)
            require(output.read_bytes() == sentinel, 'Unsupported emission changed existing artifact')
            row['lanes'][lane] = dict(evaluator=evaluated, wasm=compiled, artifact_preserved=True)
        record['cases'].append(row)
    record['counts'] = dict(seed_values=4, evaluator_values=8, wasm_unsupported=8)
    return record


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(exist_ok=True)
    record = dict(schema=1, status='incomplete', seed_revision='574b6d39a235b539eb19a5c532993a0abb3d11ad')
    try:
        frozen = json.loads((HERE / 'expectations.json').read_text())['sha256']
        require(all(digest(HERE / p) == h for p, h in frozen.items()), 'frozen expectation changed')
        extra = json.loads((HERE / 'extra-traces.json').read_text())['cases']
        corpus = cases() + extra
        expected = {(c['name'], p): reference(c, p) for c in corpus for p in 'AB'}
        literals = json.loads((HERE / 'literals.json').read_text())['witnesses']
        for witness in literals:
            for policy in 'AB':
                require(expected[(witness['case'], policy)][witness['step']] == witness[policy], witness)
        for case in extra:
            for policy in 'AB':
                require(expected[(case['name'], policy)][-1] == case['last'][policy], case)
        record['expectations'] = frozen
        record['literal_checks'] = 2 * (len(literals) + len(extra))
        record['cross_policy'] = cross_policy(corpus, expected)
        record['traces_per_candidate'] = len(corpus)
        record['steps_per_candidate_per_lane'] = sum(len(c['ops']) for c in corpus)
        inputs = [p for p in HERE.glob('*') if p.is_file() and p.suffix in ('.bend', '.py', '.ts', '.json')]
        inputs += list((HERE / 'fixtures').glob('*.bend'))
        record['sources'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(inputs)}
        record['tools'] = {name: success([name, '--version'])['stdout'].strip() for name in ('bun', 'node', 'python3')}
        record['seed_main_sha256'] = digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts')
        record['seed_base_sha256'] = digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/base.bend')
        record['proof'] = success([*SEED, HERE / 'PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['filled_laws'] = (HERE / 'LAWS.bend').read_text().count('\nlaw ')
        source = entry(BUILD / 'baseline', corpus)
        record['entry_sha256'] = digest(source)
        record['quantity_controls'] = quantity_controls(source.parent)
        record['lanes'] = {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            artifact = source.parent / ('program' + suffix)
            built = success([*SEED, source, '-o', artifact])
            observed = success([*runtime, artifact])
            actual = observations(observed['stdout'])
            differences = compare(actual, expected)
            require(not differences, differences[:3])
            output = RECEIPTS / (lane + '.txt.gz')
            output.write_bytes(gzip.compress(observed['stdout'].encode(), mtime=0))
            observed['stdout_sha256'] = hashlib.sha256(observed.pop('stdout').encode()).hexdigest()
            record['lanes'][lane] = dict(build=built, run=observed, artifact_sha256=digest(artifact),
                                         observations=sum(map(len, actual.values())), output=str(output.relative_to(ROOT)),
                                         output_sha256=digest(output))
        record['measurements'] = [dict(name=c['name'], family=c['family'], size=c['size'], commands=len(c['ops']),
                                     policies={p: list(map(int, expected[(c['name'], p)][-1].split('|')[6].split(','))) for p in 'AB'})
                                  for c in corpus if c.get('family') in ('tree', 'list', 'shared-subterm', 'rebuild')]
        record['mutants'] = []
        controls = fixtures()
        control_expected = {(c['name'], p): expected[(c['name'], p)] for c in controls for p in 'AB'}
        for name, function, old, new, obligation in MUTANTS:
            source = entry(BUILD / name, controls)
            target = source.parent / 'model.bend'
            mutate(target, function, old, new)
            checked = success([*SEED, source, '--check-only'])
            require(checked['stdout'].strip() == 'All terms check.', checked)
            artifact = source.parent / 'mutant.js'
            built = success([*SEED, source, '-o', artifact])
            observed = success(['bun', '--no-env-file', artifact])
            differences = compare(observations(observed['stdout']), control_expected)
            require(differences, ('surviving mutant', name))
            record['mutants'].append(dict(name=name, obligation=obligation, function=function, old=old, new=new,
                                          sha256=digest(target), typecheck=checked, build=built,
                                          outcome='semantic-kill', witness=differences[0], differing_traces=len(differences)))
        record['source_differential'] = source_controls()
        record['trust'] = success(['bun', '--no-env-file', HERE / 'trust.ts'])
        require(all(digest(ROOT / p) == h for p, h in record['sources'].items()), 'gate input changed')
        record['status'] = 'pass'
    except Exception as error:
        record['outcome'] = 'InternalFailure comparison' if isinstance(error, AssertionError) else str(error).split(':')[0]
        record['failure'] = repr(error)
        raise
    finally:
        (RECEIPTS / 'gate.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f"Data lifetime: {len(corpus)} traces x 2 candidates x 2 lanes; "
          f"{record['steps_per_candidate_per_lane'] * 4} full-state observations; "
          f"{record['literal_checks']} literal checks; {record['filled_laws']} filled laws; "
          f"{len(record['mutants'])} type-correct semantic mutants killed; "
          f"5 quantity controls; 4 seed / 8 evaluator values; 8 Wasm Unsupported controls.")


if __name__ == '__main__':
    main()
