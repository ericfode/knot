<!-- prechecks packet v1; rule=expectation-independent; increment=closures; head=a1d68911d5fa; base=fa31fec064ba; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-closures/check.py@a1d68911 sha256=21418eea3f6e6cb11981dc6892d15c0338d1fd734c88e41f2baf226bc0aaace4 -->
# Claim
Statements about where expected values come from:

- docs/compiler-campaign/closures-amendments.md: # Closures: expectation amendment before implementation Pinned seed Bend 2.0.29 (`574b6d39a235b539eb19a5c532993a0abb3d11ad`):
- docs/compiler-campaign/closures-amendments.md: Pinned seed Bend 2.0.29 (`574b6d39a235b539eb19a5c532993a0abb3d11ad`):
- docs/compiler-campaign/closures-amendments.md: Pinned seed Bend 2.0.29 (`574b6d39a235b539eb19a5c532993a0abb3d11ad`): ```sh BEND_NO_TELEMETRY=1 bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts tests/compiler-structural/fixtures/function-field.bend ```
- docs/compiler-campaign/closures-amendments.md: This is accepted by the seed and required by `closure-field` and `closure-list` in the frozen closure suite.

# Evidence
`tests/compiler-closures/check.py:97-122` function `seed_regression`, which builds expected values:
```python
   97  def seed_regression(case):
   98      path = HERE / case['file']
   99      require(digest(path) == case['source_sha256'], ('regression source changed', case['name']))
  100      observations = {}
  101      for phase, suffix in [('check_only', ['--check-only']), ('run', [])]:
  102          expected = case['seed'][phase]
  103          require(expected['argv'] == [*SEED, relative(path), *suffix],
  104                  ('regression seed command must check its own source', case['name'], expected))
  105          actual = run(expected['argv'])
  106          require(actual == expected, ('regression seed drift', case['name'], expected, actual))
  107          observations[phase] = actual
  108      accepted = case['knot']['require'] == 'agree'
  109      if accepted:
  110          require(observations['check_only']['exit'] == 0
  111                  and observations['check_only']['stdout'] == 'All terms check.\n'
  112                  and observations['check_only']['stderr'] == '', observations)
  113          require(len(case['calls']) == 1 and case['calls'][0]['entry'] == 'main'
  114                  and case['calls'][0]['ordinals'] == [], 'regression controls use main-only enum calls')
  115          require(observations['run']['exit'] == 0 and observations['run']['stderr'] == ''
  116                  and observations['run']['stdout'] == case['calls'][0]['result']['constructor'] + '{}\n',
  117                  ('regression call disagrees with frozen seed run', case['name']))
  118      else:
  119          require(case['knot']['require'] == 'reject' and not case['calls']
  120                  and observations['check_only']['exit'] == 1 and observations['run']['exit'] == 1,
  121                  ('negative regression must remain seed-rejected', case['name']))
  122      return {'case': case['name'], **observations}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
