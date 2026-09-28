import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import os from 'node:os';
import { stripTypeScriptTypes } from 'node:module';
import { fileURLToPath } from 'node:url';
import { book_nil, parse_book, term_lower } from '../../vendor/bend-parser/bend.mts';
import baseSource from '../../vendor/bend-parser/base-source.mjs';
import { parseImports, BEND_PARSER_PROFILE } from '../../scripts/perch-bend.mjs';
import { CLASSES, classify, executionReferences, sorted } from './features.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const OUT = 'docs/compiler-campaign/inventory';
const SEED = '.toolchain/bend-2.0.29-574b6d3/bend2/';
const COMP_HASH = '0cf866b28ff273d47970b3c16e82288e9676ce9f0ea3fce49877a82ce4a6301b';
export const json = value => JSON.stringify(value, null, 2) + '\n';
export const sha256 = text => crypto.createHash('sha256').update(text).digest('hex');
const read = (root, file) => fs.readFileSync(path.join(root, file), 'utf8');
const readJSON = (root, file) => JSON.parse(read(root, file));
const namespace = file => file === 'Base' ? '' : file.replace(/\.bend$/, '');

function failure(outcome, detail) { return Object.assign(new Error(detail), { outcome }); }
function errorOutcome(error) {
  return error.outcome ?? (error instanceof RangeError ? 'Exhausted' : error.code ? 'HostFailure' : 'InternalFailure');
}
function sourceFile(root, file) {
  if (!file.endsWith('.bend') || file.split('/').some(x => x === '..' || x.startsWith('.env'))) {
    throw failure('ResolutionFailure', `Not an allowed Bend path: ${file}`);
  }
  const target = fs.realpathSync(path.join(root, file));
  if (!target.startsWith(fs.realpathSync(root) + path.sep)) throw failure('ResolutionFailure', `Source escapes repository: ${file}`);
  if (!target.endsWith('.bend') || target.split(path.sep).some(x => x.startsWith('.env'))) throw failure('ResolutionFailure', `Not a Bend source target: ${file}`);
  return read(root, file);
}

export function packageCatalog(root) {
  const catalog = readJSON(root, 'packages/releases.json');
  return Object.entries(catalog.packages).map(([name, entry]) => {
    const bytes = read(root, entry.releaseRecord), release = JSON.parse(bytes);
    if (sha256(bytes) !== entry.releaseRecordSha256) throw failure('ResolutionFailure', `Release record pin changed: ${name}`);
    const closure = release.closure ?? release.upload_closure;
    if (!closure) throw failure('ResolutionFailure', `Missing release closure: ${name}`);
    const hashes = Array.isArray(closure)
      ? Object.fromEntries(closure.map(x => [x.path ?? x.name, x.sha256]))
      : Object.fromEntries(Object.entries(closure).map(([k, v]) => [k, v.sha256]));
    return { name, hash: entry.hash, directory: `packages/${name}`, hashes,
      release_record: entry.releaseRecord, release_record_sha256: sha256(bytes) };
  });
}

export class Inventory {
  constructor({ root = ROOT, packages = [], sources = null } = {}) {
    this.root = root; this.packages = packages; this.sources = sources;
    this.book = book_nil(); this.files = new Map(); this.loading = new Set();
    this.declarations = [];
  }
  resolve(from, spec) {
    if (spec === 'Base') return 'Base';
    if (spec.startsWith('./') || spec.startsWith('../')) {
      const file = path.posix.normalize(path.posix.join(path.posix.dirname(from), spec));
      if (file.startsWith('../')) throw failure('ResolutionFailure', `Import escapes repository: ${from}: ${spec}`);
      return file;
    }
    const pkg = this.packages.find(p => spec.startsWith(p.hash + '/'));
    if (!pkg) throw failure('Unsupported', `Unresolved offline package import: ${from}: ${spec}`);
    const suffix = spec.slice(pkg.hash.length + 1);
    if (!pkg.hashes[suffix]) throw failure('ResolutionFailure', `File absent from release: ${spec}`);
    return spec;
  }
  source(file) {
    if (file === 'Base') return baseSource;
    if (this.sources) {
      if (!this.sources.has(file)) throw failure('ResolutionFailure', `Missing source: ${file}`);
      return this.sources.get(file);
    }
    const pkg = this.packages.find(p => file.startsWith(p.hash + '/'));
    if (pkg) {
      const suffix = file.slice(pkg.hash.length + 1), expected = pkg.hashes[suffix];
      if (!expected || !suffix.endsWith('.bend')) throw failure('ResolutionFailure', `File absent from release: ${file}`);
      const local = sourceFile(this.root, pkg.directory + '/' + suffix);
      if (sha256(local) === expected) return local;
      const cache = path.join(process.env.BEND_LIB ?? path.join(os.homedir(), '.bend/lib'), file);
      if (!fs.existsSync(cache)) throw failure('ResolutionFailure', `Pinned package unavailable offline: ${file}`);
      const source = fs.readFileSync(cache, 'utf8');
      if (sha256(source) !== expected) throw failure('ResolutionFailure', `Published bytes differ: ${file}`);
      return source;
    }
    return sourceFile(this.root, file);
  }
  load(file) {
    if (this.files.has(file)) return;
    if (this.loading.has(file)) throw failure('ResolutionFailure', `Import cycle: ${file}`);
    this.loading.add(file);
    const source = this.source(file), ns = namespace(file);
    const { body, imports } = parseImports(source), aliases = Object.create(null);
    const resolved = imports.map(i => ({ module: i.module, alias: i.alias, file: this.resolve(file, i.module) }));
    for (const entry of resolved) {
      this.load(entry.file);
      if (entry.alias !== null) aliases[entry.alias] = namespace(entry.file);
    }
    const calls = [], declarations = [];
    const before = new Set(Object.keys(this.book.tlds));
    try {
      parse_book(this.book, file === 'Base' ? 'seed/' : path.posix.dirname(file) + '/', body, ns, aliases, {
        call(term, beg, end) { calls.push({ term, beg, end }); },
        declaration: (kind, name, beg, end, term, signatures = []) => {
          const dot = name.indexOf('.'), alias = dot < 0 ? '' : name.slice(0, dot);
          const key = kind === 'datatype' || kind === 'law' ? name
            : alias in aliases ? aliases[alias] + name.slice(dot) : ns ? ns + '.' + name : name;
          const tld = this.book.tlds[key];
          if (kind === 'datatype') signatures = [term_lower(tld.T), ...tld.c.map(c => term_lower(c.T))];
          // Fill headers contain bare names, whose parser placeholders are Qnt.
          // Their types come from the resolved law, not those placeholders.
          if (kind === 'law_fill') signatures = [term_lower(tld.T)];
          declarations.push({ file, key, name: name.startsWith(ns + '.') ? name.slice(ns.length + 1) : name,
            kind, beg, end, source, body: term, signatures, calls: [] });
        },
      });
    } catch (error) {
      const outcome = error instanceof RangeError ? 'Exhausted' : error?.$ === 'Err' ? 'Invalid' : 'InternalFailure';
      const detail = error?.$ === 'Err' ? `Expected ${typeof error.exp === 'string' ? error.exp : 'valid syntax'} at ${error.spn?.beg ?? '?'}` : String(error);
      throw failure(outcome, `${file}: ${detail}`);
    }
    if (file === 'Base') for (const [key, tld] of Object.entries(this.book.tlds)) if (!before.has(key)) tld.b = true;
    for (const d of declarations) d.calls = calls.filter(c => c.beg >= d.beg && c.end <= d.end).map(c => c.term);
    this.files.set(file, { file, sha256: sha256(source), imports: resolved, declarations });
    this.declarations.push(...declarations);
    this.loading.delete(file);
  }
  manifest() {
    return [...this.files.values()].sort((a, b) => a.file.localeCompare(b.file, 'en')).map(f => {
      const declarations = f.declarations.map(d => {
        const evidence = classify(d, this.book), execution = executionReferences(d.body, this.book);
        return { id: `${d.file}::${d.name}:${d.kind}`, name: d.name, key: d.key, kind: d.kind,
          lines: [d.source.slice(0, d.beg).split('\n').length, d.source.slice(0, d.end).split('\n').length],
          ...evidence, execution };
      });
      const imports = f.imports.map(i => ({ ...i, feature: i.file === 'Base' ? 'imports.base' : i.module.startsWith('0x') ? 'imports.package' : 'imports.local' }));
      return { file: f.file, sha256: f.sha256, imports,
        features: sorted([...imports.map(i => i.feature), ...declarations.flatMap(d => d.features)]), declarations };
    });
  }
}

export function intrinsicOperations(source) {
  if (sha256(source) !== COMP_HASH) throw failure('Unsupported', 'Seed comp.ts pin changed; review the OPERATIONS extraction.');
  const table = source.slice(source.indexOf('const CMPS ='), source.indexOf('// Optimized\n'));
  const helper = source.slice(source.indexOf('function tpl_ops('), source.indexOf('\nfunction tpl(', source.indexOf('function tpl_ops(')));
  if (!table.includes('const OPERATIONS:') || !helper) throw failure('InternalFailure', 'Missing pinned OPERATIONS table/helper.');
  // Only the hash-pinned pure table and its pure string helper enter the context.
  // No compiler entry, loader, filesystem, process or network is exposed.
  const code = stripTypeScriptTypes(helper + '\n' + table + '\nOPERATIONS;');
  const operations = vm.runInNewContext(code, Object.create(null), { timeout: 1000 });
  return Object.fromEntries(Object.keys(operations).sort().map(k => [k, {
    js: operations[k].JS !== undefined, native: operations[k].C !== undefined || operations[k].call === true,
  }]));
}

export function wordRepresentations(source) {
  if (sha256(source) !== COMP_HASH) throw failure('Unsupported', 'Seed comp.ts pin changed; review WORDS extraction.');
  const code = source.slice(source.indexOf('const W32:'), source.indexOf('const WIDE ='));
  return Object.keys(vm.runInNewContext(stripTypeScriptTypes(code + '\nWORDS;'), Object.create(null), { timeout: 1000 })).sort();
}

export function closure(roots, declarations, book, operations, mode = 'execution', target = 'js', words = []) {
  const byKey = new Map();
  for (const d of declarations) {
    const old = byKey.get(d.key);
    // A fill supplies the executable body; a law supplies its static contract.
    byKey.set(d.key, { ...d,
      references: sorted([...(old?.references ?? []), ...d.references]),
      type_references: sorted([...(old?.type_references ?? []), ...(d.type_references ?? [])]),
      execution: d.kind === 'law' && old ? old.execution : d.execution });
  }
  const ctorOwner = new Map(Object.entries(book.tlds).flatMap(([k, t]) => t.$ === 'ADT' ? t.c.map(c => [c.k, k]) : []));
  const seen = new Map(), pending = roots.map(key => ({ key, via: null })), unresolved = [];
  while (pending.length) {
    let { key, via } = pending.shift();
    key = ctorOwner.get(key) ?? key;
    if (seen.has(key)) continue;
    const d = byKey.get(key), tld = book.tlds[key];
    if (!d || !tld) { unresolved.push({ key, via }); continue; }
    const op = key.toLowerCase().replace(/[./]/g, '_');
    const intrinsic = tld.$ === 'Def' && tld.b === true && tld.i === undefined && operations[op]?.[target] === true;
    const foreign = tld.$ === 'Def' && tld.i !== undefined;
    const representation = tld.$ === 'ADT' && tld.b === true && words.includes(key);
    const cut = mode !== 'static' && (intrinsic || foreign || representation);
    const refs = mode === 'static' ? d.references : mode === 'runtime'
      ? [...(representation ? [] : d.type_references), ...(cut ? [] : [...d.execution.references, ...(d.execution.types ?? [])])]
      : cut ? [] : d.execution.references;
    const dependencies = sorted(refs.map(r => ctorOwner.get(r) ?? r).filter(r => r !== key));
    seen.set(key, { key, file: d.id.split('::')[0], via, kind: tld.$,
      boundary: intrinsic ? 'intrinsic' : foreign ? 'foreign' : representation ? 'representation' : tld.v === null ? 'bodiless' : 'source',
      unsafe: tld.u === true, dependencies,
      dynamic_calls: cut ? [] : d.execution.dynamic_calls });
    pending.push(...dependencies.map(key => ({ key, via: d.key })));
  }
  const entries = [...seen.values()].sort((a, b) => a.key.localeCompare(b.key, 'en'));
  return { roots, mode, target, totals: { declarations: entries.length, base: entries.filter(d => d.file === 'Base').length,
    base_intrinsics: entries.filter(d => d.file === 'Base' && d.boundary === 'intrinsic').length,
    foreign: entries.filter(d => d.boundary === 'foreign').length }, entries,
    unresolved: unresolved.sort((a, b) => a.key.localeCompare(b.key, 'en')) };
}

export function approvedPolicy(files) {
  return { schema: 1, scope: 'Reviewed implementation syntax, not Knot acceptance.',
    forbidden_dependency_features: ['arrays', 'foreign', 'holes', 'literals.f32', 'unsafe', 'bindings.parallel', 'calls.offload'],
    files: Object.fromEntries(files.filter(f => f.file.startsWith('src/')).map(f => [f.file, {
      imports: f.imports.map(i => ({ module: i.module, file: i.file })),
      declarations: Object.fromEntries(f.declarations.map(d => [d.id, d.features])),
    }])) };
}

export function policyViolations(files, policy) {
  const violations = [], byFile = new Map(files.map(f => [f.file, f]));
  const dependencies = new Set();
  const visit = file => {
    if (file === 'Base' || dependencies.has(file)) return;
    dependencies.add(file);
    const entry = byFile.get(file);
    if (!entry) { violations.push(`${file}: missing dependency inventory`); return; }
    entry.imports.forEach(i => visit(i.file));
    for (const feature of entry.features) if (policy.forbidden_dependency_features.includes(feature)) violations.push(`${file}: forbidden dependency feature ${feature}`);
  };
  for (const f of files.filter(f => f.file.startsWith('src/'))) {
    visit(f.file);
    const approved = policy.files[f.file];
    if (!approved) violations.push(`${f.file}: unapproved source file`);
    for (const i of f.imports) {
      if (!approved?.imports.some(a => a.module === i.module && a.file === i.file)) violations.push(`${f.file}: unapproved import ${i.module} -> ${i.file}`);
      visit(i.file);
    }
    for (const d of f.declarations) for (const feature of d.features) {
      if (!approved?.declarations[d.id]?.includes(feature)) violations.push(`${d.id}: unapproved feature ${feature}`);
    }
  }
  return sorted(violations);
}

export function outcome(expected, success) {
  if (expected.exit === 0) return success;
  const value = ({ 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure' })[expected.exit];
  if (!value) throw failure('InternalFailure', `Unknown expected outcome ${expected.exit}`);
  return value;
}

const SUITES = [
  ['frontend', 'tests/subsets/frontend-cases.json', 'tests/subsets/', 'tests/subsets/check_frontend.py'],
  ['checker', 'tests/compiler-checker/cases.json', '', 'tests/compiler-checker/check.py'],
  ['catalog', 'tests/compiler-structural/cases.json', 'tests/compiler-structural/', 'tests/compiler-structural/check.py'],
  ['fields', 'tests/compiler-fields/cases.json', 'tests/compiler-fields/', 'tests/compiler-fields/check.py'],
  ['wasm', 'tests/compiler-wasm/cases.json', '', 'tests/compiler-wasm/check.py'],
];
export function acceptedInventory(root = ROOT) {
  const records = [], suites = [];
  for (const [suite, manifest, prefix, gate] of SUITES) {
    const data = readJSON(root, manifest);
    suites.push({ suite, manifest, manifest_sha256: sha256(read(root, manifest)), gate, gate_sha256: sha256(read(root, gate)), fixtures: data.cases.length });
    for (const c of data.cases) {
      const file = prefix + c.file, source = sourceFile(root, file);
      const stages = suite === 'frontend' ? { parse: { outcome: 'Parsed', expectation: c.tree } }
        : suite === 'wasm' ? Object.fromEntries(['check', 'eval', 'wasm'].map(s => [s, { outcome: { check: 'Checked', eval: 'Evaluated', wasm: 'Built' }[s], reference_calls: c.calls.length }]))
        : Object.fromEntries((suite === 'checker' ? [['check', c.knot]]
          : suite === 'catalog' ? [['catalog', c.catalog], ['compile', c.compiler]]
          : [['check', c.check], ['eval', c.eval], ['compile', c.compile]])
          .map(([stage, e]) => [stage, { outcome: outcome(e, { catalog: 'Catalogued', check: 'Checked', eval: 'Evaluated', compile: 'Built' }[stage]), expectation: e }]));
      let features = null, analysis;
      try {
        const inv = new Inventory({ root }); inv.load(file);
        features = inv.manifest().find(f => f.file === file).features;
        analysis = { outcome: 'Parsed' };
      } catch (error) { analysis = { outcome: errorOutcome(error), detail: error.message }; }
      if (!features && Object.values(stages).some(s => ['Checked', 'Evaluated', 'Built', 'Catalogued'].includes(s.outcome))) {
        throw failure('InternalFailure', `Cannot inventory accepted fixture ${file}: ${analysis.detail}`);
      }
      records.push({ suite, file, sha256: sha256(source), features, analysis, stages, reference: c.reference ?? { observations: c.calls } });
    }
  }
  const classes = Object.keys(CLASSES).sort().map(feature => ({ feature, stages: Object.fromEntries(['parse', 'catalog', 'check', 'eval', 'wasm'].map(stage => {
    const evidence = records.filter(r => r.features?.includes(feature) && ['Parsed', 'Catalogued', 'Checked', 'Evaluated', 'Built'].includes(r.stages[stage]?.outcome))
      .map(r => `${r.suite}:${r.file}`);
    return [stage, { status: evidence.length ? 'observed-in-successful-fixtures' : 'no-positive-fixture-evidence', evidence }];
  })) }));
  return { schema: 1, scope: 'Fixed fixture/gate expectations; census does not run the gates. Per-feature evidence is bounded by each fixture, not general support for the class.',
    limits: ['Rejected fixture features are not individually blamed for its diagnostic.', 'Gate-generated boundary probes and semantic mutants are not counted as source acceptance.', 'An expected result is not evidence of a fresh successful gate execution.'], suites, classes, fixtures: records };
}

export function build(root = ROOT) {
  const packages = packageCatalog(root), inv = new Inventory({ root, packages });
  const pin = readJSON(root, 'vendor/bend-parser/upstream.json');
  if (sha256(baseSource) !== pin.files['bend2/base.bend']) throw failure('Unsupported', 'Vendored Base pin mismatch');
  if (sha256(read(root, SEED + 'base.bend')) !== sha256(baseSource)) throw failure('Unsupported', 'Seed and vendored Base differ');
  const comp = read(root, SEED + 'comp.ts'), operations = intrinsicOperations(comp), words = wordRepresentations(comp);
  const sources = fs.readdirSync(path.join(root, 'src')).filter(f => f.endsWith('.bend')).sort().map(f => 'src/' + f);
  sources.forEach(f => inv.load(f));
  const packageRoots = [...packages.map(p => p.directory + '/main.bend'), 'packages/output_builder/bytes.bend'];
  packageRoots.forEach(f => inv.load(f));
  const files = inv.manifest(), declarations = files.flatMap(f => f.declarations);
  const counts = selected => ({ files: selected.length, declarations: selected.reduce((n, f) => n + f.declarations.length, 0),
    unique_declarations: sorted(selected.flatMap(f => f.declarations).map(d => d.key)).length,
    definitions: selected.flatMap(f => f.declarations).filter(d => d.kind === 'definition').length,
    classes: sorted(selected.flatMap(f => f.features)).length });
  const metadata = { schema: 1, seed: { version: pin.version, commit: pin.commit, base_sha256: sha256(baseSource), comp_sha256: sha256(comp) },
    parser: { profile: BEND_PARSER_PROFILE, sha256: sha256(read(root, 'vendor/bend-parser/bend.mts')), typechecked: false },
    census_sources: Object.fromEntries(['tools/census/census.mjs', 'tools/census/features.mjs', 'scripts/perch-bend.mjs'].map(file => [file, sha256(read(root, file))])) };
  const implementation = { ...metadata, scope: { compiler: 'Every src/*.bend file, including laws/proofs.', packages: 'Runtime entry import closures of six published packages; package proof/test harnesses excluded.', package_roots: packageRoots.sort() },
    package_pins: packages.map(({ name, hash, release_record, release_record_sha256 }) => ({ name, hash, release_record, release_record_sha256 })),
    classes: CLASSES, totals: { compiler: counts(files.filter(f => f.file.startsWith('src/'))),
      frontend_files: counts(files.filter(f => ['src/lex.bend', 'src/parse.bend', 'src/syntax.bend'].includes(f.file))),
      packages: counts(files.filter(f => f.file.startsWith('packages/'))),
      published_imports: counts(files.filter(f => f.file.startsWith('0x'))), base: counts(files.filter(f => f.file === 'Base')) }, files };
  const roots = { frontend: ['src/lex.tokenize', 'src/parse.parse'], compiler: ['src/compile-cli.main'] };
  const closures = { ...metadata, method: 'Static source-body upper bound under the pinned intrinsic cut; not the seed emitted/optimized call graph.',
    limits: ['All branches and syntactically supplied callbacks are retained; variable calls are listed, not solved by flow analysis.',
      'Template value arguments are retained before instantiation; no instance-specific specialization or higher-order flow analysis is performed.',
      'Static closure includes signatures, constructor telescopes and proof bodies. The execution slice omits them.',
      'Base native representations and runtime support are trusted separately from OPERATIONS; neither closure proves seed correctness.'],
    operations, word_representations: words, roots: Object.fromEntries(Object.entries(roots).map(([name, rs]) => [name, {
      js: closure(rs, declarations, inv.book, operations, 'runtime', 'js', words),
      native: closure(rs, declarations, inv.book, operations, 'runtime', 'native', words),
      functions: closure(rs, declarations, inv.book, operations),
      static: closure(rs, declarations, inv.book, operations, 'static'),
    }])) };
  for (const [name, sets] of Object.entries(closures.roots)) for (const [target, set] of Object.entries(sets)) {
    if (set.unresolved.length) throw failure('ResolutionFailure', `${name}/${target}: unresolved references ${json(set.unresolved)}`);
  }
  const contract = readJSON(root, 'src/CONTRACT.json');
  const base = Object.entries(inv.book.tlds).filter(([, t]) => t.b === true);
  const hosts = { ...metadata,
    scope: 'Seed-built artifacts: declared foreign boundaries and intrinsic/representation requirements of the static slice. Emitted Knot artifacts: contract plus independent Wasm gate.',
    base_trust: { entries: base.length,
      foreign: base.filter(([, t]) => t.i !== undefined).map(([name, t]) => ({ name, implementations: t.i.map(p => {
        const file = path.posix.normalize(SEED + p.slice('seed/'.length));
        return { file, sha256: sha256(read(root, file)) };
      }) })),
      unsafe: base.filter(([, t]) => t.u === true).map(([name]) => name).sort(),
      bodiless: base.filter(([, t]) => t.$ === 'Def' && t.v === null && !t.i).map(([name]) => name).sort() },
    artifacts: Object.fromEntries(Object.entries(closures.roots).map(([name, sets]) => [name, Object.fromEntries(['js', 'native'].map(target => {
      const entries = sets[target].entries;
      return [target, { foreign: entries.filter(d => d.boundary === 'foreign').map(d => d.key),
        intrinsics: entries.filter(d => d.boundary === 'intrinsic').map(d => d.key),
        word_representations: entries.filter(d => d.boundary === 'representation').map(d => d.key),
        unsafe: entries.filter(d => d.unsafe).map(d => d.key),
        external_host_effects: entries.some(d => d.boundary === 'foreign') }];
    }))])),
    knot_emitted_wasm: { profile: contract.profile, contract: 'src/CONTRACT.json', contract_sha256: sha256(read(root, 'src/CONTRACT.json')),
      host: contract.host, capabilities: contract.wasm, gate: 'tests/compiler-wasm/check.py',
      boundary: 'Native Wasm engine executes enum ordinals; no imports, linear memory, IO or GPU. This is separate from the seed-built compiler host.' },
    limits: ['Foreign declarations are inventoried, not executed by census.', 'The compiler driver and underlying VM/runtime remain trusted; source analysis does not qualify an ABI.'] };
  return { 'implementation.json': implementation, 'base-closure.json': closures, 'accepted.json': acceptedInventory(root), 'hosts.json': hosts };
}

export function main(args = process.argv.slice(2)) {
  if (args.some(a => a !== '--check')) throw failure('HostFailure', 'Usage: node tools/census/census.mjs [--check]');
  const manifests = build(), policy = readJSON(ROOT, 'tools/census/approved.json');
  const violations = policyViolations(manifests['implementation.json'].files, policy);
  if (violations.length) throw failure('Unsupported', violations.join('\n'));
  for (const [file, data] of Object.entries(manifests)) {
    const output = path.join(ROOT, OUT, file), bytes = json(data);
    if (args.includes('--check')) {
      if (!fs.existsSync(output) || fs.readFileSync(output, 'utf8') !== bytes) throw failure('Unsupported', `Stale inventory: ${OUT}/${file}; review policy and run npm run census.`);
    } else { fs.mkdirSync(path.dirname(output), { recursive: true }); fs.writeFileSync(output, bytes); }
  }
  console.log(json({ status: args.includes('--check') ? 'current' : 'generated', ...manifests['implementation.json'].totals,
    base_closures: Object.fromEntries(Object.entries(manifests['base-closure.json'].roots).map(([k, v]) => [k, { js: v.js.totals, native: v.native.totals }])) }).trim());
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(); } catch (error) { console.error(`${errorOutcome(error)}: ${error.message}`); process.exitCode = 1; }
}
