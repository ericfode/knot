import unittest

from seed_build import guard_seed_builds


MISSING_CLANG = {'exit': 1, 'stdout': '', 'stderr':
    'Error: bend needs clang 14 or newer to build binaries (found no clang); install clang\n'}
SUCCESS = {'exit': 0, 'stdout': '', 'stderr': ''}


class SeedBuildGuardTests(unittest.TestCase):
    def drive(self, observations, argv=('seed', 'source.bend', '-o', 'binary'), timeout=None):
        calls = []

        @guard_seed_builds(('seed',))
        def run(command, timeout=30):
            calls.append((tuple(command), timeout))
            return observations[min(len(calls) - 1, len(observations) - 1)]

        return run(argv, timeout), calls

    def test_records_failed_discovery_before_success(self):
        result, calls = self.drive([MISSING_CLANG, SUCCESS])
        self.assertEqual(result, {**SUCCESS, 'seed_build_retries': [MISSING_CLANG]})
        self.assertEqual([timeout for _, timeout in calls], [180, 180])

    def test_persistent_missing_compiler_fails_after_three_attempts(self):
        result, calls = self.drive([MISSING_CLANG])
        self.assertEqual(result['exit'], 1)
        self.assertEqual(result['seed_build_retries'], [MISSING_CLANG, MISSING_CLANG])
        self.assertEqual(len(calls), 3)

    def test_program_error_is_never_retried(self):
        result, calls = self.drive([MISSING_CLANG, SUCCESS], ('program', '-o', 'binary'))
        self.assertEqual(result, MISSING_CLANG)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 30)

    def test_interpreter_error_is_never_retried(self):
        result, calls = self.drive([MISSING_CLANG, SUCCESS], ('seed', 'source.bend'))
        self.assertEqual(result, MISSING_CLANG)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 30)

    def test_build_errors_timeouts_and_semantic_failures_are_never_retried(self):
        failures = [
            {'exit': 1, 'stdout': '', 'stderr': 'Error: Invalid program\n'},
            {'exit': None, 'stdout': '', 'stderr': '', 'outcome': 'harness-timeout'},
            {'exit': 1, 'stdout': 'semantic result', 'stderr': MISSING_CLANG['stderr']},
            {'exit': 2, 'stdout': '', 'stderr': MISSING_CLANG['stderr']},
            {'exit': 1, 'stdout': '', 'stderr':
                'Error: bend needs clang 14 (found clang 13 as clang); install clang\n'},
        ]
        for failure in failures:
            with self.subTest(failure=failure):
                result, calls = self.drive([failure, SUCCESS])
                self.assertEqual(result, failure)
                self.assertEqual(len(calls), 1)

    def test_larger_build_hang_guard_is_preserved(self):
        result, calls = self.drive([SUCCESS], timeout=240)
        self.assertEqual(result, SUCCESS)
        self.assertEqual(calls[0][1], 240)

    def test_program_timeout_is_preserved(self):
        result, calls = self.drive([SUCCESS], ('seed', 'source.bend'), timeout=7)
        self.assertEqual(result, SUCCESS)
        self.assertEqual(calls[0][1], 7)

    def test_multi_argument_seed_prefix_matches_exactly(self):
        calls = []

        @guard_seed_builds(('bun', '/pinned/main.ts'))
        def run(argv, timeout=30):
            calls.append(timeout)
            return SUCCESS

        run(('bun', '/pinned/main.ts', 'source.bend', '-o', 'binary'))
        run(('bun', '/other/main.ts', 'source.bend', '-o', 'binary'))
        self.assertEqual(calls, [180, 30])


if __name__ == '__main__':
    unittest.main()
