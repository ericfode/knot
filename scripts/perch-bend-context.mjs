// Review context is separate from the side-effect-free parser. Only explicitly
// referenced local Bend imports are read, always from the current working tree.
import { createHash } from 'node:crypto';
import { readFile, realpath } from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { analyzeBendSource } from './perch-bend.mjs';

const hash = source => createHash('sha256').update(source).digest('hex');
const identifier = (path, declaration) => `${path}::${declaration.qualified_name}`;
export const BEND_CONTEXT_PROFILE = 'working-tree-datatypes-v1';
const within = (root, path) => {
  const rel = relative(root, path);
  return rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel);
};

/** Explicit files only; each real source is read and parsed once for this command. */
export async function createBendSourceSnapshot(root) {
  const realRoot = await realpath(root), paths = new Map(), sources = new Map();
  let parseCalls = 0;
  const outside = () => Object.assign(new Error('Bend source is outside this workspace'), {
    code: 'BEND_OUTSIDE_WORKSPACE', bend_snapshot_io: true,
  });
  return {
    root: realRoot,
    get stats() { return { requested_paths: paths.size, parse_calls: parseCalls }; },
    async load(path) {
      const absolute = resolve(realRoot, path);
      if (!within(realRoot, absolute)) throw outside();
      if (!paths.has(absolute)) paths.set(absolute, (async () => {
        let actual;
        try { actual = await realpath(absolute); }
        catch (error) { throw Object.assign(error, { bend_snapshot_io: true }); }
        if (!within(realRoot, actual)) throw outside();
        if (!sources.has(actual)) sources.set(actual, (async () => {
          let source;
          try { source = await readFile(actual, 'utf8'); }
          catch (error) { throw Object.assign(error, { bend_snapshot_io: true }); }
          parseCalls++;
          const analysis = await analyzeBendSource(source);
          return Object.freeze({ source, analysis, source_sha256: hash(source) });
        })());
        return sources.get(actual);
      })());
      return paths.get(absolute);
    },
  };
}

export function bendDeclarationSource(source, declaration, location = declaration.location) {
  const body = Buffer.from(source).subarray(location.start.byte, location.end.byte).toString('utf8');
  // Keep the declaration's immediately adjacent contract comment, without
  // borrowing a previous declaration or sibling that happens to share a line.
  if (location.start.column !== 1) return body;
  const lines = source.split('\n');
  const comments = [];
  for (let i = location.start.line - 2; i >= 0 && /^\s*#/.test(lines[i]); i--) comments.unshift(lines[i]);
  return comments.length ? `${comments.join('\n')}\n${body}` : body;
}

/** One immutable working-tree source snapshot per file-check invocation. */
export async function createBendReview({ root, path, source, analysis, limits = {}, snapshot = null }) {
  const bounds = { helpers: 16, files: 12, bytes: 48_000, callers: 4, ...limits };
  const realRoot = await realpath(root);
  if (snapshot && snapshot.root !== realRoot) throw new Error('Bend source snapshot belongs to another workspace');
  const files = new Map();
  const loads = new Map();
  const contexts = new Map();
  const makeFile = (filePath, text, parsed) => {
    const references = new Map(), callers = new Map();
    for (const reference of parsed.references) {
      if (reference.kind === 'import') continue;
      if (!references.has(reference.source)) references.set(reference.source, []);
      references.get(reference.source).push(reference);
      if (!callers.has(reference.name)) callers.set(reference.name, new Set());
      callers.get(reference.name).add(reference.source);
    }
    // Datatypes are review context, never function nodes in the semantic graph.
    const datatypes = new Map((parsed.datatype_declarations ?? []).map(decl => [decl.name, {
      ...decl, id: `bend-type:${decl.name}`, qualified_name: decl.name, syntax_kind: 'bend_datatype',
    }]));
    for (const decl of [...parsed.declarations, ...datatypes.values()]) {
      const refs = decl.context_references ?? [];
      if (refs.length) references.set(decl.id, [...(references.get(decl.id) ?? []), ...refs]);
      for (const ref of refs) {
        if (!callers.has(ref.name)) callers.set(ref.name, new Set());
        callers.get(ref.name).add(decl.id);
      }
    }
    return {
      path: filePath, source: text, analysis: parsed, source_sha256: hash(text),
      declarations: new Map(parsed.declarations.map(decl => [decl.qualified_name, decl])),
      datatypes,
      imports: parsed.references.filter(ref => ref.kind === 'import'),
      references, callers, lines: text.split('\n'), declarationSources: new Map(),
    };
  };
  const primary = makeFile(path, source, analysis);
  files.set(path, primary);

  async function importedFile(from, module) {
    if (!module.startsWith('./') && !module.startsWith('../')) return { reason: 'nonlocal-import' };
    const absolute = resolve(root, dirname(from.path), module);
    if (!absolute.endsWith('.bend') || !within(resolve(root), absolute)) return { reason: 'outside-workspace' };
    const filePath = relative(resolve(root), absolute).split(sep).join('/');
    if (files.has(filePath)) return { file: files.get(filePath) };
    if (!loads.has(filePath)) loads.set(filePath, (async () => {
      if (snapshot) {
        let loaded;
        try { loaded = await snapshot.load(filePath); }
        catch (error) {
          if (!error.bend_snapshot_io) throw error;
          return { reason: error.code === 'BEND_OUTSIDE_WORKSPACE' ? 'outside-workspace'
            : `unavailable-local-import:${error.code ?? 'read-error'}` };
        }
        if (loaded.analysis.parser_status !== 'parsed') throw new Error(`Bend context ${filePath} does not parse: ${loaded.analysis.parser_message ?? loaded.analysis.parser_status}`);
        const file = makeFile(filePath, loaded.source, loaded.analysis);
        files.set(filePath, file);
        return { file };
      }
      let actual, text;
      try {
        actual = await realpath(absolute);
        if (!within(realRoot, actual)) return { reason: 'outside-workspace' };
        text = await readFile(actual, 'utf8');
      } catch (error) {
        return { reason: `unavailable-local-import:${error.code ?? 'read-error'}` };
      }
      const parsed = await analyzeBendSource(text);
      if (parsed.parser_status !== 'parsed') throw new Error(`Bend context ${filePath} does not parse: ${parsed.parser_message ?? parsed.parser_status}`);
      const file = makeFile(filePath, text, parsed);
      files.set(filePath, file);
      return { file };
    })());
    return loads.get(filePath);
  }

  async function resolveReference(file, name, admitted) {
    const local = file.declarations.get(name) ?? file.datatypes.get(name);
    if (local) return { file, declaration: local };
    const dot = name.indexOf('.');
    const imported = dot < 0 ? null : file.imports.find(ref => ref.alias === name.slice(0, dot));
    if (!imported) return { reason: 'unresolved-or-builtin' };
    const importedPath = relative(resolve(root), resolve(root, dirname(file.path), imported.module)).split(sep).join('/');
    if (!admitted.has(importedPath) && admitted.size >= bounds.files) return { reason: 'context-file-limit', truncated: true };
    const loaded = await importedFile(file, imported.module);
    if (!loaded.file) return loaded;
    admitted.add(loaded.file.path);
    const declaration = loaded.file.declarations.get(name.slice(dot + 1)) ?? loaded.file.datatypes.get(name.slice(dot + 1));
    return declaration ? { file: loaded.file, declaration } : { reason: 'declaration-not-in-import', file: loaded.file };
  }

  function entry(file, declaration, location) {
    const span = location ?? declaration.location;
    const key = `${span.start.byte}:${span.end.byte}`;
    if (!file.declarationSources.has(key)) file.declarationSources.set(key, bendDeclarationSource(file.source, declaration, location));
    return {
      name: declaration.qualified_name ?? declaration.name, path: file.path,
      line: location?.start.line ?? declaration.line,
      end_line: location?.end.line ?? declaration.end_line,
      source: file.declarationSources.get(key),
    };
  }

  async function contextFor(name) {
    const declaration = primary.declarations.get(name) ?? primary.datatypes.get(name);
    if (!declaration) throw new Error(`No parsed Bend declaration ${path}::${name}.`);
    const admitted = new Set([path]);
    const used = new Set([path]);
    const visited = new Set([identifier(path, declaration)]);
    const unresolved = new Map();
    const calls = [], calledBy = [], laws = [], datatypes = [];
    const calleeNodes = [], callerNodes = [];
    const pending = [{ file: primary, declaration }];
    const suppliedDatatypes = new Set();
    const datatypeContextFiles = new Set([path]);
    let importedTypeHelpers = 0;
    let bytes = 0, truncated = false, pairedLawAttempted = false;
    const add = (list, item) => {
      if (list === laws) pairedLawAttempted = true;
      const size = Buffer.byteLength(item.source);
      if (bytes + size > bounds.bytes) { truncated = true; return false; }
      bytes += size;
      used.add(item.path);
      if (list !== datatypes) datatypeContextFiles.add(item.path);
      list.push(item);
      return true;
    };
    const node = (file, decl) => ({ ...decl, id: identifier(file.path, decl), path: file.path });
    const note = (file, name, reason, limited = false) => {
      unresolved.set(`${file.path}:${name}:${reason}`, { path: file.path, name, reason });
      truncated ||= limited;
    };
    const includeDatatype = target => {
      const { file, declaration: datatype } = target;
      const id = identifier(file.path, datatype);
      if (suppliedDatatypes.has(id)) return true;
      if (!add(datatypes, entry(file, datatype))) {
        note(file, datatype.name, 'context-byte-limit', true);
        return false;
      }
      suppliedDatatypes.add(id);
      visited.add(id);
      pending.push(target);
      return true;
    };

    if (declaration.law_location) add(laws, entry(primary, declaration, declaration.law_location));
    if (declaration.syntax_kind === 'bend_law_fill') {
      const target = await resolveReference(primary, name, admitted);
      if (target.declaration && target.declaration !== declaration) add(laws, entry(target.file, target.declaration));
      else {
        // A fill's own dotted name is already a local declaration. Resolve its
        // declared alias explicitly to recover the matching source law.
        const dot = name.indexOf('.');
        const imported = primary.imports.find(ref => ref.alias === name.slice(0, dot));
        if (imported) {
          const loaded = await importedFile(primary, imported.module);
          const law = loaded.file?.declarations.get(name.slice(dot + 1));
          if (law) add(laws, entry(loaded.file, law, law.law_location));
          else note(primary, name, loaded.reason ?? 'imported-law-unavailable');
        }
      }
    }
    while (pending.length) {
      const current = pending.shift();
      const references = current.file.references.get(current.declaration.id) ?? [];
      for (const reference of references) {
        const target = await resolveReference(current.file, reference.name, admitted);
        if (!target.declaration) {
          // A missing declaration was checked against this captured file; its
          // hash must invalidate the result if the declaration is later added.
          if (target.file) used.add(target.file.path);
          note(current.file, reference.name, target.reason, target.truncated);
          continue;
        }
        const id = identifier(target.file.path, target.declaration);
        if (visited.has(id)) continue;
        if (target.declaration.syntax_kind === 'bend_datatype') {
          // Local datatype source was already part of the context contract.
          // Newly followed imported datatype declarations share the helper cap.
          if (target.file.path !== path && calls.length + importedTypeHelpers >= bounds.helpers) {
            note(current.file, reference.name, 'context-helper-limit', true);
            continue;
          }
          if (includeDatatype(target) && target.file.path !== path) importedTypeHelpers++;
          continue;
        }
        if (calls.length + importedTypeHelpers >= bounds.helpers) { note(current.file, reference.name, 'context-helper-limit', true); continue; }
        visited.add(id);
        if (add(calls, entry(target.file, target.declaration))) {
          calleeNodes.push({ node: node(target.file, target.declaration), lines: target.file.lines, calls: [] });
          pending.push(target);
          if (target.declaration.law_location) add(laws, entry(target.file, target.declaration, target.declaration.law_location));
        }
      }
    }
    // Only direct callers already present in the target file; no repository
    // discovery and no unrelated file/name fallback.
    const callers = primary.callers.get(name) ?? new Set();
    for (const caller of primary.analysis.declarations.filter(decl => decl.id !== declaration.id && callers.has(decl.id))) {
      if (calledBy.length >= bounds.callers) { truncated = true; break; }
      if (add(calledBy, entry(primary, caller))) callerNodes.push({ node: node(primary, caller), lines: primary.lines, site: null });
    }
    // Preserve the existing same-file datatype context. Any explicitly
    // referenced type has already been included and traversed above.
    for (const filePath of datatypeContextFiles) {
      const file = files.get(filePath);
      for (const datatype of file.datatypes.values()) {
        if (datatype !== declaration && !suppliedDatatypes.has(identifier(file.path, datatype))) add(datatypes, entry(file, datatype));
      }
    }
    const provenance = {
      basis: 'working-tree',
      profile: BEND_CONTEXT_PROFILE,
      files: [...used].sort().map(path => ({ path, source_sha256: files.get(path).source_sha256 })),
      unresolved: [...unresolved.values()], truncated,
      limits: bounds,
    };
    const contextNotes = { basis: provenance.basis, profile: BEND_CONTEXT_PROFILE, unresolved: provenance.unresolved, truncated };
    // A second view of the already admitted laws, not another traversal or
    // budget. Keep missing/truncated proof contracts explicit too.
    const pairedLawContext = pairedLawAttempted || declaration.law_location || declaration.syntax_kind === 'bend_law_fill'
      ? { laws: laws.filter((law, index) => laws.findIndex(other => other.path === law.path
          && other.line === law.line && other.end_line === law.end_line && other.source === law.source) === index), context_notes: contextNotes }
      : null;
    return {
      seen: { calls, called_by: calledBy, laws, datatypes,
        imports: primary.imports.map(({ module, alias }) => ({ module, alias })),
        context_notes: contextNotes },
      provenance,
      builtin: { node: node(primary, declaration),
        methods: analysis.declarations.map(decl => node(primary, decl)),
        imports: primary.imports.map(ref => ({ name: ref.imported_name, alias: ref.alias ?? ref.imported_name, module: ref.module })),
        callees: calleeNodes, callers: callerNodes,
        ...(pairedLawContext ? { paired_law_context: pairedLawContext } : {}) },
    };
  }
  return {
    forUnit(name) {
      if (!contexts.has(name)) contexts.set(name, contextFor(name));
      return contexts.get(name);
    },
  };
}
