#!/usr/bin/env python3
"""Seed-only value-argument applications; existing frozen corpora are never rewritten."""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('generics_seed', HERE.parent / 'regen.py')
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
seed.HERE = HERE
seed.EXPECTATIONS = HERE / 'expectations.json'
seed.FIXTURES = 'tests/compiler-generics/value-arguments/fixtures'
seed.WRAPPERS = '.local/compiler-generics/value-argument-wrappers'

if __name__ == '__main__':
    sys.exit(seed.main())
