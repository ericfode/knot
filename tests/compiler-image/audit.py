#!/usr/bin/env python3
"""Ask the pinned seed about every source that `check-cli` reports Invalid; write seed-audit.json.

Run: BEND_NO_TELEMETRY=1 python3 tests/compiler-image/audit.py CHECK_CLI [OUTPUT.json]

The image gate does not judge Knot's checker: a source that `check-cli` refuses is compared with `check-cli`
itself, live (check.py). This audit is the independent lane for the Invalid verdicts. For each listed source whose
verdict is Invalid it runs `scripts/bend-reference PATH --check-only`, the reference interpreter of the campaign:
  * the seed rejects it: Invalid is right, and `seed_rejects` records it;
  * the seed accepts it (`All terms check.`): Knot's Invalid is a D4 gap, a form the seed accepts that Knot cannot
    yet check. `d4_gaps` records it. The gate does not judge these, as the bootstrap harness does not: it holds the
    image profile to `check-cli`'s answer, whatever that is, and the owning increment closes the gap.
The gate reads this file, verifies that every source it names still has the audited text, and reports any Invalid
verdict that it does not cover; it never runs the seed here (the audit costs about a second a source).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import freeze  # noqa: E402

ROOT = freeze.ROOT
SEED = ROOT / 'scripts/bend-reference'
OUTPUT = HERE / 'seed-audit.json'


def seed_verdict(path: str) -> dict:
    result = subprocess.run([str(SEED), path, '--check-only'], cwd=ROOT, capture_output=True, text=True, timeout=600,
                            env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    text = (result.stdout + result.stderr).strip()
    accepts = result.returncode == 0 and text.splitlines()[-1:] == ['All terms check.']
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {'seed': 'accepts' if accepts else 'rejects', 'exit': result.returncode, 'diagnostic': ' | '.join(lines[:3])[:200]}


def audit(check_cli: Path) -> dict:
    expectations = json.loads((HERE / 'expectations.json').read_text())
    paths = sorted(expectations['sources'])
    seen = freeze.observe_all(check_cli, paths)
    invalid = [p for p in paths if seen[p]['exit'] == 2]
    with ThreadPoolExecutor(max_workers=8) as pool:
        verdicts = list(pool.map(seed_verdict, invalid))
    rows = {}
    for path, verdict in zip(invalid, verdicts):
        rows[path] = {'sha256': freeze.sha((ROOT / path).read_bytes()), 'check_cli': seen[path]['stderr'].rstrip('\n'), **verdict}
    return {
        'schema': 'seed verdicts on the image gate\'s Invalid sources',
        'command': 'scripts/bend-reference PATH --check-only',
        'seed_main_ts_sha256': freeze.sha((ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts').read_bytes()),
        'listed_sources': len(paths),
        'invalid_sources': len(invalid),
        'seed_rejects': sorted(p for p, r in rows.items() if r['seed'] == 'rejects'),
        'd4_gaps': sorted(p for p, r in rows.items() if r['seed'] == 'accepts'),
        'rows': rows,
    }


def main(check_cli: Path, output: Path) -> None:
    document = audit(check_cli)
    output.write_text(json.dumps(document, indent=1, sort_keys=True) + '\n')
    print(f"{document['invalid_sources']} Invalid sources of {document['listed_sources']}: "
          f"{len(document['seed_rejects'])} rejected by the seed, {len(document['d4_gaps'])} D4 gaps")


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT)
