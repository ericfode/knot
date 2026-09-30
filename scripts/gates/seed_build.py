"""Host guards for seed builds; program observations retain their own limits."""
from functools import wraps


def guard_seed_builds(seed):
    prefix = tuple(map(str, seed if isinstance(seed, (tuple, list)) else (seed,)))

    def decorate(run):
        @wraps(run)
        def guarded(argv, timeout=None):
            command = tuple(map(str, argv))
            build = command[:len(prefix)] == prefix and '-o' in command
            options = {} if timeout is None else {'timeout': timeout}
            if build:
                options['timeout'] = max(180, options.get('timeout', 0))
            failed = []
            for attempt in range(3 if build else 1):
                observation = run(argv, **options)
                missing_clang = (observation.get('exit') == 1
                    and observation.get('stdout') == ''
                    and observation.get('stderr', '').startswith('Error: bend needs clang ')
                    and '(found no clang);' in observation.get('stderr', ''))
                if build and missing_clang and attempt < 2:
                    failed.append(observation)
                    continue
                if failed:
                    return {**observation, 'seed_build_retries': failed}
                return observation

        return guarded

    return decorate
