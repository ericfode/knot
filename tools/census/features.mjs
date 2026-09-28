import { term_lower, NAT_LITERAL_MAX } from '../../vendor/bend-parser/bend.mts';

export const CLASSES = {
  'imports.base': 'Pinned Base import.',
  'imports.local': 'Relative local module import.',
  'imports.package': 'Content-addressed package import.',
  'types.type': 'Affine Type kind.',
  'types.data': 'Reusable Data kind.',
  'types.base': 'Base type or type-level definition in a signature/annotation.',
  generics: 'Datatype/type parameters or parameterized datatype applications.',
  dependent: 'A type refers to an earlier bound parameter.',
  fields: 'Non-nullary constructor declaration, construction or pattern.',
  'quantities.affine': 'Affine binder.',
  'quantities.erased': 'Erased binder.',
  'quantities.reusable': 'Reusable binder.',
  'quantities.arguments': 'Quantity literal/argument.',
  'quantities.polymorphic': 'Quant parameter or computed kind/quantity meet.',
  'literals.u32': 'U32 literal.',
  'literals.nat': 'Nat literal or numeric Nat pattern.',
  'literals.f32': 'F32 literal.',
  'literals.char': 'Char literal.',
  'literals.string': 'String literal.',
  'literals.list': 'List literal sugar.',
  'literals.tuple': 'Tuple literal sugar.',
  'literals.array': 'Array literal sugar.',
  lambdas: 'Expression lambda (includes do-notation generated closures).',
  captures: 'Expression lambda references a surrounding local binder.',
  'higher-order': 'Function-valued parameter in a definition signature.',
  'calls.variable': 'Application headed by a bound variable.',
  'calls.partial': 'Named definition applied to fewer than its declared parameters.',
  'function-values': 'Named non-nullary definition used as a value.',
  calls: 'Application or explicit zero-argument call.',
  'calls.offload': 'Explicit GPU offload call f!(...).',
  recursion: 'Direct reference to this declaration from its body.',
  matches: 'Pattern match.',
  'matches.multi': 'More than one scrutinee in a single match.',
  'patterns.nested': 'Constructor pattern contains a constructor pattern.',
  'patterns.wildcard': 'Wildcard pattern.',
  'patterns.variable': 'Named pattern binder.',
  bindings: 'Local binding.',
  'bindings.parallel': 'Parallel binding of multiple values.',
  templates: 'Template declaration or reference to a template.',
  laws: 'Law declaration.',
  proofs: 'Law fill or proof term.',
  equality: 'Equality type.',
  rewrites: 'Equality elimination/rewrite.',
  io: 'Reference to IO or File operations/types.',
  arrays: 'Reference to Base Array or its constructors/operations.',
  foreign: 'Foreign definition.',
  unsafe: 'Unsafe definition.',
  holes: 'Hole term.',
  annotations: 'Explicit term type annotation.',
  constructors: 'Constructor construction or pattern.',
};

export const sorted = xs => [...new Set(xs)].sort();
export function children(node) {
  if (!node || typeof node !== 'object') return [];
  return Object.entries(node).filter(([k]) => !['s', 'q'].includes(k))
    .flatMap(([, v]) => Array.isArray(v) ? v : [v])
    .filter(v => v && typeof v === 'object');
}
export function walk(node, visit) {
  if (!node || typeof node !== 'object') return;
  visit(node);
  for (const child of children(node)) walk(child, visit);
}
export function head(node) {
  while (node?.$ === 'App' || node?.$ === 'Ann') node = node.$ === 'App' ? node.f : node.x;
  return node?.$ === 'Var' && node.v ? head(node.v) : node;
}
export function telescope(type) {
  const result = [];
  for (let t = type; t?.$ === 'All'; t = t.B) result.push(t);
  return result;
}

export function freeVariables(lambda) {
  const used = new Map(), bound = new Set([lambda.i]);
  walk(lambda.f, n => {
    if (n.$ === 'Var' && !n.v) used.set(n.i, n.k);
    if (['Lam', 'All', 'PVar'].includes(n.$)) bound.add(n.i);
    if (n.$ === 'Let') n.i.forEach(i => bound.add(i));
  });
  return sorted([...used].filter(([i]) => !bound.has(i)).map(([, k]) => k));
}

export function classify(declaration, book) {
  const { body, signatures, key, kind, source } = declaration;
  const tld = book.tlds[key], features = new Set(), references = new Set(), typeReferences = new Set();
  const captures = [];
  const calledHeads = new Set(declaration.calls.map(head));
  const add = f => {
    if (!Object.hasOwn(CLASSES, f)) throw Object.assign(new Error(`Unsupported feature: ${f}`), { outcome: 'Unsupported' });
    features.add(f);
  };
  const quantity = q => {
    if (q) add({ None: 'quantities.erased', Lone: 'quantities.affine', Many: 'quantities.reusable' }[q.$]);
  };
  if (kind === 'law') add('laws');
  if (kind === 'law_fill') add('proofs');
  if (kind === 'foreign_definition') add('foreign');
  if (tld?.u) add('unsafe');
  if (tld?.x > 0) add('templates');
  if (kind === 'datatype') {
    if (tld.n) add('generics');
    if (tld.c.some(c => c.n)) add('fields');
  }
  const name = (k, inType = false) => {
    if (!k) return;
    references.add(k);
    if (inType) typeReferences.add(k);
    if (/^(IO|File)(\.|$)/.test(k)) add('io');
    if (/^Array(\.|$)/.test(k) || ['ALeaf', 'ANode'].includes(k)) add('arrays');
    if (book.tlds[k]?.x > 0) add('templates');
  };
  const inspect = (node, inType = false, asCallee = false) => {
    if (!node || typeof node !== 'object') return;
    const spelling = node.s ? source.slice(node.s.beg, node.s.end) : '';
    switch (node.$) {
      case 'Var':
        if (inType && !node.v) add('dependent');
        if (node.v) inspect(node.v, inType, asCallee);
        return;
      case 'Ref':
        name(node.k, inType);
        if (node.b === true) add('calls.offload');
        if (!inType && !asCallee && !calledHeads.has(node) && book.tlds[node.k]?.n > 0 && book.tlds[node.k]?.$ === 'Def') add('function-values');
        if (inType && book.tlds[node.k]?.b) add('types.base');
        return;
      case 'ADT':
        name(node.k, true);
        if (book.tlds[node.k]?.b) add('types.base');
        if (node.x.length) add('generics');
        if (node.x.some(x => x.$ === 'Qua')) add('quantities.arguments');
        break;
      case 'All':
        quantity(node.q);
        if (node.A.$ === 'All') add('higher-order');
        if (node.A.$ === 'Typ') add('generics');
        break;
      case 'Typ':
        if (node.g.$ === 'Qua') add(node.g.q.$ === 'Many' ? 'types.data' : 'types.type');
        else add('quantities.polymorphic');
        break;
      case 'Qnt': case 'Min': add('quantities.polymorphic'); break;
      case 'Qua': if (spelling.startsWith('&')) add('quantities.arguments'); return;
      case 'App': {
        add('calls');
        const h = head(node), args = []; let f = node;
        while (f.$ === 'App') { args.unshift(f.x); f = f.f; }
        if (h?.$ === 'Var') add('calls.variable');
        if (h?.$ === 'Ref' && book.tlds[h.k]?.$ === 'Def' && args.length < book.tlds[h.k].n) add('calls.partial');
        if (h?.k === 'Array.new' && spelling.startsWith('[')) add('literals.array');
        inspect(f, inType, true); args.forEach(arg => inspect(arg, inType));
        return;
      }
      case 'Lam': {
        add('lambdas');
        quantity(node.q);
        const names = freeVariables(node);
        if (names.length) { add('captures'); captures.push({ offset: node.s?.beg ?? null, names }); }
        break;
      }
      case 'Match':
        add('matches');
        if (node.e.length > 1) add('matches.multi');
        break;
      case 'Mat': case 'Efq': add('matches'); break;
      case 'Local':
        add('bindings'); quantity(node.q);
        if (node.k.length > 1) add('bindings.parallel');
        break;
      case 'Let':
        add('bindings'); node.q.forEach(quantity);
        if (node.k.length > 1) add('bindings.parallel');
        break;
      case 'PVar':
        add(node.k === '_' ? 'patterns.wildcard' : 'patterns.variable'); quantity(node.q);
        break;
      case 'PCtr':
        if (node.x.some(x => x.$ === 'PCtr')) add('patterns.nested');
        if (/^\d+n/.test(spelling)) add('literals.nat');
        // falls through
      case 'Ctr':
        name(node.k); add('constructors');
        if (node.x.length) add('fields');
        if (node.k === 'Chr' && spelling.startsWith("'")) { add('literals.char'); return; }
        if (spelling.startsWith('[')) add('literals.list');
        if (node.k === 'Tuple' && spelling.startsWith('(')) add('literals.tuple');
        break;
      case 'Lit': add('literals.' + node.k.toLowerCase()); return;
      case 'Rfl': add('proofs'); break;
      case 'Eql': add('equality'); break;
      case 'Rwt': add('rewrites'); add('proofs'); break;
      case 'Hol': add('holes'); break;
      case 'Ann':
        add('annotations'); inspect(node.T, true); inspect(node.x, inType, asCallee); return;
      case 'Sub': break;
      default:
        if (node.$ !== undefined) throw Object.assign(new Error(`Unsupported AST node: ${node.$}`), { outcome: 'Unsupported' });
    }
    for (const child of children(node)) inspect(child, inType || node.$ === 'All');
  };
  for (const signature of signatures) inspect(signature, true);
  inspect(body);
  for (const call of declaration.calls) {
    add('calls');
    if (head(call)?.$ === 'Ref') name(head(call).k);
    else if (head(call)?.$ === 'Var') add('calls.variable');
  }
  const bodyRefs = new Set();
  walk(body, n => { if (n.$ === 'Ref') bodyRefs.add(n.k); });
  if (bodyRefs.has(key)) add('recursion');
  return { features: sorted(features), references: sorted(references), type_references: sorted(typeReferences), captures };
}

// Runtime dependency over-approximation. The parser owns desugaring and identity;
// this walk does not check/evaluate terms or choose reachable branches.
export function executionReferences(body, book) {
  const refs = new Set(), types = new Set(), dynamic = new Set();
  const visit = n => {
    if (!n || typeof n !== 'object') return;
    switch (n.$) {
      case 'Ref': refs.add(n.k); return;
      case 'Var': if (n.v) visit(n.v); return;
      case 'Ann': visit(n.x); return;
      case 'Rwt': visit(n.f); return;
      case 'All': case 'ADT': case 'Typ': case 'Qnt': case 'Qua': case 'Min':
      case 'Eql': case 'Rfl': case 'Hol': case 'PVar': return;
      case 'Lit':
        types.add(n.k);
        // Pinned comp.ts lit_call lowers large Nat literals through U32.to_nat.
        if (n.k === 'Nat' && n.v > NAT_LITERAL_MAX) refs.add('U32.to_nat');
        return;
      case 'PCtr': types.add(n.k); n.x.forEach(visit); return;
      case 'App': {
        const args = []; let f = n;
        while (f.$ === 'App') { args.unshift(f.x); f = f.f; }
        const h = head(f), tld = h?.$ === 'Ref' ? book.tlds[h.k] : null;
        const tele = tld ? telescope(term_lower(tld.T)) : [];
        if (h?.$ === 'Var') dynamic.add(h.k);
        visit(f);
        args.forEach((arg, i) => { if (i < (tld?.x ?? 0) || tele[i]?.q.$ !== 'None') visit(arg); });
        return;
      }
      case 'Ctr': {
        types.add(n.k);
        const ctr = book.ctrs[n.k];
        const tele = ctr ? telescope(term_lower(ctr.T)).slice(-ctr.n || Infinity) : [];
        n.x.forEach((arg, i) => { if (tele[i]?.q.$ !== 'None') visit(arg); });
        return;
      }
      case 'Local':
        if (n.q.$ !== 'None') n.v.forEach(visit);
        visit(n.f); return;
      case 'Let':
        n.v.forEach((v, i) => { if (n.q[i].$ !== 'None') visit(v); });
        visit(n.f); return;
      case 'Match':
        n.e.forEach(visit); n.r.forEach(r => { r.p.forEach(visit); visit(r.f); }); return;
      case 'Lam': visit(n.f); return;
      case 'Mat': types.add(n.k); visit(n.h); visit(n.m); return;
      case 'Efq': return;
      default: throw Object.assign(new Error(`Unsupported execution node: ${n.$}`), { outcome: 'Unsupported' });
    }
  };
  visit(body);
  return { references: sorted(refs), types: sorted(types), dynamic_calls: sorted(dynamic) };
}
