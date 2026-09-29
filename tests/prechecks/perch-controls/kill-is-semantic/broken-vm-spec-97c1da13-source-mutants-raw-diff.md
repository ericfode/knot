<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-spec; head=97c1da13c0d6; base=481bb3188010; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/check-spec.py@97c1da13 sha256=a6c5ae710f17a5abb0ea114796d36ba276c0845ef0d6df446617a0b42db23dee -->
# Claim
Statements about what counts as a kill:

- vm/DECISIONS.md: No golden exercises that (every golden still validates when `none` never fits an arrow), so the run control `arrow-through-identity`, `id(λx. x)(On{})`, is the one that kills such a mutant.

# Evidence
`vm/check-spec.py:1115-1168` function `codec_mutants`:
```python
 1115  def codec_mutants(plans, images, controls, admitted, describing, reg, digest) -> list:
 1116      """`plans` and `images` include the code-list controls; a decode that differs from its
 1117      plan kills as surely as an encode that differs from its image."""
 1118      source = CODEC.read_text()
 1119      results = []
 1120      for name, edits in CODEC_MUTANTS:
 1121          text = source
 1122          for old, new in edits:
 1123              require(text.count(old) == 1, f'codec mutant {name} is not uniquely located')
 1124              text = text.replace(old, new)
 1125          mutant = load_codec(text)
 1126          killed_by = None
 1127          for case, plan in plans.items():
 1128              try:
 1129                  if mutant.encode(plan, digest) != images[case]:
 1130                      killed_by = f'image {case} differs'
 1131                      break
 1132                  lost = round_trip(plan, images[case], digest, mutant)
 1133                  if lost:
 1134                      killed_by = f'image {case} {lost}'
 1135                      break
 1136              except Exception:
 1137                  continue
 1138          if not killed_by:
 1139              try:
 1140                  killed_by = text_spelling(plans, digest, mutant)
 1141              except Exception:
 1142                  pass
 1143          for label, data, reason, message in [] if killed_by else controls:
 1144              try:
 1145                  got = rejected(data, reg, digest, mutant)
 1146              except Exception:
 1147                  continue
 1148              if got is None or not got.startswith(reason) or message not in got:
 1149                  killed_by = f'control {label}: {got}'
 1150                  break
 1151          for label, data in [] if killed_by else admitted:
 1152              try:
 1153                  got = rejected(data, reg, digest, mutant)
 1154              except Exception:
 1155                  continue
 1156              if got is not None:
 1157                  killed_by = f'admitted control {label}: {got}'
 1158                  break
 1159          if not killed_by:
 1160              try:
 1161                  verdicts = describe_verdicts(describing, mutant)
 1162              except Exception:
 1163                  verdicts = None
 1164              changed = [label for label, _, _, verdict in describing if verdicts and verdicts[label] != verdict]
 1165              if changed:
 1166                  killed_by = f'describe control {changed[0]}: {verdicts[changed[0]]}'
 1167          results.append({'mutant': name, 'killed': killed_by is not None, 'by': killed_by})
 1168      return results
```

`vm/check-spec.py:1179-1192` function `source_mutants`:
```python
 1179  def source_mutants(cases, built) -> list:
 1180      out = []
 1181      for name, old, new in SOURCE_MUTANTS:
 1182          case = cases[name]
 1183          text = (ROOT / case['source']).read_text()
 1184          require(text.count(old) == 1, f'source mutant {name}')
 1185          path = BUILD / 'mutants' / f'{name}.bend'
 1186          path.parent.mkdir(parents=True, exist_ok=True)
 1187          path.write_text(text.replace(old, new))
 1188          mutated = dict(case, source=path.relative_to(ROOT).as_posix())
 1189          got = lanes(mutated, built)
 1190          killed = got['seed'] != case['seed'] and got['eval'] != case['eval']
 1191          out.append({'mutant': f'source:{name}', 'killed': killed, 'seed': got['seed'], 'eval': got['eval']})
 1192      return out
```

`vm/check-spec.py:1271-1434` function `main`:
```python
 1271  def main() -> int:
 1272      parser = argparse.ArgumentParser()
 1273      parser.add_argument('--freeze-new', action='store_true',
 1274                          help='observe and append planned cases that have no frozen row')
 1275      parser.add_argument('--write-expected', action='store_true',
 1276                          help='write vm-expected.json from the frozen observations (first freeze only)')
 1277      args = parser.parse_args()
 1278      BUILD.mkdir(parents=True, exist_ok=True)
 1279      started = datetime.datetime.now(datetime.timezone.utc)
 1280      built = oracles()
 1281      if args.freeze_new:
 1282          freeze(built)
 1283          return 0
 1284  
 1285      reg = codec.registry()
 1286      digest = codec.base_digest(reg)
 1287      record = {'date': started.isoformat(), 'status': 'incomplete',
 1288                'scope': 'knot-image-1 golden images and the frozen VM contract; no VM exists',
 1289                'oracles': {lane: b['commit'] for lane, b in built.items()},
 1290                'inputs': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
 1291                           sorted([*HERE.glob('*.md'), *HERE.glob('*.py'), HERE / 'registry.json',
 1292                                   *GOLDEN.glob('*'), *(HERE / 'oracles').glob('*'), *(HERE / 'bench').glob('*')])
 1293                           if p.is_file()}}
 1294      record['registry'] = check_registry(reg, built)
 1295  
 1296      frozen = json.loads((GOLDEN / 'expectations.json').read_text())
 1297      cases = {c['name']: c for c in frozen['cases']}
 1298      planned = {c['name']: c for c in json.loads((GOLDEN / 'plan.json').read_text())['cases']}
 1299      require(sorted(planned) == sorted(cases) and len(planned) == len(frozen['cases']),
 1300              'plan.json and expectations.json list the same cases')
 1301      for c in cases.values():
 1302          require(sha((ROOT / c['source']).read_bytes()) == c['sha256'], f"frozen source {c['name']}")
 1303          # D7: the literal review written before observation is the seed's printed value
 1304          # (plan.json's first reviews spelled `, ` as `,`); a stdout that is not UTF-8 is
 1305          # reviewed byte for byte, and the Bun cross-check by its stderr.
 1306          if 'seed_stdout_hex' in c:
 1307              require(c['seed_stdout_hex'] == c['seed'].get('stdout_hex'),
 1308                      f"{c['name']}: literal review {c['seed_stdout_hex']}, seed wrote {c['seed'].get('stdout_hex')}")
 1309          else:
 1310              require(c['seed_stdout'] == c['seed']['stdout'],
 1311                      f"{c['name']}: literal review {c['seed_stdout']!r}, seed printed {c['seed']['stdout']!r}")
 1312              require(planned[c['name']]['seed_stdout'].replace(', ', ',') == c['seed_stdout'].replace(', ', ','),
 1313                      f"{c['name']}: plan.json literal review differs from the frozen row")
 1314          if 'seed_bun_stderr' in c:
 1315              require(c['seed_bun_stderr'] == c['seed_bun']['stderr'],
 1316                      f"{c['name']}: literal review {c['seed_bun_stderr']!r}, Bun lane {c['seed_bun']['stderr']!r}")
 1317          for key in ('seed_stdout_hex', 'seed_bun_stderr', 'divergence', 'vm_stdout'):
 1318              require(planned[c['name']].get(key) == c.get(key), f"{c['name']}: plan.json {key} differs from the frozen row")
 1319      sources = {name: (ROOT / c['source']).read_text() for name, c in cases.items()}
 1320  
 1321      with ThreadPoolExecutor(max_workers=4) as pool:
 1322          fresh = dict(zip(cases, pool.map(lambda c: lanes(c, built), cases.values())))
 1323  
 1324      def display(case):
 1325          tool = built[case['lane']]['check']
 1326          return run([tool, *lane_prefix(case), case['source']], 120)
 1327  
 1328      with ThreadPoolExecutor(max_workers=4) as pool:
 1329          displays = dict(zip(cases, pool.map(display, cases.values())))
 1330  
 1331      bounds = json.loads((GOLDEN / 'bounds.json').read_text())['cases']
 1332      plans, images, fixtures, table = {}, {}, [], {}
 1333      for name, case in cases.items():
 1334          require(fresh[name]['seed'] == case['seed'], (name, 'seed drift', fresh[name]['seed'], case['seed']))
 1335          require(fresh[name]['eval'] == case['eval'], (name, 'eval drift', fresh[name]['eval'], case['eval']))
 1336          require(fresh[name].get('seed_bun') == case.get('seed_bun'), (name, 'Bun lane drift', fresh[name].get('seed_bun')))
 1337          plan = json.loads((GOLDEN / f'{name}.plan.json').read_text())
 1338          data = (GOLDEN / f'{name}.kimg').read_bytes()
 1339          require(codec.encode(plan, digest) == data, f'{name}: committed image differs from its plan')
 1340          require(codec.decode(data, digest) == plan, f'{name}: image does not decode to its plan')
 1341          problems = codec.validate(plan, reg)
 1342          require(not problems, (name, problems))
 1343          check_declarations(plan, sources[name])
 1344          shown = displays[name]
 1345          if shown['exit'] == 0:
 1346              derived = from_display(shown['stdout'], plan, sources[name], reg)
 1347              require(derived == plan['functions'], (name, 'plan differs from the checked core', derived))
 1348              view = 'checked-core'
 1349          else:
 1350              require(plan['entry'] == 'program', f'{name}: no checked core for a Book plan')
 1351              view = f"unavailable: {shown['stderr'].strip()}"
 1352          table[name] = vm_expectation(case, plan, bounds, sources[name])
 1353          plans[name], images[name] = plan, data
 1354          fixtures.append({'name': name, 'lane': case['lane'], 'seed_lane': case.get('seed_lane', 'bun'),
 1355                           'features': case['features'], 'image_sha256': sha(data), 'words': len(data) // 4,
 1356                           'plan_matches': view, 'seed': classify(case['seed']), 'eval': classify(case['eval']),
 1357                           'vm': table[name]})
 1358  
 1359      strings = plans['result-string']
 1360      for row in fixtures:
 1361          argument = print_argument(row['name'], sources[row['name']], plans[row['name']], strings, built, reg)
 1362          if argument:
 1363              row['plan_matches'] += f'; {argument}'
 1364  
 1365      expected = {'rule': 'SPEC section 11: the VM owes the seed value wherever the seed succeeds within the '
 1366                          'declared domain and budgets; eval-cli supplies the describe text where it agrees with the seed. '
 1367                          'A Book result outside section 8\'s describe domain is Unsupported, never a bound. '
 1368                          'Output that the seed Bun lane refuses as a non-scalar Char while the native lane exits 0 '
 1369                          'is D20\'s HostFailure io abi, divergent by contract, never agreement; the native bytes '
 1370                          'never classify it.',
 1371                  'fuel': VM_FUEL, 'bounds': bounds, 'cases': table}
 1372      if args.write_expected:
 1373          EXPECTED.write_text(json.dumps(expected, indent=1) + '\n')
 1374      require(json.loads(EXPECTED.read_text()) == expected, 'vm-expected.json differs from the rule')
 1375  
 1376      opcodes = {n[0] for p in plans.values() for n in walk(p)}
 1377      require(opcodes == set(codec.OPCODES), f'uncovered node forms {set(codec.OPCODES) - opcodes}')
 1378      modes = {n[4] for p in plans.values() for n in walk(p) if n[0] == 'case'}
 1379      require(modes == set(codec.CASE_MODES), 'both case modes')
 1380      big = [n for p in plans.values() for n in walk(p) if n[0] == 'lit' and n[2] != 'String' and n[3] >= 1 << 31]
 1381      require(big, 'a boxed scalar constant')
 1382      abstract = [n for p in plans.values() for n in walk(p) if n[0] not in ('branch', 'default') and n[1] is None]
 1383      require(abstract, 'a none-typed node')
 1384  
 1385      planned = plan_controls(plans)
 1386      controls = byte_controls(images, digest) + [
 1387          (f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in planned if m]
 1388      admitted = [(f'plan:{k}', codec.encode(p, digest)) for k, p, m in planned if m is None]
 1389      boundaries = expectation_controls(cases, plans, bounds, sources)
 1390      for label, data, reason, message in controls:
 1391          got = rejected(data, reg, digest)
 1392          require(got is not None and got.startswith(reason) and mes
[truncated after 12,288 bytes; 3,090 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
