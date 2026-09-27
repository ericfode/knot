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

  return source;
}
