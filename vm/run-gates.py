#!/usr/bin/env python3
"""Check the frozen Bun pin before invoking the unchanged shared gate runner."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def check_runtime(root: Path, env: dict) -> dict:
    """Refuse PATH drift before any build, using io-host's unchanged frozen Bun pin."""
    wanted = json.loads((root / 'tests/compiler-io/expectations.json').read_bytes())['seed']['bun']
    executable = shutil.which('bun', path=env.get('PATH', ''))
    if executable is None:
        raise RuntimeError(f'Bun is missing from PATH; io-host requires {wanted}')
    probe = subprocess.run([executable, '--version'], cwd=root, env=env,
                           capture_output=True, text=True, timeout=30)
    actual = probe.stdout.strip()
    if probe.returncode != 0 or actual != wanted:
        raise RuntimeError(f'Bun version mismatch: PATH selects {actual!r} at {executable}; '
                           f'io-host requires {wanted}. Select the pinned runtime before running gates.')
    return {'bun': {'version': actual, 'executable': executable}}


def main(argv=None) -> int:
    env = dict(os.environ, BEND_NO_TELEMETRY='1')
    try:
        check_runtime(ROOT, env)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        return 1
    args = sys.argv[1:] if argv is None else argv
    return subprocess.run(['npm', 'run', '-s', 'gates', '--', *args], cwd=ROOT, env=env).returncode


if __name__ == '__main__':
    raise SystemExit(main())
