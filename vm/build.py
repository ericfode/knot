#!/usr/bin/env python3
"""Assemble knot-vm-1 with the pinned wabt and check or record its pins.

vm/vm.wat is the source. Lines starting ';;TEST ' are comments in the
production build; the test build strips that prefix, which adds only debug
exports and a stop after every transition when a test asks for one.

    python3 vm/build.py            # check: tool version, source and module pins, byte-identical reassembly
    python3 vm/build.py --write    # rebuild vm/vm.wasm and rewrite vm/build.json after a reviewed edit
    python3 vm/build.py --test OUT # write the test build to OUT
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE, MODULE, PINS = HERE / 'vm.wat', HERE / 'vm.wasm', HERE / 'build.json'
TOOL, FLAGS, PREFIX = 'wat2wasm', [], ';;TEST '


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version() -> str:
    return subprocess.run([TOOL, '--version'], capture_output=True, text=True, check=True).stdout.strip()


def test_source(text: str) -> str:
    return ''.join(line.replace(PREFIX, '', 1) if line.lstrip().startswith(PREFIX) else line
                   for line in text.splitlines(keepends=True))


def assemble(text: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp) / 'vm.wat', Path(tmp) / 'vm.wasm'
        src.write_text(text)
        subprocess.run([TOOL, *FLAGS, str(src), '-o', str(out)], check=True, capture_output=True, text=True)
        return out.read_bytes()


def build() -> tuple[dict, bytes, bytes]:
    text = SOURCE.read_text()
    module, test = assemble(text), assemble(test_source(text))
    return {'tool': TOOL, 'version': version(), 'flags': FLAGS,
            'source': {'path': 'vm/vm.wat', 'sha256': sha(text.encode())},
            'module': {'path': 'vm/vm.wasm', 'sha256': sha(module), 'bytes': len(module)},
            'test_build': {'prefix': PREFIX, 'sha256': sha(test), 'bytes': len(test)}}, module, test


def main(argv) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--test', type=Path)
    args = parser.parse_args(argv)
    pins, module, test = build()
    if args.test:
        args.test.write_bytes(test)
        return 0
    if args.write:
        MODULE.write_bytes(module)
        PINS.write_text(json.dumps(pins, indent=1) + '\n')
        print(f"vm/vm.wasm {pins['module']['sha256']} ({pins['module']['bytes']} bytes)")
        return 0
    frozen = json.loads(PINS.read_text())
    problems = [f'{k}: pinned {frozen.get(k)!r}, got {pins[k]!r}' for k in pins if frozen.get(k) != pins[k]]
    if MODULE.read_bytes() != module:
        problems.append('vm/vm.wasm differs from a fresh assembly of vm/vm.wat')
    print('\n'.join(problems) or f"vm.wasm reassembles byte-identically: {pins['module']['sha256']}")
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
