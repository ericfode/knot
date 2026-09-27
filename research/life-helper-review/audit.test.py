#!/usr/bin/env python3
"""Offline mutation tests; all Jev responses are injected local mock objects."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('helper_audit', HERE / 'audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

SOURCE = 'def head(x: U32) -> U32:\n  x\n\ndef main() -> U32:\n  head(1)\n'


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='life-helper-audit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'source.snapshot').write_text(SOURCE)
        (self.root / 'broken.snapshot').write_text('def broken(:\n')
        self.manifest_path = self.root / 'manifest.json'
        self.config_path = self.root / 'config.json'
        self.manifest = {'root': str(self.root), 'entries': [
            {'id': 'private-author-a', 'source': 'source.snapshot', 'source_sha256': audit.sha(SOURCE),
                'deterministic_passed': True, 'semantic_clean': True, 'group': 'r2-v3', 'legacy_policy': 'v3'},
            {'id': 'compiler-rejected', 'source': 'broken.snapshot', 'source_sha256': audit.sha('def broken(:\n'),
                'deterministic_passed': False, 'semantic_clean': None, 'group': 'historical-continuation', 'legacy_policy': 'v2'},
        ]}
        save(self.manifest_path, self.manifest)
        self.config_path.write_bytes((HERE / 'config.json').read_bytes())
        script = r'''
import {reviewManifest} from './research/life-helper-review/review.mjs';
const [manifestPath,configPath,output]=process.argv.slice(1);
const fetchImpl=async(_url,{body})=>{
 const request=JSON.parse(body);
 const answers=Object.fromEntries(Object.entries(request.questions).map(([id,q])=>[id,{type:'score',score:q.criteria.length-1,
   confidence:1,probabilities:Object.fromEntries(q.criteria.map((_,i)=>[String(i),i===q.criteria.length-1?1:0]))}]));
 return new Response(JSON.stringify({model:'jev-1.13.0',answers,usage:{input_tokens:10,output_tokens:2}}),{status:200});
};
const result=await reviewManifest({manifestPath,configPath,output,live:true,loadEnv:false,env:{TYPESAFE_API_KEY:'fake'},fetchImpl});
console.log(result.report_path);
'''
        result = subprocess.run(['node', '--input-type=module', '-e', script, str(self.manifest_path),
            str(self.config_path), str(self.root / 'output')], cwd=ROOT, capture_output=True, text=True, check=True)
        self.report_path = Path(result.stdout.strip())
        self.report = audit.load(self.report_path)

    def check(self):
        return audit.audit_report(self.manifest_path, self.config_path, self.report_path)

    def changed_report(self, callback):
        callback(self.report)
        save(self.report_path, self.report)

    def failure(self, code):
        result = self.check()
        self.assertFalse(result['audit_passed'])
        self.assertIn(code, [error['code'] for error in result['errors']])

    def test_correct_full_pass_and_explicit_parser_rejection_are_distinct(self):
        result = self.check()
        self.assertTrue(result['audit_passed'], result['errors'])
        self.assertEqual(result['summary']['full_pass'], 1)
        self.assertEqual(result['summary']['preflight_rejected'], 1)
        self.assertEqual({g['legacy_policy'] for g in result['comparison_groups']}, {'v2', 'v3'})
        self.assertEqual(result['comparisons'][1]['status'], 'preflight_rejected')

    def test_wrong_full_pass_boolean_is_recomputed(self):
        self.changed_report(lambda report: report['entries'][0].update(full_pass=False))
        self.failure('outcome_recomputation_mismatch')

    def test_fixed_gate_cannot_be_changed_in_result(self):
        self.changed_report(lambda report: report['entries'][0].update(semantic_clean=None))
        self.failure('fixed_gate_mismatch')

    def test_missing_main_support_is_coverage_error(self):
        self.changed_report(lambda report: report['entries'][0]['support_assessments'].pop())
        self.failure('support_assessment_coverage_mismatch')

    def test_missing_family_axis_is_coverage_error(self):
        self.changed_report(lambda report: report['entries'][0]['family_assessments'].pop())
        self.failure('family_assessment_coverage_mismatch')

    def test_current_source_hash_drift_is_caught(self):
        (self.root / 'source.snapshot').write_text(SOURCE + '\n')
        self.failure('run_input_identity_drift')

    def test_request_metadata_leak_is_caught_even_when_receipt_remains_complete(self):
        directory = Path(self.report['requests'][0]['receipt_path']).parent
        request = audit.load(directory / 'request.json')
        request['state']['author'] = 'private-author-a'
        save(directory / 'request.json', request)
        self.failure('request_state_or_metadata_leak')

    def test_response_hash_drift_is_caught(self):
        path = Path(self.report['requests'][0]['receipt_path']).parent / 'response.txt'
        path.write_bytes(path.read_bytes() + b' ')
        self.failure('response_hash_drift')

    def test_response_model_is_checked_after_coherent_hash_rewrite(self):
        row = self.report['requests'][0]
        receipt_path = Path(row['receipt_path'])
        response_path = receipt_path.parent / 'response.txt'
        response = audit.load(response_path)
        response['model'] = 'jev-latest'
        save(response_path, response)
        receipt = audit.load(receipt_path)
        receipt['response_sha256'] = audit.file_sha(response_path)
        receipt['resolved_model'] = 'jev-latest'
        save(receipt_path, receipt)
        row['receipt'] = receipt
        row['receipt_sha256'] = audit.file_sha(receipt_path)
        save(self.report_path, self.report)
        self.failure('resolved_model_mismatch')

    def test_target_mass_is_recomputed(self):
        self.changed_report(lambda report: report['entries'][0]['family_assessments'][0].update(target_probability=0.9))
        self.failure('target_mass_mismatch')

    def test_source_review_identity_drift_is_caught(self):
        self.changed_report(lambda report: report['identity']['implementation']['files'].update({'scripts/perch-bend.mjs': '0' * 64}))
        self.failure('implementation_hash_drift')

    def test_usage_cannot_count_shared_or_reused_answers_twice(self):
        self.changed_report(lambda report: report['usage']['fresh'].update(input_tokens=60))
        self.failure('usage_totals_mismatch')

    def test_json_number_normalization_preserves_values_but_not_booleans(self):
        self.assertTrue(audit.same({'0': 0.0, '1': 1.0}, {'1': 1, '0': 0}))
        self.assertFalse(audit.same(True, 1))
        self.assertFalse(audit.same([1, 2], [2, 1]))
        self.assertEqual(audit.left_sum([0.1, 0.2, 0.3]), 0.6000000000000001)


if __name__ == '__main__':
    unittest.main()
