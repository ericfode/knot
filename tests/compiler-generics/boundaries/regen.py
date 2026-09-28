#!/usr/bin/env python3
"""Seed-only boundary probes; the original frozen corpus is never rewritten."""
import importlib.util
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('generics_seed', HERE.parent / 'regen.py')
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
seed.HERE = HERE
seed.EXPECTATIONS = HERE / 'expectations.json'
seed.FIXTURES = 'tests/compiler-generics/boundaries/fixtures'
seed.WRAPPERS = '.local/compiler-generics/boundary-wrappers'

# This corpus also exposes a literal Kind(&2) enum through the host boundary.
# Constructor tags still come only from declaration order.
original_enums = seed.enums

def boundary_enums(source):
    canonical_headers = re.sub(r'(?m)^type (\w+) is Kind\(&2\):$',
                               r'type \1 is Data:', source)
    return original_enums(canonical_headers)

seed.enums = boundary_enums

if __name__ == '__main__':
    sys.exit(seed.main())
