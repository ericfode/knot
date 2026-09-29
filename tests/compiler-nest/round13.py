#!/usr/bin/env python3
"""Round-13 regressions: operators, `+name` and holes after a term, term openers at another column, and the core budget.

`round13.py` replays the 206 seed-frozen fixtures in both compiler lanes, runs the reviewer's 684-cell class grid and
64-form zoo in both lanes, and kills the mutants that restore each misclassification (Invalid where the seed accepts, a
code that names the wrong thing) and each bound that a repair added. The Bun lane's own fault on a large module
(`memory fault (machine stack overflow?)`) is classified as Exhausted (host), not as a disagreement.
"""
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import shutil

import check as gate
import review
import round13_seed as seed

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round13'
RECEIPT = HERE / 'receipts/round13.json'
ACCEPTED = {'exit': 0}
WORKERS = 4


def invalid(phase, code):
    return {'exit': 2, 'diagnostic': f'Invalid\t{phase}\t{code}\t'}


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


GAP = 'gap(S.skip_lines(Con{second,tail}))'
FORM = 'Bool.pick(String,operator(ts),"operator","term-form")'
GLUE = 'Bool.pick(String,abuts(t,h,rest),"operator","term-form")'
PROMOTED = 'Bool.and(Bool.not(pattern),promotes(rest))'
HOLE = 'Bool.and(Bool.not(Bool.or(parameters,pattern)),S.matches(h,"?"))'
OPENERS = 'Bool.or(matches(t,"("),Bool.or(matches(t,"["),Bool.or(numeral(text(t)),matches(t,"?"))))'
START = 'Bool.and(U32.is_gt(parent,0),S.body_start(h))'
LATER = 'S.choose(Result<S.Error,Parsed>,S.body_start(h),u =>'
SAME_LINE = 'S.choose(Result<S.Error,List<&2,S.Token>>,operator(ts),u =>'
HEADER = 'S.choose(Result<S.Error,Parsed>,operator(tokens),u => unsupported(tokens,"operator"),u =>'
BUDGET = ('S.choose(Result<S.Error,C.Checked>,U32.is_gt(weight(U32.to_nat(U32.add(core_budget(),2)),[term],U32.add(core_budget(),1)),0),u =>\n'
          '        Done{checked},u => C.exhausted(C.Checked,token))')
# Each mutant is one replacement in a copy of `src/`, killed in both lanes on the named witness (a round-13 fixture,
# or a frozen fixture of an earlier round). The parser mutants restore the Invalid that the seed contradicts (the
# marker gap widened, `+name` and `?` after an argument, a bracket, numeral or hole at a body's start) or name the wrong
# code (`operator` and `term-form` swapped); the budget mutants drop the bound or lose part of the count.
MUTANTS = [
    {'name': 'marker-gap-widened', 'file': 'parse.bend', 'old': GAP, 'new': 'True{}',
     'witness': 'letop-plus-dead2', 'phase': 'check', 'wrong': invalid('parse', 'detached-marker')},
    {'name': 'marker-gap-dropped', 'file': 'parse.bend', 'old': GAP, 'new': 'False{}',
     'witness': 'letop-gap-plus-typed-dead2', 'phase': 'check', 'wrong': unsupported('operator')},
    {'name': 'marker-gap-ignores-line-breaks', 'file': 'parse.bend', 'old': GAP, 'new': 'gap(Con{second,tail})',
     'witness': 'letop-gap-plus-break-dead2', 'phase': 'check', 'wrong': unsupported('operator')},
    {'name': 'operator-code-term-form', 'file': 'parse.bend', 'old': FORM, 'new': '"term-form"',
     'witness': 'argterm-spaced-dead2', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'line-operator-term-form', 'file': 'parse.bend', 'old': 'Bool.and(Bool.not(first),operator(tokens)),u => unsupported(tokens,"operator")',
     'new': 'Bool.and(Bool.not(first),operator(tokens)),u => unsupported(tokens,"term-form")',
     'witness': 'letop-star-typed-single', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'same-line-operator-statement', 'file': 'parse.bend', 'old': SAME_LINE,
     'new': 'S.choose(Result<S.Error,List<&2,S.Token>>,False{},u =>',
     'witness': 'letop-sameline-arrow-dead2', 'phase': 'check', 'wrong': unsupported('same-line-statement')},
    {'name': 'header-operator-term-form', 'file': 'parse.bend', 'old': HEADER,
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u => unsupported(tokens,"operator"),u =>',
     'witness': 'letop-header-plus-dead2', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'argument-promotion-invalid', 'file': 'parse.bend', 'old': PROMOTED, 'new': 'False{}',
     'witness': 'argterm-promo-dead2', 'phase': 'check', 'wrong': invalid('parse', 'argument-separator')},
    {'name': 'argument-glue-lost', 'file': 'parse.bend', 'old': GLUE, 'new': '"term-form"',
     'witness': 'argterm-glued-dead2', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'argument-glue-always', 'file': 'parse.bend', 'old': GLUE, 'new': '"operator"',
     'witness': 'argterm-promo-dead2', 'phase': 'check', 'wrong': unsupported('operator')},
    {'name': 'argument-hole-invalid', 'file': 'parse.bend', 'old': HOLE, 'new': 'False{}',
     'witness': 'argterm-hole-dead2', 'phase': 'check', 'wrong': invalid('parse', 'argument-separator')},
    {'name': 'argument-at-unsupported', 'file': 'parse.bend', 'old': HOLE,
     'new': 'Bool.and(Bool.not(Bool.or(parameters,pattern)),Bool.or(S.matches(h,"?"),S.matches(h,"@")))',
     'witness': 'argterm-ctl-at-dead2', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'argument-erased-marker-unsupported', 'file': 'parse.bend', 'old': PROMOTED, 'new': 'Bool.and(Bool.not(pattern),marker(rest))',
     'witness': 'argterm-ctl-minus-dead2', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'argument-pattern-promotion-unsupported', 'file': 'parse.bend', 'old': PROMOTED, 'new': 'promotes(rest)',
     'witness': 'argspace-promoted-fields', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'body-start-paren-invalid', 'file': 'syntax.bend', 'old': OPENERS,
     'new': OPENERS.replace('matches(t,"(")', 'False{}'),
     'witness': 'bodystart-body-multi-paren-live', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'body-start-bracket-invalid', 'file': 'syntax.bend', 'old': OPENERS,
     'new': OPENERS.replace('matches(t,"[")', 'False{}'),
     'witness': 'bodystart-body-multi-bracket-dead', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'body-start-numeral-invalid', 'file': 'syntax.bend', 'old': OPENERS,
     'new': OPENERS.replace('numeral(text(t))', 'False{}'),
     'witness': 'bodystart-body-multi-numeral-dead', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'body-start-hole-invalid', 'file': 'syntax.bend', 'old': OPENERS,
     'new': OPENERS.replace('matches(t,"?")', 'False{}'),
     'witness': 'bodystart-body-multi-hole-dead', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'body-start-bang-unsupported', 'file': 'syntax.bend', 'old': OPENERS,
     'new': OPENERS.replace('matches(t,"?")', 'Bool.or(matches(t,"?"),matches(t,"!"))'),
     'witness': 'bodystart-ctl-body-multi-bang', 'phase': 'check', 'wrong': unsupported('body-indentation')},
    {'name': 'arm-body-start-statement-only', 'file': 'parse.bend', 'old': START, 'new': START.replace('S.body_start(h)', 'S.statement(h)'),
     'witness': 'bodystart-body-multi-paren-live', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'later-statement-statement-only', 'file': 'parse.bend', 'old': LATER, 'new': LATER.replace('S.body_start(h)', 'S.statement(h)'),
     'witness': 'bodystart-stmt-multi-paren-live', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'budget-dropped', 'file': 'check.bend', 'old': BUDGET, 'new': 'Done{checked}',
     'witness': 'default-dd7x5', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'budget-counts-no-arms', 'file': 'check.bend', 'old': 'case C.Case{token,level,type_id,arms}: arms',
     'new': 'case C.Case{token,level,type_id,arms}: Nil{}',
     'witness': 'default-dd7x5', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'budget-counts-no-bodies', 'file': 'check.bend', 'old': 'case C.Branch{tag,fields,body}: [body]',
     'new': 'case C.Branch{tag,fields,body}: Nil{}',
     'witness': 'default-dd7x4-heavy', 'phase': 'check', 'wrong': ACCEPTED},
]


def outcome(result):
    """Accepted, or the first three fields of the diagnostic; anything else is an unclassified host failure."""
    if result['exit'] == 0:
        gate.checked(result)
        return 'Accepted'
    gate.require(result['exit'] in (2, 3, 4) and not result['stdout'], ('unclassified', result))
    fields = result['stderr'].split('\n')[0].split('\t')
    return '\t'.join(fields[:3])


def sweep(record, name, cells, frozen, lanes, expected):
    """Every cell in both lanes: the lanes agree, a seed-accepted cell is never Invalid, a rejected one never Accepted,
    and `expected(cell)` (a reviewed outcome, or None) is met exactly."""
    directory = BUILD / name
    directory.mkdir(parents=True, exist_ok=True)

    def one(pair):
        cell, frozen_cell = pair
        source = cell['source']
        gate.require(hashlib.sha256(source.encode()).hexdigest() == frozen_cell['sha256'], (name, 'cell changed', cell))
        path = directory / f"{frozen_cell['sha256'][:16]}.bend"
        path.write_text(source)
        seen = {lane: gate.run([*commands['check'], path]) for lane, commands in lanes.items()}
        seen_outcome = {lane: outcome(result) for lane, result in seen.items()}
        gate.require(len(set(seen_outcome.values())) == 1, (name, 'lanes disagree', cell, seen_outcome))
        got = seen_outcome['native']
        seed_accepted = frozen_cell['seed']['exit'] == 0
        gate.require(not (seed_accepted and got.startswith('Invalid')), (name, 'D4: the seed accepts, Knot reports Invalid', cell, got))
        gate.require(seed_accepted or got != 'Accepted', (name, 'the seed rejects, Knot accepts', cell))
        want = expected(frozen_cell)
        if want is not None:
            gate.require(got == '\t'.join(want['diagnostic'].split('\t')[:3]), (name, 'reviewed outcome', cell, got, want))
        return seed_accepted, got

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(one, zip(cells, frozen)))
    table = {}
    for seed_accepted, got in results:
        key = f"seed-{'Accepted' if seed_accepted else 'Rejected'} knot-{got.replace(chr(9), ' ')}"
        table[key] = table.get(key, 0) + 1
    record[name] = {'cells': len(results), 'outcomes': dict(sorted(table.items()))}


def run_mutants(record, pool, mutants):
    """`gate.mutants`, with the mutants built four at a time: each has its own directory."""
    def one(mutation):
        directory = BUILD / 'mutants' / mutation['name']
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
        for source in (gate.ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        target = directory / mutation['file']
        text = target.read_text()
        gate.require(text.count(mutation['old']) == 1, ('mutation anchor', mutation['name']))
        target.write_text(text.replace(mutation['old'], mutation['new']))
        entry = directory / 'check-cli.bend'
        proof = gate.successful([*gate.SEED, entry, '--check-only'])
        gate.require(proof['stdout'].strip() == 'All terms check.', proof)
        case = pool[mutation['witness']]
        expected = case['knot']
        item = {'name': mutation['name'], 'file': mutation['file'], 'old': mutation['old'], 'new': mutation['new'],
                'mutated_sha256': gate.digest(target), 'typecheck': proof, 'witness': mutation['witness'],
                'expected': expected, 'lanes': {}}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            output = directory / ('mutant' + suffix)
            build = gate.successful([*gate.SEED, entry, '-o', output])
            actual = gate.run([*runtime, output, gate.ROOT / case['file']])
            if mutation['wrong']['exit'] == 0:
                gate.checked(actual)
            else:
                gate.diagnostic(actual, mutation['wrong'])
            try:
                gate.checked(actual) if expected['exit'] == 0 else gate.diagnostic(actual, expected)
            except AssertionError:
                pass
            else:
                raise AssertionError(('mutant survived', mutation['name'], actual))
            item['lanes'][lane] = {'build': build, 'actual': actual, 'outcome': 'semantic-kill'}
        return item

    with ThreadPoolExecutor(max_workers=WORKERS) as workers:
        record['mutants'] = list(workers.map(one, mutants))


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    (gate.ROOT / '.local').mkdir(exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round13-expectations.json').read_text())
    frozen = json.loads((HERE / 'round13-grid.json').read_text())
    pool = {c['name']: c for c in manifest['fixtures']}
    for earlier in ('round10', 'round11', 'round12'):
        for c in json.loads((HERE / f'{earlier}-expectations.json').read_text())['fixtures']:
            pool.setdefault(c['name'], c)
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round13-expectations.json', HERE / 'round13-grid.json', *sorted((HERE / 'round13-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round13_seed.py'])
        record['proofs'] = {}
        for entry in sorted((gate.ROOT / 'src').glob('*PROOF.bend')):
            proof = gate.successful([*gate.SEED, entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry.name] = proof
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        sweep(record, 'grid', seed.grid_cells(), frozen['cells'], lanes, lambda cell: cell['knot'])
        sweep(record, 'zoo', seed.zoo_cells(), frozen['zoo'], lanes, lambda cell: None)
        run_mutants(record, pool, MUTANTS)
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-13 inputs changed')
        cases = manifest['fixtures']
        accepted = sum(c['knot']['exit'] == 0 for c in cases)
        exhausted_host = [(item['name'], lane) for item in record['fixtures'] for lane, seen in item['lanes'].items()
                          if seen.get('compile', {}).get('outcome') == 'Exhausted (host)']
        gate.require(all(lane == 'bun' for _, lane in exhausted_host), ('only the Bun lane may exhaust its host', exhausted_host))
        record['host_exhausted'] = exhausted_host
        record['counts'] = {'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants']),
                            'seed_fixtures': len(cases), 'seed_calls': sum(len(c['calls']) for c in cases),
                            'accepted_books': accepted, 'check_observations': 2 * len(cases),
                            'evaluator_values': sum(len(c['calls']) for c in cases if c['knot']['exit'] == 0) * 2,
                            'wasm_values': sum(1 for item in record['fixtures'] for seen in item['lanes'].values()
                                               for call in seen.get('calls', []) if call['wasm'] is not None),
                            'rejected_phase_observations': 8 * (len(cases) - accepted),
                            'host_exhausted_modules': len(exhausted_host),
                            'grid_cells': record['grid']['cells'], 'zoo_forms': record['zoo']['cells'],
                            'findings': {f: sum(c['finding'].startswith(f) for c in cases) for f in ('letop', 'argterm', 'bodystart', 'default')}}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest round 13 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
