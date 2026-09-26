/** Side-effect-free Bend 2 source analysis for Perch. No module resolver or evaluator. */
import { book_nil, parse_book, Qnt } from '../vendor/bend-parser/bend.mts';
import baseSource from '../vendor/bend-parser/base-source.mjs';

export const BEND_PARSER_PROFILE = 'bend-2.0.29-574b6d3-observer-v2';
const ANALYSIS_PROFILE = 'language-pack-1.20-v3';
const NAMED = /^([a-z][a-z0-9-]{0,63})@((?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){3})$/;
const NAME = /^[A-Za-z_]\w*(\.[A-Za-z_]\w*)*$/;

function sourcePoints(source) {
  const points = new Array(source.length + 1);
  let line = 1, column = 1, byte = 0;
  for (let at = 0; at < source.length;) {
    const cp = source.codePointAt(at);
    const char = String.fromCodePoint(cp);
    points[at] = { line, column, byte };
    if (char.length === 2) points[at + 1] = { line, column, byte };
    const size = Buffer.byteLength(char);
    byte += size;
    if (char === '\n') { line++; column = 1; } else column += size;
    at += char.length;
  }
  points[source.length] = { line, column, byte };
  return (beg, end = beg) => ({
    start: points[Math.max(0, Math.min(source.length, beg))],
    end: points[Math.max(0, Math.min(source.length, end))],
  });
}

/** The import-header grammar is copied from pinned book_load; resolution is omitted. */
function parseImports(source) {
  const lines = source.split('\n');
  const body = lines.slice();
  const aliases = Object.create(null);
  const imports = [];
  const fail = (message, beg, end) => { throw { importSyntax: true, message, beg, end }; };
  for (let i = 0, at = 0; i < lines.length; at += lines[i].length + 1, i++) {
    const line = lines[i].trim();
    if (line === '' || line.startsWith('#')) continue;
    if (!/^import(\s|$)/.test(line)) break;
    const m = /^import\s+(\S+)(?:\s+as\s+([A-Za-z_]\w*))?\s*(?:#.*)?$/.exec(line);
    const beg = at + lines[i].indexOf(m?.[1] ?? line);
    if (m === null || (m[2] === undefined && m[1] !== 'Base')) {
      fail("Expected an import ('import Base', or 'import <path> as <Name>').", beg, at + lines[i].length);
    }
    const module = m[1], alias = m[2] ?? null;
    if (alias !== null) {
      if (!module.endsWith('.bend')) fail('Expected an import of a .bend file.', beg, beg + module.length);
      if (alias in aliases) fail(`Expected a fresh alias (${alias} names an earlier import).`, beg, beg + module.length);
      const nv = /^([^/]*@[^/]*)\//.exec(module);
      if (nv !== null && !NAMED.test(nv[1])) fail('Expected a named package with four version numbers.', beg, beg + module.length);
      // Replace only the already-validated package identity while checking the
      // upstream path grammar. No package name lookup, filesystem, or network.
      const path = nv === null ? module : '0x0/' + module.slice(nv[1].length + 1);
      if (!/^(\/|(\.\.\/)*)((?:[A-Za-z_][\w-]*\/)*[A-Za-z_][\w-]*)$/.test(
        path.replace(/^\.\//, '').slice(0, -5).replace(/^0x[0-9a-f]+\//, ''))) {
        fail('Expected an import path of plain names.', beg, beg + module.length);
      }
      aliases[alias] = '@import/' + alias; // Preserve the spelling: canonical module identity is unavailable.
    }
    imports.push({ module, alias, beg, end: beg + module.length });
    // Keep every UTF-16 offset and newline intact for parser spans.
    body[i] = ' '.repeat(lines[i].length);
  }
  return { body: body.join('\n'), aliases, imports };
}

function lexicalReference(term, source) {
  if (term?.$ === 'Var') term = term.v;
  if (term?.$ !== 'Ref' || !term.s) return null;
  const spelling = source.slice(term.s.beg, term.s.end);
  if (!NAME.test(spelling) || spelling !== term.k && '@import/' + spelling !== term.k) return null;
  return { name: spelling, beg: term.s.beg, end: term.s.end };
}

/** Walk original parser nodes, before match lowering can duplicate or erase them. */
function termReferences(term, source, found) {
  if (!term || typeof term !== 'object') return;
  const ref = lexicalReference(term, source);
  if (ref) found.push(ref);
  if (term.$ === 'Var' || term.$ === 'Ref') return;
  if (term.$ === 'Match') {
    for (const expr of term.e) termReferences(expr, source, found);
    for (const row of term.r) termReferences(row.f, source, found);
    return;
  }
  if (term.$ === 'Local') {
    for (const value of term.v) termReferences(value, source, found);
    termReferences(term.f, source, found);
    return;
  }
  for (const [key, value] of Object.entries(term)) {
    if (key === 's' || key === 'q') continue;
    if (Array.isArray(value)) value.forEach((node) => termReferences(node, source, found));
    else if (value && typeof value === 'object') termReferences(value, source, found);
  }
}

/**
 * Syntax analysis only. Metrics are null rather than fabricated; imported law
 * context and external datatype/template context are not compiler validation.
 */
export async function analyzeBendSource(source) {
  if (typeof source !== 'string') throw new TypeError('Bend source must be a string.');
  const location = sourcePoints(source);
  const analysis = {
    profile: ANALYSIS_PROFILE,
    language: 'bend',
    parser_status: 'parsed',
    parser_message: null,
    metrics: null,
    declarations: [], datatype_declarations: [], references: [], diagnostics: [],
    truncated: { declarations: false, references: false, diagnostics: false },
    parser_metadata: {
      profile: BEND_PARSER_PROFILE,
      compiler_commit: '574b6d39a235b539eb19a5c532993a0abb3d11ad',
      dependency_resolution: 'none',
      typechecked: false,
      metrics_status: 'unsupported',
    },
  };
  const unsupported = (message, loc = null) => analysis.diagnostics.push({ kind: 'unsupported', message, location: loc });
  const declarations = [];
  const calls = [];
  try {
    const { body, aliases, imports } = parseImports(source);
    const book = book_nil();
    if (imports.some((entry) => entry.module === 'Base')) {
      parse_book(book, '', baseSource, '', Object.create(null));
      for (const tld of Object.values(book.tlds)) tld.b = true;
    }
    if (imports.some((entry) => entry.alias !== null)) {
      unsupported('Imported module identities, declaration existence, constructor and datatype arities, and template signatures are unresolved; this analysis never loads dependencies.');
    }
    parse_book(book, '', body, '', aliases, {
      missingDatatype(name, span) {
        if (name.startsWith('@import/')) throw { dependencyContext: true, message: `Imported datatype ${name.slice(8)} requires quantity/arity context for + syntax.`, span };
      },
      externalConstructor(name, fields) {
        return name.startsWith('@import/') ? { k: name, n: fields, T: Qnt() } : null;
      },
      externalTemplate(name) {
        return name.startsWith('@import/') ? Infinity : 0;
      },
      externalLaw(name, resolved, beg, end) {
        const dot = name.indexOf('.');
        if (dot < 0 || !(name.slice(0, dot) in aliases)) return undefined;
        unsupported(`Imported law fill ${name}: the body uses the real parser, but law existence, parameter count, and template clauses require dependency context.`, location(beg, end));
        return { $: 'Def', n: 0, x: 0, T: Qnt(), v: null, m: '' };
      },
      call(term) {
        const ref = lexicalReference(term, source);
        if (ref) calls.push(ref);
      },
      declaration(kind, name, beg, end, term, tele = []) {
        if (kind === 'datatype') {
          const loc = location(beg, end);
          analysis.datatype_declarations.push({ name, location: loc, line: loc.start.line, end_line: loc.end.line });
          return;
        }
        const values = [];
        termReferences(term, source, values);
        tele.forEach((node) => termReferences(node, source, values));
        declarations.push({ kind, name, beg, end, values });
      },
    });
    const byName = new Map();
    for (const entry of declarations) {
      const previous = byName.get(entry.name);
      if (previous?.kind === 'law' && entry.kind === 'law_fill') {
        entry.law = previous;
        byName.set(entry.name, entry);
      } else byName.set(entry.name, entry);
    }
    for (const entry of byName.values()) {
      const loc = location(entry.beg, entry.end);
      const decl = {
        id: `bend:${entry.name}`,
        kind: 'function',
        syntax_kind: entry.law ? 'bend_law_definition' : `bend_${entry.kind}`,
        name: entry.name,
        qualified_name: entry.name,
        parent_function: null,
        function_depth: 0,
        line: loc.start.line,
        end_line: loc.end.line,
        location: loc,
        metrics: null,
      };
      if (entry.law) decl.law_location = location(entry.law.beg, entry.law.end);
      analysis.declarations.push(decl);
      const fragments = entry.law ? [entry.law, entry] : [entry];
      const refs = new Map();
      for (const fragment of fragments) {
        for (const ref of fragment.values) refs.set(`${ref.beg}:${ref.end}`, { ...ref, kind: 'value' });
        for (const ref of calls) {
          if (ref.beg >= fragment.beg && ref.end <= fragment.end) refs.set(`${ref.beg}:${ref.end}`, { ...ref, kind: 'call' });
        }
      }
      for (const ref of refs.values()) {
        const refLoc = location(ref.beg, ref.end);
        analysis.references.push({
          kind: ref.kind, name: ref.name, reference: ref.name,
          module: null, imported_name: null, alias: null,
          source: decl.id, line: refLoc.start.line, column: refLoc.start.column,
          location: refLoc,
        });
      }
    }
    for (const entry of imports) {
      const loc = location(entry.beg, entry.end);
      analysis.references.push({
        kind: 'import', name: entry.alias ?? 'Base', reference: entry.module,
        module: entry.module, imported_name: '*', alias: entry.alias,
        source: 'file', line: loc.start.line, column: loc.start.column, location: loc,
      });
    }
    analysis.declarations.sort((a, b) => a.location.start.byte - b.location.start.byte);
    analysis.references.sort((a, b) => a.location.start.byte - b.location.start.byte || a.kind.localeCompare(b.kind));
    unsupported('Complexity and Halstead metrics are unavailable. The graph reports explicit static calls and values in definitions and laws; dynamic calls, datatype declarations, constructors, foreign implementation paths, and desugared operations are omitted.');
  } catch (error) {
    const range = error?.importSyntax ? location(error.beg, error.end)
      : error?.dependencyContext ? location(error.span.beg, error.span.end)
      : error?.spn?.src !== baseSource && error?.spn ? location(error.spn.beg, error.spn.end) : null;
    let message = error?.importSyntax || error?.dependencyContext ? error.message : error?.$ === 'Err'
      ? `Expected ${typeof error.exp === 'string' ? error.exp : 'a valid Bend term'}${typeof error.obs === 'string' ? `; observed ${error.obs}` : ''}.`
      : error instanceof Error ? error.message : 'Bend parser failed.';
    const contextMissing = error?.dependencyContext === true;
    const resource = error instanceof RangeError;
    analysis.parser_status = resource ? 'resource-unavailable' : contextMissing ? 'unsupported' : 'parse-error';
    if (contextMissing) message += ' Imported datatype context is unavailable without loading dependencies.';
    analysis.parser_message = message;
    analysis.declarations = [];
    analysis.datatype_declarations = [];
    analysis.references = [];
    analysis.diagnostics.push({ kind: resource ? 'resource' : contextMissing ? 'unsupported' : 'syntax', message, location: range });
  }
  return analysis;
}
