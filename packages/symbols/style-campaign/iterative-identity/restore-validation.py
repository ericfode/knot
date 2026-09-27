#!/usr/bin/env python3
"""Restore archived additive evidence into its ignored scratch paths, without clobbering."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCRATCH = (ROOT / 'packages/symbols/build/memetic-search').resolve()
INPUTS = HERE.parent / 'intern-identity-1/inputs'


def restore(path, data):
    assert path.resolve().is_relative_to(SCRATCH), path
    if path.exists():
        assert path.read_bytes() == data, f'Refusing to overwrite different bytes: {path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main():
    archive = json.loads(gzip.decompress((HERE / 'validation-evidence.json.gz').read_bytes()))
    planned, implementations = [], set()
    for item in archive['files']:
        data = item['content'].encode()
        assert hashlib.sha256(data).hexdigest() == item['sha256'], item['path']
        path = ROOT / item['path']
        assert path.resolve().is_relative_to(SCRATCH), path
        if path.exists():
            assert path.read_bytes() == data, f'Refusing to overwrite different bytes: {path}'
        planned.append((path, data))
        if path.name == 'main.bend':
            implementations.add(path.parent)
    for directory in implementations:
        for source in INPUTS.glob('*.bend.snapshot'):
            if source.name != 'main.bend.snapshot':
                planned.append((directory / source.name.removesuffix('.snapshot'), source.read_bytes()))
    # Preflight the complete plan before writing any file.
    for path, data in planned:
        assert path.resolve().is_relative_to(SCRATCH), path
        if path.exists():
            assert path.read_bytes() == data, f'Refusing to overwrite different bytes: {path}'
    for path, data in planned:
        restore(path, data)
    print(f'Restored or verified {len(planned)} source/evidence files. No binaries generated.')


if __name__ == '__main__':
    main()
