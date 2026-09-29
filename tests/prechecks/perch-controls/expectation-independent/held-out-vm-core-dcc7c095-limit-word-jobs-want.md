<!-- prechecks packet v1; rule=expectation-independent; increment=vm-core; head=dcc7c095bf5e; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/CORE.md@dcc7c095 sha256=44dfee24fdfeac88c6a55f0214026eb088bf7967e9807189e757262e159e1626; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a; vm/check-core.py@dcc7c095 sha256=d4a614b6dc4f747d0a4843a7bac53f42e29ffe9e0059677dbc8a50b7a06a850a -->
# Claim
`vm/CORE.md:68-71`

> - 7,741 images that set one word of a limit (each section's record count, each
>   function's arity and `slots`, each Closure's `slots`) to values around its
>   limit and, for a count, around the fit of two words per record: all refused,
>   516 of them at a limit.

# Evidence
`vm/check-core.py:634-652` (compare)

```
  634  def compare(kind: str, corpus: list, outcomes: dict) -> dict:
  635      """The VM refuses each image of a corpus with the reference codec's first defect, a limit of
  636      section 4 as Exhausted kind 2 among them, admits what the reference admits, and never traps.
  637      An image the reference cannot decode is counted, not compared."""
  638      tally = {'refused': 0, 'limits': 0, 'accepted': 0, 'reference_crash': 0}
  639      for r in corpus:
  640          g = outcomes[r['label']]
  641          require(clean(g), f"{kind} {r['label']} is not a clean outcome: {g['status']} {g['stderr']!r}")
  642          ref = r['reference']
  643          if ref is None:
  644              require(observed_reason(g) is None, f"{kind} {r['label']}: reference admits it, VM refused {g['stderr']!r}")
  645              tally['accepted'] += 1
  646          elif ref.startswith('reference-crash'):
  647              tally['reference_crash'] += 1
  648          else:
  649              require(observed_reason(g) == expected_reason(ref), f"{kind} {r['label']}: VM {g['stderr']!r}, reference {ref!r}")
  650              tally['refused'] += 1
  651              tally['limits'] += ref.startswith('Exhausted')
  652      return tally
```

`vm/check-core.py:872-878` (mutants of group limit-words)

```
  872      ('record-fit-exclusive', 'a count that exactly fills the words that remain is one they cannot hold',
  873       [('      (if (i32.gt_u (local.get $count) (i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))\n',
  874         '      (if (i32.ge_u (local.get $count) (i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))\n')],
  875       'limit-words'),
  876      ('record-fit-one-word', 'a record takes one word of the words that remain, not two',
  877       [('(i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))', '(i32.sub (global.get $W) (local.get $at)))')],
  878       'limit-words'),
```

`vm/check-core.py:903-903` (main)

```
  903      module, test = HERE / 'vm.wasm', BUILD / 'vm-test.wasm'
```

`vm/check-core.py:1082-1084` (main: traced)

```
 1082      def traced(rows, where, timeout=600):
 1083          return harness([{'id': r['label'], 'wasm': str(test), 'files': {r['argv'][0]: str(where / r['argv'][0])},
 1084                           'argv': r['argv'], 'trace': 'yields'} for r in rows], timeout)
```

`vm/check-core.py:1201-1205` (main)

```
 1201      limit_words = BUILD / 'limit-words'
 1202      limit_words.mkdir()
 1203      words_corpus = limit_corpus(images, reg, digest, limit_words)
 1204      words_seen = traced(words_corpus, limit_words, timeout=1200)
 1205      words_tally = compare('limit word', words_corpus, words_seen)
```

`vm/check-core.py:1213-1216` (main: the mutants are edits of vm.wat)

```
 1213      # mutants: a changed observation in their group, never a crash, except group `trap`, whose
 1214      # defect is a trap where section 5 gives an outcome. Runs use the test build, so a golden
 1215      # also compares the VM's own outcome registers.
 1216      source = (HERE / 'vm.wat').read_text()
```

`vm/check-core.py:1243-1245` (main: word_jobs)

```
 1243      word_jobs = [{'id': f"limit-word:{r['label']}", 'files': {r['argv'][0]: str(limit_words / r['argv'][0])},
 1244                    'argv': r['argv'], 'want': {k: words_seen[r['label']][k] for k in ('exit', 'stdout', 'stderr')},
 1245                    'dump': {k: words_seen[r['label']]['state'][k] for k in ('outcome', 'cause')}} for r in words_corpus]
```

`vm/check-core.py:1252-1255` (main: groups)

```
 1252                'image-limits': image_limits, 'limit-words': word_jobs}
 1253  
 1254      def observed_wrong(job, out):
 1255          return shown(out, job['want']) != job['want'] or any(out['state'][k] != v for k, v in job.get('dump', {}).items())
```

`vm/check-core.py:1284-1286` (main: the mutant kill)

```
 1284          else:
 1285              wrong = [j['id'] for j in groups[group] if clean(out[j['id']]) and observed_wrong(j, out[j['id']])]
 1286          require(wrong, f'mutant {name} survives group {group} (crashes: {crashed[:5]})')
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
