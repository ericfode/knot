<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=bootstrap; head=dc76dac378e0; base=fa31fec064ba; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-bootstrap/README.md@dc76dac3 sha256=27175fb56e6c5def31a3336ba9cee2a94c1e18123db9fe0f1725bf878d245708; tests/compiler-bootstrap/check.py@dc76dac3 sha256=f46ffe6bfff4aa51321e3372549723fdcc5def6c9754a8ce233e66952bc47cd4 -->
# Claim
tests/compiler-bootstrap/README.md:108-108 (section: Gate verdict (`bootstrap`)) - verbatim text:

> The unmutated copy must pass. All eight mutants must be rejected:

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
`tests/compiler-bootstrap/check.py:413-469` (added)
  413  def mutants(progress) -> list[dict]:
  414      """Scratch copies with substituted recorded classifications; the judge must reject each."""
  415      folder = ROOT / BUILD / 'judge'
  416      folder.mkdir(parents=True, exist_ok=True)
  417  
  418      def knot_blocker(p):
  419          s = next((s for s in p['stages'] if s['status'] == 'blocked' and s['blocker']['source'] == 'knot'), None)
  420          if s is None:  # Nothing blocked any more: substitute into the A2 stage.
  421              s = next(s for s in p['stages'] if s['id'] == 'e2e3.a2')
  422              s.update(status='blocked', agree=0, disagree=0, blocker={'source': 'knot', 'exit': 3, 'stdout': '',
  423                       'stderr': 'Unsupported\tlex\tliteral\t0:1:1:1\n'})
  424          return s['blocker']
  425  
  426      def invalid(row, exit=True, word=True):
  427          if exit:
  428              row['exit'] = 2
  429          if word:
  430              row['stderr'] = 'Invalid\t' + row['stderr'].split('\t', 1)[-1]
  431  
  432      def disagree(p):
  433          s = next(s for s in p['stages'] if s['status'] == 'reached')
  434          s['agree'] -= 1
  435          s['disagree'] += 1
  436  
  437      def silent_skip(p):
  438          s = next((s for s in p['stages'] if s['status'] == 'not-run'), None)
  439          if s is None:
  440              return False
  441          pre = next(x for x in p['stages'] if x['id'] == s['prerequisite'])
  442          pre.update(status='reached', agree=pre['corpus'], disagree=0)
  443          pre.pop('blocker', None)
  444  
  445      cases = (
  446          ('unmutated', 0, lambda p: None),
  447          ('blocker-invalid', 1, lambda p: invalid(knot_blocker(p))),
  448          ('blocker-invalid-word-only', 1, lambda p: invalid(knot_blocker(p), exit=False)),
  449          ('blocker-invalid-exit-only', 1, lambda p: invalid(knot_blocker(p), word=False)),
  450          ('blocker-host-crash', 1, lambda p: knot_blocker(p).update(
  451              exit=1, stderr='error: uncaught RuntimeError: unreachable\n    at main\n')),
  452          ('blocker-signal', 1, lambda p: knot_blocker(p).update(exit=-11, stderr='')),
  453          ('own-source-invalid', 1, lambda p: invalid(p['own_source'][0])),
  454          ('reached-disagreement', 1, disagree),
  455          ('not-run-after-reached', 1, silent_skip),
  456      )
  457      result = []
  458      for label, expected, mutate in cases:
  459          scratch = copy.deepcopy(progress)
  460          if mutate(scratch) is False:
  461              result.append({'name': label, 'applicable': False})
  462              continue
  463          path = folder / f'{label}.json'
  464          path.write_text(json.dumps(scratch, indent=2) + '\n')
  465          r = run([sys.executable, '-B', f'{REL}/check.py', '--judge', path.relative_to(ROOT).as_posix()], 60)
  466          result.append({'name': label, 'expected_exit': expected, 'exit': r['exit'],
  467                         'violations': text(r['stdout']).splitlines(),
  468                         'outcome': 'rejected' if r['exit'] == 1 else 'accepted' if r['exit'] == 0 else 'error'})
  469      return result
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
