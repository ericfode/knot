#!/usr/bin/env python3
"""Offline controls for corpus growth and append-only baseline selection."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import check as gate
import freeze


class CorpusGrowth(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.frozen = json.loads((gate.HERE / 'expectations.json').read_text())
        self.baseline = json.loads((gate.HERE / 'baseline.json').read_text())
        self.generated = copy.deepcopy(self.baseline['generated'])
        for family in ('compiler-wasm', 'compiler-fields-wasm', 'compiler-recursion'):
            source = gate.ROOT / 'tests' / family / 'cases.json'
            target = self.root / source.relative_to(gate.ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for observer in self.frozen['observer_cases']:
            source = gate.ROOT / observer['original']
            target = self.root / observer['original']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        self.addCleanup(patch.stopall)
        patch.object(gate, 'ROOT', self.root).start()
        patch.object(gate, 'BUILD', self.root / '.local/corpus-control').start()
        patch.object(gate, 'successful', side_effect=lambda argv: {'stdout': json.dumps(self.generated)}).start()

    def load(self):
        return gate.load_corpus(self.frozen, self.baseline)

    def append(self, family, case):
        target = self.root / 'tests' / family / 'cases.json'
        data = json.loads(target.read_text())
        data['cases'].append(case)
        target.write_text(json.dumps(data))

    def test_shared_positive_grows_without_baseline_edit(self):
        before, rejects = self.load()
        case = copy.deepcopy(next(c for c in before if c['family'] == 'compiler-wasm'))
        case.update(file='tests/subsets/s1/new-corpus-control.bend', name='new-corpus-control')
        self.append('compiler-wasm', case)
        after, new_rejects = self.load()
        self.assertEqual(len(before) + 1, len(after))
        self.assertEqual(rejects, new_rejects)
        self.assertIn('compiler-wasm-new-corpus-control', {c['key'] for c in after})

    def test_shared_rejections_grow_without_baseline_edit(self):
        before, rejects = self.load()
        case = copy.deepcopy(rejects[0])
        case.update(file='fixtures/new-rejection.bend', name='new-rejection')
        self.append('compiler-recursion', case)
        after, new_rejects = self.load()
        self.assertEqual(before, after)
        self.assertEqual(len(rejects) + 1, len(new_rejects))

    def test_generator_growth_has_no_global_equality_pin(self):
        before, _ = self.load()
        program = copy.deepcopy(next(p for p in self.generated if p['name'].startswith('enum-')))
        program.update(name='enum-8', program='.local/bench/generated/enum-8.bend', args=[7], expected=7)
        self.generated.append(program)
        after, _ = self.load()
        self.assertEqual(len(before) + 1, len(after))
        self.assertIn('bench-enum-8', {c['key'] for c in after})

    def test_changed_recursion_input_is_observed_from_current_source(self):
        observer = self.frozen['observer_cases'][0]
        source = self.root / observer['original']
        source.write_text('# additional shared-source comment\n' + source.read_text())
        cases, _ = self.load()
        current = next(c for c in cases if c['key'] == 'compiler-opt-observer-' + observer['name'])
        self.assertEqual(source.read_text() + observer['suffix'], gate.corpus_path(current).read_text())
        self.assertNotEqual(current['file'], current['source_file'])

    def test_new_structured_input_requires_seeded_wasm_observer(self):
        cases, _ = self.load()
        case = copy.deepcopy(next(c for c in cases if c['family'] == 'compiler-recursion'))
        case.update(name='missing-observer', file='fixtures/missing-observer.bend')
        self.append('compiler-recursion', case)
        with self.assertRaisesRegex(AssertionError, 'seeded exact-tree observer'):
            self.load()

    def test_duplicate_case_key_is_rejected(self):
        cases, _ = self.load()
        self.append('compiler-wasm', next(c for c in cases if c['family'] == 'compiler-wasm'))
        with self.assertRaisesRegex(AssertionError, 'unique corpus keys'):
            self.load()

    def test_freeze_refuses_to_replace_existing_bytes(self):
        cases, _ = self.load()
        case = cases[0]
        with self.assertRaisesRegex(AssertionError, 'cannot be replaced'):
            freeze.select(cases, {case['file']: {}}, [case['key']])
        with self.assertRaisesRegex(AssertionError, 'unknown corpus key'):
            freeze.select(cases, {}, ['absent'])
        self.assertEqual([case], freeze.select(cases, {}, [case['key']]))

    def test_extension_cannot_shadow_original_frozen_entry(self):
        extensions = {'baselines': [copy.deepcopy(self.baseline['cases'][0])], 'observers': []}
        with self.assertRaisesRegex(AssertionError, 'duplicate frozen off baseline'):
            gate.baselines(self.baseline, extensions, {'cases': []})


if __name__ == '__main__':
    unittest.main()
