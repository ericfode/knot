#!/usr/bin/env python3
"""Write expectations.json for the image gate, before src/image.bend exists (D7).

Every entry comes from an independent lane: main's own `check-cli` (the checker's verdict and the
core it displays) and reference.py (the bytes a checked book must encode to). The gate recomputes
both and requires them equal to the frozen file, so the file cannot drift toward an
implementation. Run: python3 tests/compiler-image/freeze.py CHECK_CLI OUTPUT.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference as R  # noqa: E402
import synthetic as X  # noqa: E402

ROOT = R.ROOT


def sources() -> list:
    """The frozen suites' sources: every suite fixture, the subset corpus, the golden sources and this
    gate's witnesses."""
    found = set()
    for pattern in ('tests/*/fixtures/**/*.bend', 'tests/subsets/**/*.bend', 'vm/golden/*.bend',
                    'tests/compiler-image/witnesses/*.bend'):
        found |= {p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern)}
    return sorted(found)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def observe(check_cli: Path, path: str) -> dict:
    result = subprocess.run([str(check_cli), path], cwd=ROOT, capture_output=True, text=True,
                            env={'BEND_NO_TELEMETRY': '1', 'PATH': '/usr/bin:/bin'})
    return {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def document(check_cli: Path) -> dict:
    paths = sources()
    with ThreadPoolExecutor(max_workers=8) as pool:
        seen = list(pool.map(lambda p: observe(check_cli, p), paths))
    table = {}
    for path, seen_one in zip(paths, seen):
        text = (ROOT / path).read_text()
        entry = {'sha256': sha(text.encode()), 'check': {'exit': seen_one['exit'], 'stderr': seen_one['stderr']}}
        if seen_one['exit'] == 0:
            image = R.image(text, seen_one['stdout'])
            entry['image'] = {'sha256': sha(image), 'bytes': len(image)}
            golden = (ROOT / path).with_suffix('.kimg')
            if path.startswith('vm/golden/'):
                assert golden.read_bytes() == image, f'{path}: reference differs from the committed golden image'
                entry['golden'] = True
        table[path] = entry
    synthetic = R.codec.encode(X.plan(), R.DIGEST)
    baseline = json.loads((ROOT / 'tests/compiler-fields-wasm/enum-baseline.json').read_text())
    frozen = {
        'schema': 'knot image gate expectations',
        'frozen': 'before src/image.bend existed; sources: main check-cli, images: tests/compiler-image/reference.py',
        'base_sha256': R.REGISTRY['base']['sha256'],
        'sources': table,
        'default_module_hashes': baseline,
        # Literal contract of the image profile, fixed before implementation. Words are 4 bytes; the
        # image ceiling is SPEC section 4's 4,194,304 words, so the output cap admits every valid image.
        'profile': {
            'flag': '--profile=knot-image-1',
            'arguments': '--profile=knot-image-1 source output [characters parser-depth checker-depth emitter-depth output-bytes]',
            'default_arguments_unchanged': 'source output [characters parser-depth checker-depth emitter-depth output-bytes]',
            'defaults': {'characters': 1048576, 'parser_depth': 512, 'checker_depth': 512,
                         'emitter_depth': 1048576, 'output_bytes': 16777216},
            'maximum_overrides': {'characters': 4194304, 'parser_depth': 4096, 'checker_depth': 4096,
                                  'emitter_depth': 1048576, 'output_bytes': 16777216},
            'default_profile': {'characters': 65536, 'output_bytes_maximum': 1048576},
            'chunk_bytes': 65536,
            'built_record': 'Built<TAB>byte-count',
            'exhausted_phase': 'compile',
        },
        # base.bend is 67,190 characters (VM-DESIGN.md): the default profile must stay exhausted at the
        # unchanged 65,536 cap, and the image profile admit the same book, whose image is unchanged.
        'character_cap': {'padded_characters': 67190, 'book': 'vm/golden/let.bend'},
        'synthetic': {'functions': X.FUNCTIONS, 'lets': X.LETS, 'fields': X.FIELDS,
                      'source_bytes': len(X.source().encode()), 'source_sha256': sha(X.source().encode()),
                      'image_bytes': len(synthetic), 'image_sha256': sha(synthetic),
                      'minimum_image_bytes': 4 * 1024 * 1024},
    }
    return frozen


def main(check_cli: Path, output: Path) -> None:
    frozen = document(check_cli)
    output.write_text(json.dumps(frozen, indent=1, sort_keys=True) + '\n')
    table = frozen['sources']
    accepted = sum(1 for e in table.values() if 'image' in e)
    print(f'{len(table)} sources, {accepted} accepted, {sum(1 for e in table.values() if e.get("golden"))} golden')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
