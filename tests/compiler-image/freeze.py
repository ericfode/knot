#!/usr/bin/env python3
"""Write expectations.json for the image gate (D7). Run: python3 tests/compiler-image/freeze.py CHECK_CLI OUTPUT.json

Frozen, and from which lane:
  * the explicit list of sources the gate judges. It is discovered here, once, and reviewed in the diff of the
    file; the gate never globs, so a merge that adds a fixture or a golden changes nothing it judges;
  * for each source that `check-cli` accepts, the sha256 and size of the image that reference.py derives from the
    source text and the core `check-cli` displays. That lane shares no Bend code with the encoder, and the gate
    recomputes it and requires it unchanged, so the file cannot drift toward an implementation;
  * the committed golden images that the Bend codec must read, the profile's contract, the padded-source case and
    the synthetic book.
Not frozen: the verdict on any other source. The gate compares the image profile with a `check-cli` built from the
same tree in the same run, so no expectation is a snapshot of Knot's own checker; the pinned seed's verdict on
every Invalid source is recorded in seed-audit.json (audit.py), where a source the seed accepts is a D4 gap that
this gate does not judge.
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


def discover() -> list:
    """The frozen suites' sources: every suite fixture, the subset corpus, the golden sources and this gate's
    witnesses. Only a freeze calls this; the gate reads the list it wrote."""
    found = set()
    for pattern in ('tests/*/fixtures/**/*.bend', 'tests/subsets/**/*.bend', 'vm/golden/*.bend',
                    'tests/compiler-image/witnesses/*.bend'):
        found |= {p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern)}
    return sorted(found)


def golden_images() -> list:
    return sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'vm/golden').glob('*.kimg'))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def observe(check_cli: Path, path: str) -> dict:
    result = subprocess.run([str(check_cli), path], cwd=ROOT, capture_output=True, text=True,
                            env={'BEND_NO_TELEMETRY': '1', 'PATH': '/usr/bin:/bin'})
    return {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def observe_all(check_cli: Path, paths: list) -> dict:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(paths, pool.map(lambda p: observe(check_cli, p), paths)))


def reference_image(path: str, seen: dict) -> bytes:
    """The bytes a source that `check-cli` accepts must encode to, from reference.py alone."""
    return R.image((ROOT / path).read_text(), seen['stdout'])


def contract() -> dict:
    """The frozen document less its two lists: every part that no source and no check-cli verdict decides. The
    gate recomputes this and requires it unchanged."""
    synthetic = R.codec.encode(X.plan(), R.DIGEST)
    baseline = json.loads((ROOT / 'tests/compiler-fields-wasm/enum-baseline.json').read_text())
    return {
        'schema': 'knot image gate expectations 2',
        'frozen': 'the source list and the images of the books check-cli accepts (reference.py); no verdict of check-cli',
        'base_sha256': R.REGISTRY['base']['sha256'],
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


def document(check_cli: Path, paths: list) -> dict:
    seen = observe_all(check_cli, paths)
    table = {}
    for path in paths:
        text = (ROOT / path).read_text()
        entry = {'sha256': sha(text.encode())}
        if seen[path]['exit'] == 0:
            image = reference_image(path, seen[path])
            entry['image'] = {'sha256': sha(image), 'bytes': len(image)}
            if path.startswith('vm/golden/'):
                assert (ROOT / path).with_suffix('.kimg').read_bytes() == image, \
                    f'{path}: reference differs from the committed golden image'
                entry['golden'] = True
        table[path] = entry
    return {**contract(), 'sources': table, 'golden_images': golden_images()}


def main(check_cli: Path, output: Path) -> None:
    frozen = document(check_cli, discover())
    output.write_text(json.dumps(frozen, indent=1, sort_keys=True) + '\n')
    table = frozen['sources']
    accepted = sum(1 for e in table.values() if 'image' in e)
    print(f'{len(table)} sources, {accepted} accepted, {sum(1 for e in table.values() if e.get("golden"))} golden, '
          f'{len(frozen["golden_images"])} golden images')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
