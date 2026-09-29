#!/usr/bin/env python3
"""Freeze the pinned seed's verdicts on the generated programs of C1's fast corpus.

    python3 scripts/prechecks/freeze.py            # (re)write tests/prechecks/registry/seed-verdicts.jsonl (needs the pinned seed and bun)
    python3 scripts/prechecks/freeze.py --check    # no seed: the file must cover exactly the generated programs of the corpus

The fast tier of C1 judges the same programs on every head, base and host (lib/generate.py `fixed_programs`), and it
never runs the seed on them: the verdicts below are frozen, keyed by the program's sha256 and the pinned seed's revision,
exactly as the registry rows carry the verdicts of the reviewers' probes. Rerun this whenever a generator, the registry
or the seed pin changes; the unit test `FrozenCorpusTests` fails until the file matches again.

A program with imports is judged only when the `Base` library resolves in this environment (the probe below): the seed
otherwise rejects it for a reason that says nothing about the program, and such a verdict must never be frozen.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import c1_probe_differential as c1  # noqa: E402
from lib import oracle as oracle_mod  # noqa: E402
from lib.seed import SEED_REVISION, Seed  # noqa: E402

BASE_PROBE = 'import Base\n\ndef f() -> U32:\n  7\n'


def generated_programs() -> dict[str, tuple]:
    """{sha: (family, key, text, None)}: the corpus's generated part, which is independent of any checked tree."""
    rows = c1.tool_rows()
    registry = {c1.sha(row['text']) for row in rows}
    corpus = c1.build_corpus(rows, rows, [])
    return {digest: entry for digest, entry in corpus.items() if digest not in registry}


def freeze(scratch: Path, jobs: int = 8) -> list[dict]:
    seed = Seed(c1.TOOL_ROOT, scratch / 'seed-run')
    if not seed.available():
        raise SystemExit('freeze: the pinned seed is not installed')
    programs = generated_programs()
    directory = scratch / 'programs'
    paths = c1.materialize(programs, directory)
    probe = directory / 'base-probe.bend'
    probe.write_text(BASE_PROBE)
    base_ok = seed.check_only(probe)['verdict'] == 'accept'
    if not base_ok:
        print('freeze: the Base library does not resolve here; programs with imports are left without a verdict', file=sys.stderr)
    plain = {d: str(paths[d]) for d, (_f, _k, text, _v) in programs.items() if not oracle_mod.IMPORT.search(text)}
    parsed = seed.parse_many(list(plain.values()))
    todo = []
    rows: dict[str, dict] = {}
    for digest, (family, key, text, _v) in programs.items():
        verdict: dict = {}
        has_import = bool(oracle_mod.IMPORT.search(text))
        if has_import:
            verdict['parse'] = 'skipped'
            verdict['reason'] = 'imports need the loader: parsed and checked together by the seed'
        else:
            parse = parsed[plain[digest]]
            verdict['parse'] = 'ok' if parse['ok'] else 'reject'
            verdict['offset'] = parse.get('beg')
            verdict['expected'] = parse.get('exp')
        if (not has_import and parsed[plain[digest]]['ok']) or (has_import and base_ok):
            todo.append(digest)
        rows[digest] = {'sha256': digest, 'family': family, 'key': key, 'seed': verdict, 'seed_revision': SEED_REVISION}

    def check(digest):
        return digest, seed.check_only(paths[digest])

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        accepted = []
        for digest, row in pool.map(check, todo):
            rows[digest]['seed']['check'] = row['verdict']
            if row['verdict'] == 'accept' and oracle_mod.has_main(programs[digest][2]):
                accepted.append(digest)

        def run(digest):
            return digest, seed.run(paths[digest])

        for digest, row in pool.map(run, accepted):
            rows[digest]['seed']['run'] = row['verdict']
            rows[digest]['seed']['stdout'] = row['stdout']
    return [rows[d] for d in sorted(rows)]


def verify() -> list[str]:
    """Problems with the committed file (none when it covers exactly the generated programs)."""
    wanted = set(generated_programs())
    have: dict[str, dict] = {}
    if c1.TOOL_VERDICTS.is_file():
        for line in c1.TOOL_VERDICTS.read_text(encoding='utf-8').split('\n'):
            if line.strip():
                row = json.loads(line)
                have[row['sha256']] = row
    problems = []
    if wanted - set(have):
        problems.append(f'{len(wanted - set(have))} generated program(s) have no frozen verdict')
    if set(have) - wanted:
        problems.append(f'{len(set(have) - wanted)} frozen verdict(s) belong to no generated program')
    stale = [d for d, row in have.items() if row.get('seed_revision') != SEED_REVISION]
    if stale:
        problems.append(f'{len(stale)} verdict(s) were frozen against another seed revision')
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='verify the committed file against the generators; no seed needed')
    ap.add_argument('--scratch', default=str(c1.TOOL_ROOT / '.local/prechecks/freeze'))
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args(argv)
    if args.check:
        problems = verify()
        for problem in problems:
            print(f'freeze: {problem}', file=sys.stderr)
        print('freeze: the frozen verdicts match the generators' if not problems else 'freeze: rerun scripts/prechecks/freeze.py')
        return 1 if problems else 0
    rows = freeze(Path(args.scratch), args.jobs)
    c1.TOOL_VERDICTS.parent.mkdir(parents=True, exist_ok=True)
    c1.TOOL_VERDICTS.write_text(''.join(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')
    kinds: dict[str, int] = {}
    for row in rows:
        kind = f"{row['seed']['parse']}/{row['seed'].get('check', '-')}"
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f'freeze: {len(rows)} verdicts written to {c1.TOOL_VERDICTS.relative_to(c1.TOOL_ROOT)}: {dict(sorted(kinds.items()))}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
