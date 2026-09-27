#!/usr/bin/env node
// Apply a reproducible local adapter to the exact pinned upstream bundle.
import { createHash } from 'node:crypto';
import { readFile, writeFile, rename, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { patchThroughput } from './perch-throughput-patch.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const bundle = join(root, 'node_modules/@lakeday/perch/dist/cli.mjs');
const backup = `${bundle}.upstream`;
const expected = '4dad0bcc84fd77d6ee6ceab59ff1caabdb9daa867a575600618965fa063b5e27';
const sha = data => createHash('sha256').update(data).digest('hex');
const marker = '// Knot Bend parser integration v1';

function replaceOnce(source, before, after) {
  if (source.split(before).length !== 2) throw new Error(`Perch patch anchor changed: ${before.slice(0, 70)}`);
  return source.replace(before, after);
}

export function patchPerch(source, profile) {
  let patched = replaceOnce(source, 'var languages = {\n', 'var languages = {\n  bend: "bend",\n');
  patched = replaceOnce(patched, 'var ANALYSIS_PROFILE = "language-pack-1.20-v3";',
    `var ANALYSIS_PROFILE = ${JSON.stringify(profile)};`);
  patched = replaceOnce(patched, 'function createSourceAnalyzer() {\n  return createAnalyzer();\n}', `function createSourceAnalyzer() {
  const other = createAnalyzer();
  return {
    analyzeSource(source, language) {
      return language === "bend" ? knotAnalyzeBendSource(source) : other.analyzeSource(source, language);
    },
    async analyzeSummary(source, language) {
      if (language !== "bend") return other.analyzeSummary(source, language);
      const { declarations, references, ...summary } = await knotAnalyzeBendSource(source);
      return { ...summary, declaration_count: declarations.length };
    }
  };
}`);
  // A file check normally skips parsing upstream. Bend checks must validate
  // syntax as well as selecting rules, so malformed source never reaches Jev.
  const fileReturn = '  if (!name) return { path, name: path, line: 1, text: text3, lines: text3.split("\\n") };';
  patched = replaceOnce(patched, fileReturn, `  const bend = languageOf(path) === "bend" ? await analyzer.analyzeSource(text3, "bend") : null;
  if (bend && bend.parser_status !== "parsed") throw new Error(path + " does not parse: " + (bend.parser_message ?? "syntax error"));
  const parser = bend ? { profile: ${JSON.stringify(profile)}, status: bend.parser_status, declarations: bend.declarations.length, diagnostics: bend.diagnostics, metadata: bend.parser_metadata ?? null } : null;
  if (!name) return { path, name: path, line: 1, text: text3, lines: text3.split("\\n"), parser, bend };`);
  patched = replaceOnce(patched,
    '  const analysis = await analyzer.analyzeSource(text3, language);',
    '  const analysis = bend ?? await analyzer.analyzeSource(text3, language);');
  patched = replaceOnce(patched,
    'return { path, name: found.qualified_name, line: found.line, end_line: found.end_line, metrics: found.metrics, part: true, text: text3, lines: text3.split("\\n") };',
    'return { path, name: found.qualified_name, line: found.line, end_line: found.end_line, metrics: found.metrics, part: true, text: text3, lines: text3.split("\\n"), parser, bend, declaration: found };');
  // Upstream check(file) selects only file rules, and custom check(method)
  // supplies an empty graph. Bend checks fan out over parsed declarations and
  // use an explicit working-tree context snapshot for both custom and built-in
  // questions. Scans retain their committed-revision semantics.
  patched = replaceOnce(patched,
    'async function checkTarget({ target, root, out, analyzer, systemOne, revision: revision2, only = [], debug = () => {',
    'async function checkTarget({ target, root, out, analyzer, systemOne, revision: revision2, only = [], knotUnit = null, knotReview = null, knotFileOnly = false, debug = () => {');
  patched = replaceOnce(patched,
    '  const unit = await resolveTarget2({ target, root, out, analyzer });\n  const named2 = splitOnly(only);',
    `  const unit = knotUnit ?? await resolveTarget2({ target, root, out, analyzer });
  const named2 = splitOnly(only);
  if (unit.bend && !unit.part && !knotFileOnly) {
    const configured = await readRules(root, revision2);
    const candidates = unit.bend.declarations.map(declaration => ({ ...unit, declaration,
      name: declaration.qualified_name, line: declaration.line, end_line: declaration.end_line,
      metrics: declaration.metrics, part: true }));
    const selected = candidates.filter(candidate => !only.length || named2.types.length || rulesFor(configured, candidate, named2.rules).length);
    const review = selected.length ? await knotCreateBendReview({ root, path: unit.path, source: unit.text, analysis: unit.bend }) : null;
    // Preflight every selected context before the first provider request. A
    // syntax failure in an explicitly referenced local helper fails the check.
    for (const candidate of selected) await review.forUnit(candidate.name);
    const units = [];
    for (const candidate of selected) units.push(await checkTarget({ target, root, out, analyzer, systemOne,
      revision: revision2, only, debug, knotUnit: candidate, knotReview: review }));
    const fileRules = only.length && !named2.rules.length ? [] : rulesFor(configured, unit, named2.rules);
    if (fileRules.length) units.push(await checkTarget({ target, root, out, analyzer, systemOne,
      revision: revision2, only: fileRules.map(rule => rule.name), debug, knotUnit: unit, knotFileOnly: true }));
    const located = (items, member) => (items ?? []).map(item => ({ ...item, name: member.name, line: member.line, end_line: member.end_line }));
    const broken = units.flatMap(member => located(member.broken, member));
    const issues = units.flatMap(member => located(member.issues, member));
    return { path: unit.path, name: unit.path, line: 1, parser: unit.parser,
      checked: units.reduce((sum, member) => sum + member.checked, 0), units,
      broken, issues, note: null, clean: units.every(member => member.clean) };
  }
  const bendReview = unit.bend && unit.part
    ? await (knotReview ?? await knotCreateBendReview({ root, path: unit.path, source: unit.text, analysis: unit.bend })).forUnit(unit.name) : null;`);
  patched = replaceOnce(patched,
    '  const body = unit.part ? bodyOf(unit.text, unit) : unit.text;',
    '  const body = unit.bend && unit.part ? knotBendDeclarationSource(unit.text, unit.declaration) : unit.part ? bodyOf(unit.text, unit) : unit.text;');
  patched = replaceOnce(patched,
    'seen: neighbourhood(sees, unit, { graph: EMPTY_GRAPH, files: /* @__PURE__ */ new Map([[unit.path, unit.text]]) })',
    'seen: bendReview?.seen ?? neighbourhood(sees, unit, { graph: EMPTY_GRAPH, files: /* @__PURE__ */ new Map([[unit.path, unit.text]]) })');
  patched = replaceOnce(patched,
    'function neighbourhood(sees, unit, { graph, files, max = MAX_SEEN }) {\n  if (!sees || sees === "self") return {};',
    'function neighbourhood(sees, unit, { graph, files, max = MAX_SEEN }) {\n  if (unit.part && languageOf(unit.path) === "bend" && (!sees || sees === "self")) sees = "neighbors";\n  if (!sees || sees === "self") return {};');
  patched = replaceOnce(patched,
    '    const context = await methodContext({ finding: { method: `${unit.path}::${unit.name}`, path: unit.path, revision: revision2 }, root, out, analyzer, revision: revision2, log: debug }).catch((error) => {',
    '    const context = bendReview?.builtin ?? await methodContext({ finding: { method: `${unit.path}::${unit.name}`, path: unit.path, revision: revision2 }, root, out, analyzer, revision: revision2, log: debug }).catch((error) => {');
  // The law text has already passed the shared Bend context budget. Carry that
  // same selection into every built-in chunk and token retry, inside build()
  // so it cannot bypass the upstream request budget or disappear under pressure.
  patched = replaceOnce(patched,
    'callees: context.callees, callers: context.callers, budget });',
    'callees: context.callees, callers: context.callers, knotPairedLawContext: context.paired_law_context, budget });');
  patched = replaceOnce(patched,
    'function methodStep({ node, lines, imports = [], methods = [node], moduleScopeText = moduleScope(lines, methods),',
    'function methodStep({ node, lines, imports = [], methods = [node], knotPairedLawContext = null, moduleScopeText = moduleScope(lines, [...methods, ...(knotPairedLawContext?.laws ?? []).filter(law => law.path === node.path)]),');
  patched = replaceOnce(patched,
    '    call_graph: fewerCallees || fewerCallers ? edges : []\n  });',
    '    call_graph: fewerCallees || fewerCallers ? edges : [],\n    ...(knotPairedLawContext ?? {})\n  });');
  // Local paired laws also occur outside def ranges in module scope. Suppress
  // only that duplicate rendering; these are not additional method/graph nodes.
  patched = replaceOnce(patched,
    '  const moduleScopeText = moduleScope(lines, methods);',
    '  const moduleScopeText = moduleScope(lines, [...methods, ...(options2.knotPairedLawContext?.laws ?? []).filter(law => law.path === node.path)]);');
  patched = replaceOnce(patched, '    checked: rules.length + (issues2 ? 1 : 0),',
    '    parser: unit.parser ?? null,\n    end_line: unit.end_line ?? null,\n    asked,\n    context: bendReview?.provenance ?? null,\n    checked: rules.length + (issues2 ? 1 : 0),');
  patched = replaceOnce(patched, '      { run, issues: issues2, usage: meter.toJSON() },',
    '      { run, parser_coverage: scan.coverage, issues: issues2, usage: meter.toJSON() },');
  // Resolve only explicit paths present in the scanned revision. Base, remote
  // content hashes and other imports stay unresolved; analysis never fetches.
  patched = replaceOnce(patched,
    '  if (language === "python") return resolvePython(fromPath, module, paths);',
    `  if (language === "bend") {
    if (!module.startsWith("./") && !module.startsWith("../")) return null;
    const candidate = normalize(posix.join(dirname3(fromPath), module));
    return candidate.endsWith(".bend") && paths.has(candidate) ? candidate : null;
  }
  if (language === "python") return resolvePython(fromPath, module, paths);`);
  patched = replaceOnce(patched, '  const resolve3 = (file, name) => {', `  const resolve3 = (file, name) => {
    if (file.language === "bend") {
      const local = lookup(file.path, name);
      if (local) return local;
      const dot = name.indexOf(".");
      if (dot < 0) return null;
      const imported = file.imports.find(item => item.alias === name.slice(0, dot));
      if (!imported) return null;
      const target = resolveModule(file.path, imported.module, "bend", paths);
      return target ? lookup(target, name.slice(dot + 1)) : null;
    }`);
  patched = replaceOnce(patched,
    'resolve3(file, value2.name) ?? unique.get(value2.name.split(/::|\\./).at(-1)) ?? null',
    'resolve3(file, value2.name) ?? (file.language === "bend" ? null : unique.get(value2.name.split(/::|\\./).at(-1))) ?? null');
  patched = patchThroughput(patched);
  return `${marker}\nimport { DEFAULT_PERCH_JOBS as knotDefaultJobs, perchConcurrency as knotConcurrency, mapConcurrent as knotMapConcurrent, runWorkers as knotRunWorkers, memoizeTextCount as knotMemoizeTextCount, drainAll as knotDrainAll, limitConcurrent as knotLimitConcurrent, failureCohorts as knotFailureCohorts } from "../../../../scripts/perch-throughput.mjs";\nimport { analyzeBendSource as knotAnalyzeBendSource } from "../../../../scripts/perch-bend.mjs";\nimport { createBendReview as knotCreateBendReview, bendDeclarationSource as knotBendDeclarationSource } from "../../../../scripts/perch-bend-context.mjs";\n${patched}\nexport { createSourceAnalyzer as knotCreateSourceAnalyzer, resolveModule as knotResolveModule, buildGraph as knotBuildGraph, createLineReader as knotCreateLineReader, openStore as knotOpenStore, methodSteps as knotMethodSteps, methodStep as knotMethodStep, askKey as knotAskKey, estimateTokens as knotEstimateTokens };\n`;
}

export async function install() {
  const installed = JSON.parse(await readFile(join(root, 'node_modules/@lakeday/perch/package.json')));
  if (installed.version !== '0.3.5') throw new Error('Bend adapter requires reviewed Perch 0.3.5; refusing an unreviewed upgrade.');
  const current = await readFile(bundle, 'utf8');
  const original = current.startsWith(marker) ? await readFile(backup, 'utf8') : current;
  if (sha(original) !== expected) throw new Error('Upstream Perch bundle checksum changed; refusing to patch.');
  const parserFiles = (await readdir(join(root, 'vendor/bend-parser'))).sort();
  const inputs = [await readFile(fileURLToPath(import.meta.url)), await readFile(join(root, 'scripts/perch-bend.mjs')),
    await readFile(join(root, 'scripts/perch-bend-context.mjs')),
    await readFile(join(root, 'scripts/perch-throughput.mjs')), await readFile(join(root, 'scripts/perch-throughput-patch.mjs')),
    ...await Promise.all(parserFiles.map(name => readFile(join(root, 'vendor/bend-parser', name))))];
  const profile = `language-pack-1.20-v3+knot-bend-${sha(Buffer.concat(inputs)).slice(0, 16)}`;
  const patched = patchPerch(original, profile);
  if (!current.startsWith(marker)) await writeFile(backup, original);
  if (patched !== current) {
    await writeFile(`${bundle}.knot-tmp`, patched);
    await rename(`${bundle}.knot-tmp`, bundle);
  }
  console.log(`Perch 0.3.5: .bend parser enabled (${profile}).`);
  return { profile, upstream_sha256: expected, patched_sha256: sha(patched) };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { await install(); } catch (error) { console.error(error.message); process.exitCode = 1; }
}
