import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { assessStyle, prepareStyleTargets, rankRows, runStyleRanking, validateScore } from '../scripts/perch-style.mjs';

const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
const targets = ['a.bend::solve', 'b.bend::solve'];
const args = ['--live', '--json', '--cohort=Add one to an unsigned word', ...targets];
const key = 'offline-secret-must-not-be-recorded';
const source = 'import Base\nimport ./helper.bend as H\ndef solve(x: U32) -> U32: H.next(x)\ndef unrelated() -> U32: 999\n';
const score = (level, dimension = config.dimensions[0]) => ({ type: 'score', score: level, confidence: 1,
  probabilities: Object.fromEntries(dimension.levels.map((_, i) => [i, i === level ? 1 : 0])) });
const criticalityScore = probability => ({ type: 'score', score: probability, confidence: Math.max(probability, 1 - probability),
  probabilities: { 0: 1 - probability, 1: probability } });
const response = (brain = 3, delight = 2, model = 'offline-style-fixture', memetic = 3, criticality = 0,
  diagnostics = { anticipation: 3, payoff: 3 }) => ({ ok: true, json: async () => ({
  model, answers: { maximally_big_brain: score(brain), delightful_to_read: score(delight, config.dimensions[1]),
    highly_memetic: score(memetic, config.dimensions[2]), criticality: criticalityScore(criticality),
    ...Object.fromEntries(config.diagnostic_dimensions.map(d => [d.id, score(diagnostics[d.id], d)])) },
  usage: { input_tokens: 100, output_tokens: 10 },
}) });

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-style-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(config));
  await writeFile(join(root, 'a.bend'), source);
  await writeFile(join(root, 'b.bend'), 'import Base\ndef solve(x: U32) -> U32: U32.add(x,1)\n');
  await writeFile(join(root, 'helper.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,1)\n');
  return root;
}

test('rank preflight uses exact parsed units and working-copy helpers; all inputs validate before paid calls', async t => {
  const root = await fixture(t);
  const units = await prepareStyleTargets([...targets, targets[0]], 'Add one', config, root);
  assert.equal(units.length, 2, 'duplicate selections must not cause paid repeats');
  assert.match(units[0].state.source, /^def solve/);
  assert.ok(!units[0].state.source.includes('unrelated'));
  assert.equal(units[0].state.calls[0].name, 'next');
  assert.deepEqual(units[0].context.files.map(f => f.path), ['a.bend', 'helper.bend']);
  let calls = 0;
  const run = selection => runStyleRanking(['--live', '--cohort=Add one', ...selection], {
    root, env: { PERCH_API_KEY: key }, fetchImpl: async () => { calls++; return response(); },
  });
  await assert.rejects(run([]), /at least one/);
  await assert.rejects(run([...targets, 'b.bend::missing']), /No applicable parsed declaration/);
  await assert.rejects(prepareStyleTargets(['a.bend', 'b.bend'], 'Add one', { ...config, max_units: 2 }, root), /limited to 2/);
  await writeFile(join(root, 'b.bend'), 'def broken( -> U32: 0\n');
  await assert.rejects(run(targets), /does not parse/);
  assert.equal(calls, 0);
  await writeFile(join(root, 'helper.bend'), 'def next( -> U32: 0\n');
  await assert.rejects(run(targets), /context .*does not parse/);
  assert.equal(calls, 0);
});

test('one request carries three style questions, two diagnostics and criticality; receipts enforce only the selected bars', async t => {
  const root = await fixture(t), requests = [], output = [];
  const code = await runStyleRanking(args, { root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x),
    fetchImpl: async (_url, request) => {
      requests.push(JSON.parse(request.body));
      assert.equal(request.headers.authorization, `Bearer ${key}`);
      return requests.length === 1 ? response(5, 1, 'offline-style-fixture', 3, 1) : response(2, 4);
    },
  });
  assert.equal(code, 3, 'completed review with unmet style targets needs attention');
  assert.equal(requests.length, 2);
  for (const request of requests) {
    assert.equal(Object.keys(request.questions).length, 6);
    for (const dimension of [...config.dimensions, ...config.diagnostic_dimensions, config.criticality]) {
      assert.equal(request.questions[dimension.id].type, 'score');
      assert.deepEqual(request.questions[dimension.id].criteria, dimension.levels);
    }
  }
  const report = JSON.parse(output[0]);
  assert.equal(report.status, 'completed');
  assert.equal(report.provider_requests, 2);
  assert.equal(report.provider_responses, 2);
  assert.equal(report.rankings[0].entries[0].target, targets[0]);
  assert.equal(report.rankings[0].entries[0].score, 5);
  assert.equal(report.rankings[0].entries[0].probabilities[5], 1);
  assert.equal(report.rankings[1].entries[0].target, targets[1]);
  assert.equal(report.typechecked, false);
  assert.equal(report.behavioral_equivalence_checked, false);
  assert.equal(report.assessments.length, 8);
  const brain = report.assessments.find(a => a.target === targets[0] && a.dimension === 'maximally_big_brain');
  assert.equal(brain.target_level, 5);
  assert.equal(brain.target_basis, 'criticality');
  assert.equal(brain.probability_at_target, 1);
  assert.equal(brain.status, 'meets_target');
  assert.deepEqual(report.criticality.assessments.map(c => c.status), ['critical', 'noncritical']);
  assert.deepEqual(report.criticality.policy, config.criticality);
  assert.equal(report.style_summary.meets_all, 0);
  assert.equal(report.style_summary.needs_review, 2);
  assert.equal(report.rubric_version, 3);
  assert.equal(report.diagnostics.required_for, 'critical_or_uncertain');
  assert.deepEqual(report.diagnostics.targets, config.criticality.diagnostic_targets);
  assert.equal(report.diagnostics.assessments.length, 4);
  const receipts = await readdir(join(root, '.perch/usage'));
  assert.equal(receipts.length, 1);
  const saved = await readFile(join(root, '.perch/usage', receipts[0]), 'utf8');
  assert.deepEqual(JSON.parse(saved), report);
  assert.ok(!saved.includes(key) && !saved.includes('def solve') && !saved.includes('def next'));
});

test('diagnostic extremes remain advisory for noncritical declarations and remain visible in CLI output', async t => {
  const root = await fixture(t), output = [];
  const code = await runStyleRanking(['--live', '--json', ...targets], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x),
    fetchImpl: async (_url, request) => response(3, 3, 'offline-style-fixture', 3, 0,
      JSON.parse(request.body).state.path === 'a.bend' ? { anticipation: 0, payoff: 4 } : { anticipation: 4, payoff: 0 }),
  });
  const report = JSON.parse(output[0]);
  assert.equal(code, 0);
  assert.equal(report.style_summary.meets_all, 2);
  assert.equal(report.assessments.length, 6);
  assert.equal(report.rankings.length, 3);
  assert.deepEqual(report.diagnostics.assessments.map(a => a.score), [0, 4, 4, 0]);
  assert.ok(report.diagnostics.assessments.every(a => a.status === 'limited_context' && a.unresolved_references > 0));
  assert.ok(report.diagnostics.assessments.every(a => a.advisory && !a.required));
  assert.ok(report.diagnostics.assessments.every(a => !('target_level' in a) && !('probability_at_target' in a)));
  assert.equal(report.rows[0].answers.anticipation.probabilities[0], 1);
  const lines = [];
  assert.equal(await runStyleRanking(['--live', targets[0]], {
    root, env: { PERCH_API_KEY: key }, stdout: x => lines.push(x),
    fetchImpl: async () => response(3, 3, 'offline-style-fixture', 3, 0, { anticipation: 0, payoff: 4 }),
  }), 0);
  assert.match(lines.join('\n'), /Anticipation \(required for critical or uncertain declarations\)/);
  assert.match(lines.join('\n'), /0\.00\/4 \[limited context\]/);
  assert.match(lines.join('\n'), /Payoff \(required for critical or uncertain declarations\)/);
});

test('truncated context skips diagnostic questions and reports unavailable rather than a fabricated low score', async t => {
  const root = await fixture(t), output = [];
  await writeFile(join(root, 'many.bend'), 'import Base\ndef target(x: U32) -> U32: U32.add(x,1)\n'
    + Array.from({ length: 5 }, (_, i) => `def caller${i}(x: U32) -> U32: target(x)\n`).join(''));
  const code = await runStyleRanking(['--live', '--json', 'many.bend::target'], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), fetchImpl: async (_url, request) => {
      const input = JSON.parse(request.body);
      assert.equal(input.state.context_notes.truncated, true);
      assert.equal('anticipation' in input.questions, false);
      assert.equal('payoff' in input.questions, false);
      assert.equal(Object.keys(input.questions).length, 4);
      return response(5, 3);
    },
  });
  const report = JSON.parse(output[0]);
  assert.equal(code, 3, 'truncated context cannot waive mandatory anticipation and payoff');
  assert.equal(report.assessments[0].target_level, 5, 'the existing criticality safeguard still applies');
  assert.equal(report.diagnostics.assessments.length, 2);
  assert.equal(report.style_summary.unavailable, 2);
  assert.equal(report.style_summary.meets_all, 0);
  assert.ok(report.diagnostics.assessments.every(a => a.status === 'unavailable' && a.reason === 'context_truncated' && !('score' in a)));
  assert.equal('anticipation' in report.rows[0].answers, false);
});

test('critical and uncertain declarations need both anticipation and payoff with their own target probability', async t => {
  const root = await fixture(t), output = [];
  const code = await runStyleRanking(['--live', '--json', targets[0]], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x),
    fetchImpl: async () => response(5, 4, 'offline-style-fixture', 4, 0.5, { anticipation: 2, payoff: 4 }),
  });
  const report = JSON.parse(output[0]);
  assert.equal(code, 3);
  assert.equal(report.style_summary.meets_all, 0);
  assert.equal(report.assessments.find(a => a.dimension === 'anticipation').status, 'below_target');
  assert.ok(report.diagnostics.assessments.every(a => a.required && !a.advisory));
  for (const criticality of [0.5, 0.6, 1]) {
    for (const dimension of config.diagnostic_dimensions) {
      for (const [mass, status] of [[0.4, 'below_target'], [0.5, 'uncertain'], [0.6, 'meets_target']]) {
        const answers = (await response(5, 3, 'offline-style-fixture', 3, criticality).json()).answers;
        answers[dimension.id] = { score: 2 + mass, confidence: 0.5, probabilities: { 0: 0, 1: 0, 2: 1 - mass, 3: mass, 4: 0 } };
        const assessments = assessStyle([{ target: 'f', kind: 'bend_definition', context: { truncated: false }, answers }], config);
        const diagnostic = assessments.find(a => a.dimension === dimension.id);
        assert.equal(diagnostic.target_level, 3);
        assert.equal(diagnostic.target_basis, 'criticality');
        assert.equal(diagnostic.status, status);
      }
    }
  }
});

test('invalid diagnostic configurations are rejected before any provider request', async t => {
  const root = await fixture(t);
  for (const diagnostic_dimensions of [null, {}, [{ ...config.diagnostic_dimensions[0], id: 'highly_memetic' }],
    [{ ...config.diagnostic_dimensions[0], id: 'criticality' }],
    [config.diagnostic_dimensions[0], config.diagnostic_dimensions[0]],
    [{ ...config.diagnostic_dimensions[0], levels: ['only one'] }]]) {
    await assert.rejects(prepareStyleTargets(targets, null, { ...config, diagnostic_dimensions }, root), /[Dd]iagnostic/);
  }
  await assert.rejects(prepareStyleTargets(targets, null, { ...config, style_targets: [...config.style_targets,
    { dimension: 'anticipation', level: 3, minimum_probability: 0.6 }] }, root), /Each style dimension/);
});

test('partial transport failure records incomplete coverage, stops requests, and never returns a partial ranking', async t => {
  const root = await fixture(t), output = [], errors = [];
  let calls = 0;
  const code = await runStyleRanking([...args, 'a.bend::unrelated'], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), stderr: x => errors.push(x),
    fetchImpl: async () => {
      if (++calls === 2) throw new Error(`unsafe request details ${key}`);
      return response();
    },
  });
  assert.equal(code, 1);
  assert.equal(calls, 2);
  const report = JSON.parse(output[0]);
  assert.equal(report.status, 'failed');
  assert.equal(report.provider_requests, 2);
  assert.equal(report.provider_responses, 1);
  assert.deepEqual(report.rows, []);
  assert.equal(report.completed_rows.length, 1, 'retain valid answers for explicit reuse after a failure');
  assert.deepEqual(report.rankings, []);
  assert.ok(!JSON.stringify([report, errors]).includes(key));
});

test('a single existing declaration is assessed without a cohort or alternative; all axes must meet the bar', async t => {
  const root = await fixture(t), output = [];
  const code = await runStyleRanking(['--live', '--json', targets[0]], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), fetchImpl: async (_url, request) => {
      const input = JSON.parse(request.body);
      assert.match(input.state.cohort, /No alternative implementation is required/);
      return response(3, 3, 'offline-style-fixture', 3);
    },
  });
  const report = JSON.parse(output[0]);
  assert.equal(code, 0);
  assert.equal(report.provider_requests, 1);
  assert.equal(report.style_summary.meets_all, 1);
  const uncertain = { ...score(3, config.dimensions[1]), score: 2.5, confidence: 0.5, probabilities: { 0: 0, 1: 0, 2: 0.5, 3: 0.5, 4: 0 } };
  const assessment = assessStyle([{ target: 'x', kind: 'bend_definition', answers: { maximally_big_brain: score(4),
    delightful_to_read: uncertain, highly_memetic: score(1, config.dimensions[2]), criticality: criticalityScore(0) } }], config);
  assert.deepEqual(assessment.map(a => a.status), ['meets_target', 'uncertain', 'below_target']);
});

test('all declaration kinds have criticality and mandatory diagnostics; datatypes retain the ordinary big-brain bar', async t => {
  const root = await fixture(t);
  const law = 'law equal:\n  for +n: U32\n  {n == n : U32}\n';
  await writeFile(join(root, 'laws.bend'), `import Base\n${law}`);
  await writeFile(join(root, 'proof.bend'), 'import Base\nimport ./laws.bend as L\ndef L.equal(n): {==}\n');
  await writeFile(join(root, 'combined.bend'), `import Base\n${law}def equal(n): {==}\n`);
  await writeFile(join(root, 'types.bend'), 'import Base\ntype Flag is Data: Off{} On{}\n');
  for (const brain of [4, 5]) {
    const output = [];
    const code = await runStyleRanking(['--live', '--json', targets[0], 'laws.bend', 'proof.bend', 'combined.bend', 'types.bend'], {
      root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), fetchImpl: async (_url, request) => {
        const input = JSON.parse(request.body);
        assert.equal('criticality' in input.questions, true);
        assert.ok(input.state.path.endsWith('.bend'));
        return response(brain, 3, 'offline-style-fixture', 3, 1);
      },
    });
    const report = JSON.parse(output[0]);
    assert.equal(code, brain === 5 ? 0 : 3);
    assert.deepEqual(report.rows.map(r => r.kind), ['bend_definition', 'bend_law', 'bend_law_fill', 'bend_law_definition', 'bend_datatype']);
    assert.deepEqual(report.assessments.filter(a => a.dimension === 'maximally_big_brain').map(a => a.target_level), [5, 5, 5, 5, 3]);
    assert.equal(report.style_summary.meets_all, brain === 5 ? 5 : 1);
    assert.equal(report.rankings.length, 3, 'criticality is not a fourth aesthetic ranking');
    assert.equal(report.criticality.assessments.at(-1).status, 'critical');
    assert.equal(report.assessments.filter(a => a.dimension === 'anticipation').length, 5);
    assert.equal(report.assessments.filter(a => a.dimension === 'payoff').length, 5);
  }
});

test('uncertain or truncated criticality cannot lower the bar; Galaxy brain needs its own probability mass', async () => {
  const base = (await response(4, 3, 'offline-style-fixture', 3).json()).answers;
  const assess = (probability, brain, truncated = false) => assessStyle([{ target: 'a::f', kind: 'bend_definition',
    context: { truncated }, answers: { ...base, maximally_big_brain: brain, criticality: criticalityScore(probability) },
  }], config)[0];
  for (const probability of [0, 0.4]) {
    assert.equal(assess(probability, score(3)).target_level, 3);
    assert.equal(assess(probability, score(3)).status, 'meets_target');
  }
  for (const probability of [0.5, 0.6, 1]) {
    assert.equal(assess(probability, score(4)).target_level, 5);
    assert.equal(assess(probability, score(4)).status, 'below_target');
    assert.equal(assess(probability, score(5)).status, 'meets_target');
  }
  assert.equal(assess(0.5, score(4)).criticality_status, 'uncertain');
  assert.equal(assess(0.6, score(4)).criticality_status, 'critical');
  assert.equal(assess(0, score(4), true).target_level, 5);
  for (const [mass, status] of [[0.4, 'below_target'], [0.5, 'uncertain'], [0.6, 'meets_target']]) {
    const brain = { ...score(5), score: 4 + mass, probabilities: { 0: 0, 1: 0, 2: 0, 3: 0, 4: 1 - mass, 5: mass } };
    assert.equal(assess(1, brain).status, status);
  }
  assert.throws(() => assessStyle([], { ...config, criticality: undefined }), /Criticality needs/);
  assert.throws(() => assessStyle([], { ...config, criticality: { ...config.criticality, style_target: config.style_targets[0] } }), /stricter/);
});

test('whole-project mode covers tracked and new Bend files, reports invalid and empty files, and excludes ignored installs', async t => {
  const root = await fixture(t), output = [];
  execFileSync('git', ['init', '-q'], { cwd: root });
  await writeFile(join(root, '.gitignore'), 'ignored.bend\n');
  await writeFile(join(root, 'ignored.bend'), 'def hidden(): 0\n');
  await writeFile(join(root, 'types.bend'), 'import Base\ntype Flag is Data: Off{} On{}\n');
  await writeFile(join(root, 'empty.bend'), 'import Base\n');
  await writeFile(join(root, 'broken.bend'), 'def broken( -> U32: 0\n');
  execFileSync('git', ['add', 'a.bend'], { cwd: root });
  const code = await runStyleRanking(['--live', '--all', '--json', '--jobs=2'], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), stderr: () => {},
    fetchImpl: async () => response(3, 3),
  });
  const report = JSON.parse(output[0]);
  assert.equal(code, 1, 'an unreadable file must not masquerade as full coverage');
  assert.equal(report.status, 'incomplete');
  assert.equal(report.coverage.ranked, 5);
  assert.equal(report.provider_requests, 5);
  const datatype = report.rows.find(r => r.target === 'types.bend::Flag');
  assert.equal(datatype.kind, 'bend_datatype');
  assert.equal(datatype.context.files[0].path, 'types.bend');
  assert.deepEqual(report.inventory.unranked.map(f => f.path), ['broken.bend']);
  assert.deepEqual(report.inventory.empty_files, ['empty.bend']);
  assert.ok(!report.inventory.discovered_files.includes('ignored.bend'));
  assert.equal(report.rankings.length, 3);
});

test('explicit reuse avoids paid repeats and invalidates when helper context changes', async t => {
  const root = await fixture(t);
  const run = (extra, output) => runStyleRanking(['--live', '--json', targets[0], ...extra], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), fetchImpl: async () => response(3, 3),
  });
  const first = [];
  assert.equal(await run(['--output=first.json.gz'], first), 0);
  const second = [];
  assert.equal(await run(['--reuse=first.json.gz'], second), 0);
  assert.equal(JSON.parse(second[0]).provider_requests, 0);
  assert.equal(JSON.parse(second[0]).reused_units, 1);
  const damaged = JSON.parse(first[0]);
  delete damaged.rows[0].answers.criticality;
  await writeFile(join(root, 'missing-criticality.json'), JSON.stringify(damaged));
  await assert.rejects(run(['--reuse=missing-criticality.json'], []), /Invalid Score answer/);
  const missingDiagnostic = JSON.parse(first[0]);
  delete missingDiagnostic.rows[0].answers.anticipation;
  await writeFile(join(root, 'missing-diagnostic.json'), JSON.stringify(missingDiagnostic));
  await assert.rejects(run(['--reuse=missing-diagnostic.json'], []), /Invalid Score answer/);
  await writeFile(join(root, 'helper.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,2)\n');
  const third = [];
  assert.equal(await run(['--reuse=first.json.gz'], third), 0);
  assert.equal(JSON.parse(third[0]).provider_requests, 1);
  assert.equal(JSON.parse(third[0]).reused_units, 0);
  const revised = structuredClone(config);
  revised.diagnostic_dimensions[0].instructions += ' Revised context.';
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(revised));
  await assert.rejects(run(['--reuse=first.json.gz'], []), /same rubric/);
});

test('concurrent responses preserve target attribution and changes during review are disclosed', async t => {
  const root = await fixture(t), output = [];
  const code = await runStyleRanking(['--live', '--json', '--jobs=2', ...targets], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), stderr: () => {},
    fetchImpl: async (_url, request) => {
      const input = JSON.parse(request.body);
      if (input.state.source.includes('H.next')) {
        await new Promise(resolve => setTimeout(resolve, 20));
        await writeFile(join(root, 'helper.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,2)\n');
        return response(4, 3);
      }
      return response(3, 4);
    },
  });
  const report = JSON.parse(output[0]);
  assert.equal(code, 3, 'changed working copy needs attention even if recorded snapshot met targets');
  assert.deepEqual(report.source_freshness.changed_sources, ['helper.bend']);
  assert.deepEqual(report.rows.map(r => r.target), targets);
  assert.equal(report.rows[0].answers.maximally_big_brain.score, 4);
  assert.equal(report.rows[1].answers.delightful_to_read.score, 4);
});

test('missing credentials, unauthorized responses, malformed scores and model drift cannot produce rankings', async t => {
  const root = await fixture(t);
  const invalid = response();
  invalid.json = async () => ({ model: 'offline', answers: { maximally_big_brain: score(4) } });
  for (const mode of ['missing-key', 'unauthorized', 'invalid-answer', 'missing-criticality', 'missing-diagnostic', 'invalid-diagnostic', 'model-drift']) {
    let calls = 0;
    const output = [];
    const code = await runStyleRanking(args, {
      root, env: mode === 'missing-key' ? {} : { PERCH_API_KEY: key }, stdout: x => output.push(x), stderr: () => {},
      fetchImpl: async () => {
        calls++;
        if (mode === 'unauthorized') return { ok: false, status: 401 };
        if (mode === 'invalid-answer') return invalid;
        if (mode === 'missing-criticality') {
          const body = await response(5, 3).json();
          delete body.answers.criticality;
          return { ok: true, json: async () => body };
        }
        if (mode === 'missing-diagnostic' || mode === 'invalid-diagnostic') {
          const body = await response(5, 3).json();
          if (mode === 'missing-diagnostic') delete body.answers.payoff;
          else body.answers.payoff.score = 99;
          return { ok: true, json: async () => body };
        }
        return response(3, 2, `offline-${calls}`);
      },
    });
    const report = JSON.parse(output[0]);
    assert.equal(code, 1, mode);
    assert.equal(report.status, 'failed', mode);
    assert.deepEqual(report.rankings, [], mode);
    assert.equal(calls, mode === 'missing-key' ? 0 : mode === 'model-drift' ? 2 : 1, mode);
  }
  assert.throws(() => validateScore({ ...score(4), score: 1 }, config.dimensions[0].levels.length), /Inconsistent/);
  assert.throws(() => validateScore({ ...score(4), probabilities: { 4: 1 } }, config.dimensions[0].levels.length), /Incomplete/);
});

test('ties share a rank, near ties remain visible, and existing output is rejected before requests', async t => {
  const root = await fixture(t);
  const rows = [4, 4, 3.8, 2].map((value, i) => ({ target: String(i), answers: { taste: { score: value } } }));
  const ranked = rankRows(rows, [{ id: 'taste' }], 0.25)[0].entries;
  assert.deepEqual(ranked.map(row => row.rank), [1, 1, 3, 4]);
  assert.deepEqual(ranked.map(row => row.near_tie_above), [false, true, true, false]);
  await writeFile(join(root, 'old.json'), 'old evidence');
  let calls = 0;
  await assert.rejects(runStyleRanking([...args, '--output=old.json'], { root,
    fetchImpl: async () => { calls++; return response(); },
  }), /already exists/);
  assert.equal(calls, 0);
  assert.equal(await readFile(join(root, 'old.json'), 'utf8'), 'old evidence');
});
