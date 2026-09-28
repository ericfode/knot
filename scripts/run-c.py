#!/usr/bin/env python3
"""Compile a Knot C artifact with the system C99 compiler and invoke its shim."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ['-O2', '-std=c99', '-Wall', '-Werror', '-fwrapv']


def main():
    if len(sys.argv) < 3:
        print('HostFailure\tc\texpected source.c export [ordinal ...]', file=sys.stderr)
        return 5
    source = Path(sys.argv[1]).resolve()
    build = ROOT / '.local/compiler-c/host'
    try:
        size = source.stat().st_size
        build.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build) as directory:
            binary = Path(directory) / 'program'
            compiled = subprocess.run(['cc', *FLAGS, f'-DKNOT_SOURCE_BYTES={size}',
                                       str(source), '-o', str(binary)],
                                      capture_output=True, text=True, timeout=120)
            if compiled.returncode:
                print('HostFailure\tc-compile\t' + compiled.stderr.strip(), file=sys.stderr)
                return 5
            result = subprocess.run([str(binary), *sys.argv[2:]], timeout=60)
            if result.returncode in (0, 4, 5, 6):
                return result.returncode
            print(f'HostFailure\tc-run\texit {result.returncode}', file=sys.stderr)
            return 5
    except subprocess.TimeoutExpired:
        print('Exhausted\tc-host\ttimeout', file=sys.stderr)
        return 4
    except OSError as error:
        print(f'HostFailure\tc-host\t{error}', file=sys.stderr)
        return 5


if __name__ == '__main__':
    sys.exit(main())
