// Applied only after the installer's exact upstream checksum and Bend patch.
export function patchThroughput(source) {
  const replace = (before, after) => {
    if (source.split(before).length !== 2) throw new Error(`Perch throughput anchor changed: ${before.slice(0, 80)}`);
    source = source.replace(before, after);
  };
  replace('var DEFAULT_PARALLEL = 8;', 'var DEFAULT_PARALLEL = knotDefaultJobs;');
  replace('  retryDelayMs = 2e3,', '  concurrency = knotDefaultJobs,\n  retryDelayMs = 2e3,');
  replace('  let authenticationFailure = null, firstRequest = null;',
    '  let authenticationFailure = null, firstRequest = null;\n  const limitedRequest = knotLimitConcurrent(request, concurrency);');
  replace('    const pending = request(body, attempted, beforeRequest);',
    '    const pending = limitedRequest(body, attempted, beforeRequest);');
  const client = 'model: io.env.PERCH_MODEL_ID, log:';
  if (source.split(client).length !== 3) throw new Error('Perch provider client anchors changed');
  source = source.replaceAll(client, 'model: io.env.PERCH_MODEL_ID, concurrency: knotConcurrency(io.flags.parallel ?? io.env.PERCH_JOBS), log:');
  replace('function textTokens(text3) {', 'function knotUncachedTextTokens(text3) {');
  replace('var estimateTokens = (value2) => textTokens(JSON.stringify(value2));',
    'var textTokens = knotMemoizeTextCount(knotUncachedTextTokens);\nvar estimateTokens = (value2) => textTokens(JSON.stringify(value2));');
  replace('parallel: ["--parallel N", `How many methods to read at once (default ${DEFAULT_PARALLEL}; files and tests go ${UNIT_PARALLEL} at a time)`, ["scan"]]',
    'parallel: ["--parallel N", `Concurrent scan/check units, 1..256 (default ${DEFAULT_PARALLEL}; PERCH_JOBS overrides)`, ["scan", "check"]]');
  replace('const parallel = positiveInteger("--parallel", io.flags.parallel, DEFAULT_PARALLEL);',
    'const parallel = knotConcurrency(io.flags.parallel ?? io.env.PERCH_JOBS);');
  replace('      paths,\n        parallel,', '      paths,\n        parallel,\n        unitParallel: parallel,');
  replace('      revision: await revision(root),\n      only,',
    '      revision: await revision(root),\n      parallel: knotConcurrency(io.flags.parallel ?? io.env.PERCH_JOBS),\n      only,');

  // The snapshot belongs to a single check, so subsequent commands see edits.
  replace('only = [], knotUnit = null, knotReview = null, knotFileOnly = false, debug',
    'only = [], parallel = DEFAULT_PARALLEL, knotRules = null, knotUnit = null, knotReview = null, knotFileOnly = false, debug');
  replace('  systemOne = requestScope(systemOne);\n  const unit = knotUnit', '  const unit = knotUnit');
  replace('    const configured = await readRules(root, revision2);',
    '    const configured = knotRules ?? await readRules(root, revision2);');
  replace('    const units = [];\n    for (const candidate of selected) units.push(await checkTarget({ target, root, out, analyzer, systemOne,\n      revision: revision2, only, debug, knotUnit: candidate, knotReview: review }));',
    '    const units = await knotMapConcurrent(selected, parallel, candidate => checkTarget({ target, root, out, analyzer, systemOne,\n      revision: revision2, only, parallel, knotRules: configured, debug, knotUnit: candidate, knotReview: review }));');
  replace('only: fileRules.map(rule => rule.name), debug, knotUnit: unit, knotFileOnly: true',
    'only: fileRules.map(rule => rule.name), parallel, knotRules: configured, debug, knotUnit: unit, knotFileOnly: true');
  replace('  const bendReview = unit.bend && unit.part',
    '  systemOne = requestScope(systemOne);\n  const bendReview = unit.bend && unit.part');
  replace('rulesFor(await readRules(root, revision2), unit, named2.rules)',
    'rulesFor(knotRules ?? await readRules(root, revision2), unit, named2.rules)');
  replace('const asked = (await Promise.all([...contexts].map',
    'const asked = (await knotDrainAll([...contexts].map');
  replace('const results2 = await Promise.all(over.map', 'const results2 = await knotDrainAll(over.map');
  replace('  await Promise.all(running.map(async ({ rule, units, id, key }) => {',
    '  await knotDrainAll(running.map(async ({ rule, units, id, key }) => {');
  replace('      const here = await Promise.all(batch.map(async (unit) => {',
    '      const here = await knotDrainAll(batch.map(async (unit) => {');

  // Singleflight the immutable Git source, including concurrent caller reads.
  replace('      sources.set(node.path, (await readBlob(root, file.blob)).split("\\n"));',
    '      sources.set(node.path, readBlob(root, file.blob).then(text => text.split("\\n")).catch(error => { sources.delete(node.path); throw error; }));');
  replace('          for (const key of RUN_ROWS) lengths[key] = run[key].length;',
    '          for (const key of RUN_ROWS) lengths[key] += batch[key].length;');
  replace('        const batch = Object.fromEntries(RUN_ROWS.map((key) => [key, run[key].slice(lengths[key])]));',
    '        const { visited, broken, failed, ...header } = run;\n        const savedHeader = structuredClone(header);\n        const batch = Object.fromEntries(RUN_ROWS.map((key) => [key, run[key].slice(lengths[key])]));');
  replace('        const { visited, broken, failed, ...header } = run;\n        await writeJson(path, { ...header, journal_bytes: bytes });',
    '        await writeJson(path, { ...savedHeader, journal_bytes: bytes });');
  // Preserve the entire file/context universe: directory fallback can depend
  // on entries that do not themselves match a rule. Only the IO is batched.
  replace('      for (const item of tree) if (eligible(item) && !files.has(item.path)) files.set(item.path, await readBlob(root, item.sha).catch(() => ""));',
    `      const unread = tree.filter(item => eligible(item) && !files.has(item.path));
      if (unread.length) await readBlobs(root, unread.map(item => item.sha),
        (index, text) => files.set(unread[index].path, text)).catch(async () => {
          for (const item of unread) if (!files.has(item.path)) files.set(item.path, await readBlob(root, item.sha).catch(() => ""));
        });`);

  // A refillable pool avoids waiting for the slowest request in every batch.
  // Recording is synchronous apart from its resolved async return. Journal
  // checkpoints are serialized and drained before finalization, even on error.
  const start = source.indexOf('    for (; ; ) {\n      const batch = [];\n      while (batch.length < parallel)');
  const end = source.indexOf('    const files = /* @__PURE__ */ new Map();', start);
  if (start < 0 || end < 0) throw new Error('Perch scan worker anchors changed');
  source = source.slice(0, start) + `    let completed = 0, admitted = 0, lastSave = performance.now(), saveFailure;
    const failureCohorts = knotFailureCohorts(parallel);
    let saving = Promise.resolve();
    try {
      await knotRunWorkers(parallel, () => {
        if (saveFailure) throw saveFailure;
        const nodeId = walk.next();
        if (!nodeId) return undefined;
        walk.visited.add(nodeId);
        return { nodeId, index: admitted++ };
      }, async ({ nodeId, index }) => {
        let result;
        try { result = await ask(nodeId); }
        catch (error) {
          if (error instanceof AuthenticationError) throw error;
          const node = graph.nodes.get(nodeId);
          log(node.qualified_name + " in " + node.path + ": " + error.message);
          result = { failed: { method: nodeId, id: findingId(nodeId), path: node.path, name: node.qualified_name, line: node.line, status: "failed", error: error.message, incomplete: error instanceof IncompleteCheckError } };
        }
        if (result.failed) {
          const failed = result.failed;
          run.failed.push(failed); run.visited.push(failed);
          missing.set(failed.path, (missing.get(failed.path) ?? 0) + 1);
          finish(failed.path, null);
        } else { await record([result]); }
        progress(++completed, total);
        if (failureCohorts(index, Boolean(result.failed))) throw new Error("Two consecutive cohorts could not be read");
        if (performance.now() - lastSave >= 1000) {
          lastSave = performance.now();
          saving = saving.then(() => saveRun()).catch(error => { saveFailure ??= error; });
        }
      });
    } finally { await saving; }
    if (saveFailure) throw saveFailure;
    await saveRun();
` + source.slice(end);

  // File rules also refill as soon as a unit finishes, while results retain
  // their original sorted order. Search batches retain their stop semantics.
  const fileStart = source.indexOf('  for (let at = 0; at < work.length; at += parallel) {');
  const fileEnd = source.indexOf('  return { results, asked, carried };', fileStart);
  if (fileStart < 0 || fileEnd < 0) throw new Error('Perch file worker anchors changed');
  source = source.slice(0, fileStart) + `  let completed = 0;
  const answered = await knotMapConcurrent(work, parallel, async item => {
    try { return await askOne(item); }
    catch (error) {
      if (error instanceof AuthenticationError) throw error;
      return { results: item.rules.map(rule => failedCheck(rule, item.unit, error, revision2)), carried: 0 };
    } finally { progress(completed += item.rules.length, total); }
  });
  for (const [index, item] of work.entries()) {
    asked += item.rules.length;
    carried += answered[index].carried;
    results.push(...answered[index].results);
  }
` + source.slice(fileEnd);

  // Incremental scans validate the current whole selection. --since remains
  // an explicitly narrower path filter, never an incremental completeness gate.
  replace('var switches = /* @__PURE__ */ new Set(["force",',
    'var switches = /* @__PURE__ */ new Set(["incremental", "fresh", "force",');
  replace('  since: ["--since REF", "Only what changed since this branch or commit", ["scan"]],',
    '  since: ["--since REF", "Only what changed since this branch or commit", ["scan"]],\n  incremental: ["--incremental", "Validate current contexts and reuse identical prior answers", ["scan"]],\n  fresh: ["--fresh", "Ask again without reusing answers; retain parser caches and closures", ["scan"]],');
  replace('function checkFlags(flags, commandName) {', `function checkFlags(flags, commandName) {
  if ((flags.incremental && flags.fresh) || (flags.since && (flags.incremental || flags.fresh)))
    throw new UsageError("--incremental, --fresh and --since are mutually exclusive");`);
  replace('Delete .perch/scan.jsonl to ask about everything again.',
    'Use --incremental to make this reuse explicit, or --fresh to ask again without deleting the prior cache. Both validate the current selected graph; neither combines with --since. Cached answers retain their recorded resolved model; pin PERCH_MODEL_ID or use --fresh when a moving model alias changes.');
  replace('The answer would be the same one, and asking for it would move the numbers on an issue you have already looked at.',
    'Reuse preserves previously recorded evidence; a fresh stochastic answer may differ.');
  replace('--paths and --since narrow it further, and --since origin/main is what CI wants.',
    '--paths and --since narrow it further. These explicit path filters do not establish whole-repository coverage.');
  replace('  unitParallel = UNIT_PARALLEL,\n  min = 0.5,',
    '  unitParallel = UNIT_PARALLEL,\n  fresh = false,\n  min = 0.5,');
  replace('        unitParallel: parallel,\n        min,',
    '        unitParallel: parallel,\n        fresh: Boolean(io.flags.fresh),\n        min,');
  replace('    paths,\n    parallel,\n    scan_id: scan.id,',
    '    paths,\n    parallel,\n    mode: fresh ? "fresh" : "incremental",\n    parser_coverage: scan.coverage,\n    scan_id: scan.id,');
  replace('{ run, parser_coverage: scan.coverage, issues: issues2, usage: meter.toJSON() },',
    '{ run, parser_coverage: run.parser_coverage, issues: issues2, usage: meter.toJSON() },');
  replace('  const earlier = latest;', '  const earlier = fresh ? new Map() : latest;');
  replace('systemOne, inScope, min, debug, earlier: checks };',
    'systemOne, inScope, min, debug, earlier: fresh ? new Map() : checks };');
  replace('    checked: 0,\n    visited: [],', '    checked: 0,\n    reviewed_checks: 0,\n    visited: [],');
  replace('  const read = [], broken = [];', '  const read = [], broken = [], reviewed = new Map();');
  replace('      const event = before ? { ...before, ...fresh } : fresh;\n      read.push(event);',
    `      const event = before ? { ...before, ...fresh } : fresh;
      const answeredNames = new Set(questionsFor([...methodQuestions(kinds), ...rulesForMethod(rules, node)], filters, label)
        .filter(question => event[question.name] !== undefined).map(question => question.name));
      for (const name of answeredNames) reviewed.set(name, (reviewed.get(name) ?? 0) + 1);
      run.reviewed_checks += answeredNames.size;
      read.push(event);`);
  replace('    run.carried += units.carried + searches.carried;',
    `    run.carried += units.carried + searches.carried;
    for (const result of [...units.results, ...searches.results]) {
      if (result.error || result.incomplete || typeof result.broken !== "number") continue;
      reviewed.set(result.rule, (reviewed.get(result.rule) ?? 0) + 1);
      run.reviewed_checks++;
    }`);
  replace('...questionSet().filter((question) => question.each === "method" && !question.kind).map((question) => ({',
    '...questionSet().filter((question) => question.each === "method" && !question.kind && reviewed.has(question.name)).map((question) => ({');
  replace('        units: read.length,', '        units: reviewed.get(question.name),');
  replace('      ...rules.map((rule) => ({\n        name: rule.name,\n        from: RULES_FILE,',
    '      ...rules.filter(rule => reviewed.has(rule.name)).map((rule) => ({\n        name: rule.name,\n        from: RULES_FILE,');
  replace('        units: rule.each === "method" && !SEARCHES(rule.kind) ? candidates.filter((candidate) => rulesForMethod([rule], graph.nodes.get(candidate.id)).length).length : selectUnits(rule, { scan, graph, files, tree, inScope }).length,',
    '        units: reviewed.get(rule.name),');

  // Names and compiled questions are part of the request. The old unnamed
  // hash list could carry A's answer after an otherwise identical rename to B.
  replace('var askKey = (steps, asked, client) => sha(JSON.stringify([steps.map((step) => step.state), asked.map((question) => question.hash).sort(), client]));',
    `var askKey = (steps, asked, client) => sha(JSON.stringify(["knot-request-v2",
  steps.map(step => [step.state, step.questions ?? null]),
  asked.map(question => [question.name, question.hash, question.kind, question.type,
    question.when, question.issue, question.min, question.gate]).sort((a, b) => a[0].localeCompare(b[0])), client]));`);
  replace('const key = askKey(steps, over, systemOne.cacheKey ?? systemOne.id);',
    'const key = askKey(steps, over, [systemOne.cacheKey ?? systemOne.id, min]);');
  replace('    const key = rule.sees === "self" ? askKey([{ state: units.map((unit) => [unit.id, unit.hash ?? null]) }], [rule], systemOne.cacheKey ?? systemOne.id) : null;',
    `    let key = null;
    try {
      const inputs = units.map(unit => {
        const source = files.get(unit.path) ?? "";
        const steps = unitSteps({ rules: [rule], unit, source: unit.part ? bodyOf(source, unit) : source,
          seen: neighbourhood(rule.sees, unit, { graph, files }), budget: systemOne.limits?.state });
        return [unit.id, askKey(steps, [rule], systemOne.cacheKey ?? systemOne.id)];
      });
      key = sha(JSON.stringify(["knot-search-v2", rule.name, rule.kind, min, inputs]));
    } catch { /* Preserve per-unit incomplete reporting when context preparation fails. */ }`);
  replace('    if (!units.length) return;\n    let settled = null;',
    `    if (!units.length) {
      const unit = { id: "search:" + rule.name, path: RULES_FILE, name: String(rule.where), line: 1 };
      results.push({ ...checkOf(rule, unit, { broken: rule.kind === "ensure_present" ? 1 : 0,
        line: 1, text: null, revision: revision2, key }), id });
      return;
    }
    let settled = null;`);
  replace('const elsewhere = [...earlier.values()].filter((event) => !walked.has(event.method) && graph.nodes.has(event.method));',
    'const elsewhere = [...latest.values()].filter(event => !walk.visited.has(event.method) && graph.nodes.has(event.method) && !graph.nodes.get(event.method).test && !ignored.some(glob => matches(glob, event.path)));');
  replace('    const unasked = [...checks.values()].filter((check2) => !said.has(check2.id) && byName.get(check2.rule)?.hash === check2.rule_hash);',
    `    const liveUnits = new Map(rules.filter(rule => !SEARCHES(rule.kind)).map(rule => [rule.name,
      new Set(selectUnits(rule, { scan, graph, files, tree,
        inScope: path => !ignored.some(glob => matches(glob, path)) }).map(unit => unit.id))]));
    const unasked = [...checks.values()].filter(check => !said.has(check.id)
      && byName.get(check.rule)?.hash === check.rule_hash
      && (SEARCHES(byName.get(check.rule)?.kind) ? true : liveUnits.get(check.rule)?.has(check.unit)));`);

  // Parser output is content-addressed, while path IDs, graph resolution and
  // coverage are rebuilt from the current tree. Cache files are disposable.
  replace('async function analyzeTree({ root, revision: revision2, out, analyzer,', `import { randomUUID as knotParseNonce } from "node:crypto";
export function knotCachedAnalyzer(analyzer, out, stats) {
  const pending = new Map();
  return { async analyzeSource(source, language) {
    const key = identity("knot-parse-v1", ANALYSIS_PROFILE, language, sha256(source));
    if (pending.has(key)) { stats.hits++; return pending.get(key); }
    const reading = (async () => {
      const path = join3(out, "analysis", key + ".json");
      const cached = await readJson(path, null).catch(() => null);
      if (cached?.schema === 1 && cached.key === key && cached.analysis
          && ["parsed", "parse-error"].includes(cached.analysis.parser_status)
          && cached.digest === sha256(JSON.stringify(cached.analysis))) {
        stats.hits++;
        return cached.analysis;
      }
      stats.misses++;
      const analysis = await analyzer.analyzeSource(source, language);
      if (["parsed", "parse-error"].includes(analysis.parser_status)) {
        const temporary = path + "." + process.pid + "." + knotParseNonce() + ".tmp";
        try {
          await mkdir(dirname2(path), { recursive: true });
          await writeFile(temporary, JSON.stringify({ schema: 1, key, digest: sha256(JSON.stringify(analysis)), analysis }));
          await rename(temporary, path);
        } catch { stats.write_failures++; await rm(temporary, { force: true }).catch(() => {}); }
      }
      return analysis;
    })();
    pending.set(key, reading);
    return reading;
  } };
}
async function analyzeTree({ root, revision: revision2, out, analyzer,`);
  replace('  if (existing?.status === "complete") {',
    '  if (existing?.status === "complete" && !existing.coverage?.transient_parse_failures) {');
  replace('    return existing;\n  }\n  await store.exclude(root);',
    '    return { ...existing, coverage: { ...existing.coverage, parser_cache: { hits: 0, misses: 0, write_failures: 0, revision_reused: true } } };\n  }\n  await store.exclude(root);');
  replace('  const analysis = await analyzeFiles(sources, { analyzer, readSource, progress, debug });',
    '  const parserCache = { hits: 0, misses: 0, write_failures: 0, revision_reused: false };\n  const analysis = await analyzeFiles(sources, { analyzer: knotCachedAnalyzer(analyzer, out, parserCache), readSource, progress, debug });');
  replace('coverage: { ...analysis.coverage, excluded: tree.filter((item) => item.type === "blob").length - sources.length },',
    'coverage: { ...analysis.coverage, parser_cache: parserCache, excluded: tree.filter((item) => item.type === "blob").length - sources.length },');
  replace('    if (analysis.parser_status !== "parsed") {\n      coverage.parse_failures++;',
    '    if (analysis.parser_status !== "parsed") {\n      coverage.parse_failures++;\n      if (analysis.parser_status !== "parse-error") coverage.transient_parse_failures = (coverage.transient_parse_failures ?? 0) + 1;');

  return source;
}
