import json
import unittest
from unittest import mock

from checks import c5_preflight_delta as c5
from .helpers import RepoTest

MANIFEST = json.dumps({'groups': [{'name': 'parsing', 'files': ['src/parse.bend']}, {'name': 'checking', 'files': ['src/check.bend']}]})
PROFILE = "export const BEND_PARSER_PROFILE = 'bend-2.0.29-observer-v3';\n"
JUDGE = ("const judge = `Judge the declaration against the rubric. Do not infer a potential verdict, previous scores "
         "or missing implementation from the surrounding text.`;\n")


def unit(target, *reasons):
    return {'target': target, 'truncated': bool(reasons), 'limit_reasons': list(reasons)}


def report(units=(), composition=None, groups=None, parser='p1', blockers=0):
    body = {'parser': parser, 'summary': {'units': len(units), 'files': 1, 'truncated_units': sum(1 for u in units if u['truncated'])},
            'structural_blockers': blockers, 'units': list(units), 'composition': composition or {'source_bytes': 1000, 'byte_limit': 48000}}
    if groups is not None:
        body['groups'] = groups
    return body


def group(name, size, files=(), available=True, reasons=()):
    return {'name': name, 'files': list(files) or [f'src/{name}.bend'],
            'summary': {'units': 3, 'truncated_units': 0},
            'composition': {'source_bytes': size, 'byte_limit': 48000, 'available': available, 'reasons': list(reasons)}}


class Stub:
    """Canned preflight reports keyed by (tree label, manifest mode)."""

    def __init__(self, head=None, base=None, head_manifest=None, base_manifest=None, head_error='', base_error=''):
        self.tables = {('head', False): (head, head_error), ('base', False): (base, base_error),
                       ('head manifest', True): (head_manifest, head_error), ('base manifest', True): (base_manifest, base_error)}
        self.calls = []

    def __call__(self, ctx, tree, args, label, timeout=120):
        self.calls.append((label, args))
        return self.tables[(label, any(a.startswith('--manifest=') for a in args))]


class C5Tests(RepoTest):
    def start(self, files=None):
        base = {'src/parse.bend': 'def parse(): 1\n', 'src/check.bend': 'def check(): 1\n',
                'docs/compiler-campaign/manifest.json': MANIFEST, 'scripts/perch-style.mjs': JUDGE,
                'scripts/perch-bend.mjs': PROFILE, 'perch-style.json': '{"a": 1}\n', 'docs/perch-review-log.md': '# log\n'}
        base.update(files or {})
        self.fx.commit('main', base)
        self.fx.branch('campaign/x')

    def run5(self, stub=None, **kw):
        with mock.patch.object(c5, 'preflight', stub or Stub()):
            return self.conditions(c5, **kw)[1]

    def rules(self, result, rule):
        return [c for c in result.conditions if c.rule == rule]

    def test_no_changed_bend_is_not_applicable_to_the_preflight(self):
        self.start()
        self.fx.commit('doc', {'README.md': 'x\n'})
        stub = Stub()
        result = self.run5(stub)
        self.assertEqual([], stub.calls)
        self.assertEqual([], result.conditions)
        self.assertIn('0 changed .bend targets', ' '.join(result.notes))

    def test_new_truncation_is_reported_and_old_truncation_is_not(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})
        stub = Stub(head=report([unit('src/parse.bend::a', 'caller-or-byte-limit'), unit('src/parse.bend::b', 'context-file-limit')]),
                    base=report([unit('src/parse.bend::b', 'context-file-limit')]),
                    head_manifest=report(groups=[group('parsing', 1000), group('checking', 1000)]),
                    base_manifest=report(groups=[group('parsing', 1000), group('checking', 1000)]))
        result = self.run5(stub)
        found = self.rules(result, 'preflight-new-blocker')
        self.assertEqual(['src/parse.bend::a'], [c.subject['target'] for c in found])
        self.assertEqual({'changed_targets': 1, 'units': 2, 'files': 1, 'truncated': 2, 'blockers': 0}.items() <= result.facts['preflight'].items(), True)

    def test_parser_profile_move_reports_no_truncation_delta(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})
        stub = Stub(head=report([unit('src/parse.bend::a', 'context-file-limit')], parser='p2'), base=report([], parser='p1'),
                    head_manifest=report(groups=[]), base_manifest=report(groups=[]))
        result = self.run5(stub)
        self.assertEqual([], self.rules(result, 'preflight-new-blocker'))
        self.assertTrue(any('parser profile' in n for n in result.notes))

    def test_sole_member_outside_every_group_over_the_cap(self):
        """A file that is itself over the cap cannot fit any group review: major, and the fix is to split it."""
        self.start({'src/loose.bend': 'def loose(): 1\n'})
        self.fx.commit('work', {'src/loose.bend': 'def loose(): 2\n# ' + 'x' * 50000 + '\n'})
        over = {'source_bytes': 135255, 'byte_limit': 48000, 'available': False, 'context_files': 7}
        stub = Stub(head=report([], composition=over), base=report([]), head_manifest=report(groups=[]), base_manifest=report(groups=[]))
        found = self.rules(self.run5(stub), 'composition-budget')
        self.assertEqual(['major'], [c.severity for c in found])
        self.assertIn('in no manifest group', found[0].observed)
        self.assertIn('7 helper file(s)', found[0].observed)
        self.assertIn('Split the file', found[0].fix_hint)
        stub = Stub(head=report([], composition=over), base=report([], composition=over),
                    head_manifest=report(groups=[]), base_manifest=report(groups=[]))
        self.assertEqual([], self.rules(self.run5(stub), 'composition-budget'))    # already over the cap at base

    def test_a_small_file_outside_every_group_whose_helper_closure_is_large_is_minor_and_names_the_closure(self):
        """recursion 624228e5: 4,620 bytes of its own, 52,742 with seven helper files; no manifest existed yet."""
        self.start({'src/loose.bend': 'def loose(): 1\n'})
        self.fx.commit('work', {'src/loose.bend': 'def loose(): 2\n'})
        over = {'source_bytes': 52742, 'byte_limit': 48000, 'available': False, 'context_files': 7}
        stub = Stub(head=report([], composition=over), base=report([]), head_manifest=report(groups=[]), base_manifest=report(groups=[]))
        found = self.rules(self.run5(stub), 'composition-budget')
        self.assertEqual(['minor'], [c.severity for c in found])
        self.assertIn('bytes of its own and 7 helper file(s)', found[0].observed)
        self.assertIn('Add it to a group', found[0].fix_hint)
        self.assertNotIn('Split the file', found[0].fix_hint)

    def test_a_file_that_a_group_lists_is_judged_by_its_group_not_alone(self):
        """A new law file added to an existing group composes 52k alone (its helper closure) and 22k as the group reviews it."""
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})               # src/parse.bend is listed by the `parsing` group
        over = {'source_bytes': 52838, 'byte_limit': 48000, 'available': False, 'context_files': 7}
        groups = [group('parsing', 22008, files=['src/parse.bend']), group('checking', 1000)]
        stub = Stub(head=report([], composition=over), base=report([]), head_manifest=report(groups=groups), base_manifest=report(groups=groups))
        result = self.run5(stub)
        self.assertEqual([], self.rules(result, 'composition-budget'))
        self.assertEqual(22008, result.facts['preflight']['groups']['parsing']['bytes'])
        # The group rule still catches the same file when the group itself loses its composition (vm-model's model.bend).
        lost = [group('parsing', 144319, files=['src/parse.bend'], available=False, reasons=['composition_byte_limit']), group('checking', 1000)]
        stub = Stub(head=report([], composition=over), base=report([]), head_manifest=report(groups=lost), base_manifest=report(groups=groups))
        found = self.rules(self.run5(stub), 'composition-budget')
        self.assertEqual([('major', 'parsing')], [(c.severity, c.subject.get('group')) for c in found])

    def test_a_target_that_does_not_parse_is_dropped_and_named_not_a_blind_spot(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n', 'tests/x/bad.bend': 'not bend\n', 'tests/x/worse.bend': 'still not\n'})
        calls = []

        def stub(ctx, tree, args, label, timeout=120):
            calls.append((label, list(args)))
            if args and args[0].startswith('--manifest='):
                return report(groups=[]), ''
            for bad in ('tests/x/bad.bend', 'tests/x/worse.bend'):
                if bad in args:
                    return None, f'Style ranking failed: Bend target does not parse: {bad}'
            return (report([unit('src/parse.bend::a', 'context-file-limit')]) if label == 'head' else report([])), ''

        with mock.patch.object(c5, 'preflight', stub):
            result = self.conditions(c5)[1]
        self.assertEqual(['src/parse.bend::a'], [c.subject['target'] for c in self.rules(result, 'preflight-new-blocker')])
        self.assertEqual(['tests/x/bad.bend', 'tests/x/worse.bend'], result.facts['preflight']['unparsed_targets'])
        self.assertIn('2 changed .bend target(s) do not parse', result.rules_unavailable['preflight-targets'])
        self.assertEqual('conditions', result.finish().outcome)

    def test_manifest_group_budgets_ratchet_against_base(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})
        head_groups = [group('parsing', 48500, available=False, reasons=['composition_byte_limit']), group('checking', 47903),
                       group('scope', 47500)]
        base_groups = [group('parsing', 45000), group('checking', 47903)]
        stub = Stub(head=report([]), base=report([]), head_manifest=report(groups=head_groups), base_manifest=report(groups=base_groups))
        found = {c.subject['group']: c.severity for c in self.rules(self.run5(stub), 'composition-budget')}
        self.assertEqual({'parsing': 'major', 'scope': 'minor'}, {k: v for k, v in found.items() if k != 'checking'})
        self.assertNotIn('checking', found)          # already at 0.2% headroom at base

    def test_unit_cap_and_aborted_runs(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})
        stub = Stub(head=report([]), base=report([]), head_manifest=None, base_manifest=report(groups=[]),
                    head_error='Style run limited to 5000 units; narrow groups or raise max_units')
        result = self.run5(stub)
        found = self.rules(result, 'unit-cap')
        self.assertEqual(('major', 5000), (found[0].severity, found[0].value['max_units']))
        # the group rules read that manifest run, so they did not run: named, never silently absent
        self.assertEqual({'composition-budget (groups)', 'manifest-membership'}, set(result.rules_unavailable))
        self.assertIn('limited to 5000 units', result.rules_unavailable['composition-budget (groups)'])
        self.assertTrue(result.finish().incomplete)

    def test_an_aborted_manifest_run_is_a_blocker_and_names_the_rules_that_did_not_run(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})
        stub = Stub(head=report([]), base=report([]), head_manifest=None, base_manifest=report(groups=[]), head_error='the run crashed')
        result = self.run5(stub)
        self.assertEqual(['run-aborted'], [c.subject['reasons'][0] for c in self.rules(result, 'preflight-new-blocker')])
        self.assertIn('manifest-membership', result.rules_unavailable)

    def test_a_completed_manifest_run_leaves_the_group_rules_running(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse(): 2\n'})
        stub = Stub(head=report([]), base=report([]), head_manifest=report(groups=[group('parsing', 1000)]),
                    base_manifest=report(groups=[group('parsing', 1000)]))
        result = self.run5(stub)
        self.assertNotIn('manifest-membership', result.rules_unavailable)
        self.assertNotIn('composition-budget (groups)', result.rules_unavailable)
        self.assertIn('manifest-membership', result.rules_run)

    def test_manifest_membership(self):
        self.start()
        self.fx.commit('work', {'src/new.bend': 'def n(): 1\n'})
        groups = [group('parsing', 1000, files=['src/parse.bend']), group('checking', 1000, files=['src/check.bend'])]
        stub = Stub(head=report([]), base=report([]), head_manifest=report(groups=groups), base_manifest=report(groups=groups))
        found = self.rules(self.run5(stub), 'manifest-membership')
        self.assertEqual(['src/new.bend'], [c.subject['path'] for c in found])
        stub = Stub(head=report([]), base=report([]), head_manifest=report(groups=[group('parsing', 1, files=['src/parse.bend'])]),
                    base_manifest=report(groups=[group('parsing', 1, files=['src/parse.bend', 'src/old.bend'])]))
        found = [c for c in self.rules(self.run5(stub), 'manifest-membership') if 'dropped' in c.subject]
        self.assertEqual(['src/old.bend'], found[0].subject['dropped'])

    def test_bend_hygiene(self):
        self.start()
        self.fx.commit('work', {'src/parse.bend': 'def parse():\n  # ---- section ----\n  1  # § note\n'})
        kinds = sorted(c.subject['kind'] for c in self.rules(self.run5(Stub(head=report([]), base=report([]),
                       head_manifest=report(groups=[]), base_manifest=report(groups=[]))), 'bend-hygiene'))
        self.assertEqual(['divider', 'non-ascii'], kinds)

    def test_task_provenance(self):
        self.start()
        self.fx.commit('work', {'tests/compiler-x/README.md': 'Run `--task=tests/compiler-x/README.md src/parse.bend` for the review.\n',
                                'src/parse.bend': 'def parse(): 2\n'})
        stub = Stub(head=report([]), base=report([]), head_manifest=report(groups=[]), base_manifest=report(groups=[]))
        found = self.rules(self.run5(stub), 'task-provenance')
        self.assertEqual(1, len(found))
        self.assertEqual('minor', found[0].severity)

    def test_identity_changes_need_a_log_entry(self):
        self.start()
        self.fx.commit('bump', {'scripts/perch-bend.mjs': PROFILE.replace('observer-v3', 'observer-v4')})
        found = self.rules(self.run5(), 'perch-identity-change')
        self.assertEqual(['minor'], [c.severity for c in found])
        self.fx.commit('log it', {'docs/perch-review-log.md': '# log\n\nThe parser profile bump invalidates .perch/cache/style-v1.\n'})
        self.assertEqual([], self.rules(self.run5(), 'perch-identity-change'))

    def test_dropping_a_judge_sentence_is_major(self):
        self.start()
        self.fx.commit('edit prompt', {'scripts/perch-style.mjs': "const judge = `Judge the declaration against the rubric.`;\n"})
        found = self.rules(self.run5(), 'perch-identity-change')
        self.assertEqual(['major'], [c.severity for c in found])
        self.assertIn('potential verdict', found[0].observed)


if __name__ == '__main__':
    unittest.main()
