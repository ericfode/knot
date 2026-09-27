#!/usr/bin/env python3
"""Preserve candidate evidence without build products or duplicated frozen tests."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCRATCH = ROOT / 'packages/symbols/build/memetic-search'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(source, relative, manifest):
    data = source.read_bytes()
    target = HERE / 'candidates' / relative
    if (source.suffix == '.json' and (len(data) > 64000 or source.name.startswith('style'))) or data.endswith(b'\n\n'):
        target = target.with_name(target.name + '.gz')
        encoded = gzip.compress(data, mtime=0)
    else:
        encoded = data
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == encoded, f'Archived evidence changed: {target}'
    else:
        target.write_bytes(encoded)
    manifest.append({'origin': str(source.relative_to(ROOT)),
                     'archive': str(target.relative_to(HERE)),
                     'sha256_uncompressed': digest(data), 'bytes_uncompressed': len(data)})
    return str(target.relative_to(HERE))


def main():
    manifest, variants = [], []
    for lane in ['cps', 'lenses', 'phase']:
        parent = SCRATCH / lane
        for source in sorted(parent.glob('*')):
            if source.is_file() and source.suffix in {'.py', '.json', '.md'}:
                save(source, Path(lane) / source.name, manifest)
        for directory in sorted(parent.iterdir()):
            if not directory.is_dir() or not (directory / 'main.bend').exists():
                continue
            variant = {'lane': lane, 'name': directory.name,
                       'source_sha256': digest((directory / 'main.bend').read_bytes()),
                       'style': []}
            for source in sorted(directory.glob('*')):
                if not source.is_file():
                    continue
                if source.name == 'main.bend':
                    name = source.name + '.snapshot'
                elif source.suffix in {'.snapshot', '.json', '.md', '.py'}:
                    name = source.name
                else:
                    continue
                archive = save(source, Path(lane) / directory.name / name, manifest)
                if source.name.startswith('style') and source.suffix == '.json':
                    receipt = json.loads(source.read_text())
                    variant['style'].append({
                        'receipt': archive, 'coverage': receipt.get('coverage'),
                        'summary': receipt.get('style_summary'),
                        'assessments': receipt.get('assessments'),
                        'rubric_sha256': receipt.get('rubric_sha256'),
                        'requested_model': receipt.get('requested_model')})
            variants.append(variant)
    (HERE / 'candidate-index.json.gz').write_bytes(gzip.compress((json.dumps(
        {'variants': variants, 'manifest': manifest}, indent=2) + '\n').encode(), mtime=0))
    print(f'Archived {len(variants)} candidates and {len(manifest)} evidence files.')


if __name__ == '__main__':
    main()
