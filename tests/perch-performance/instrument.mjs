// Count events in actual compiled execution. No candidate-supplied counters.
import {readFileSync, writeFileSync} from 'node:fs';
import languagePack from '@xberg-io/tree-sitter-language-pack';
const {getParser} = languagePack;
const [, , input, output, metadata] = process.argv;
const source = readFileSync(input);
const tree = getParser('javascript').parse(source.toString());
if (!tree || tree.rootNode().hasError()) throw new Error('Generated JS did not parse');
const edits = [];
const sites = {functions: 0, loops: 0, allocations: 0};
const insert = (pos, text) => edits.push({pos, text});
const instrumentBody = (body, kind) => {
  if (!body) throw new Error('Missing instrumented body');
  const tick = `__gate_tick(${JSON.stringify(kind)});`;
  if (body.kind() === 'statement_block') insert(body.startByte() + 1, tick);
  else {
    insert(body.startByte(), `{${tick}`);
    insert(body.endByte(), '}');
  }
};
function visit(node) {
  const kind = node.kind();
  if (['function_declaration', 'function_expression', 'arrow_function', 'method_definition'].includes(kind)) {
    const body = node.childByFieldName('body');
    sites.functions++;
    if (body.kind() === 'statement_block') instrumentBody(body, 'functions');
    else {
      insert(body.startByte(), '(__gate_tick("functions"),(');
      insert(body.endByte(), '))');
    }
  }
  if (['for_statement', 'for_in_statement', 'while_statement', 'do_statement'].includes(kind)) {
    sites.loops++;
    instrumentBody(node.childByFieldName('body'), 'loops');
  }
  if (kind === 'object' || kind === 'array') {
    sites.allocations++;
    insert(node.startByte(), '(__gate_tick("allocations"),(');
    insert(node.endByte(), '))');
  }
  for (let i = 0; i < node.namedChildCount(); i++) visit(node.namedChild(i));
}
visit(tree.rootNode());
if (!sites.functions || !sites.loops) throw new Error('Missing runtime instrumentation sites');
// Stable reverse ordering preserves nesting when sites share an offset.
edits.sort((a, b) => b.pos - a.pos);
let result = source;
for (const edit of edits) result = Buffer.concat([result.subarray(0, edit.pos), Buffer.from(edit.text), result.subarray(edit.pos)]);
const prelude = `let __gate_counts = {functions:0,loops:0,allocations:0};
let __gate_active = false;
function __gate_tick(kind) { if (__gate_active) { __gate_counts[kind]++; if (__gate_counts.functions + __gate_counts.loops + __gate_counts.allocations > 20000000) throw new Error("operation budget exceeded"); } }
export function __gate_start() { __gate_counts = {functions:0,loops:0,allocations:0}; __gate_active = true; }
export function __gate_stop() { __gate_active = false; return {...__gate_counts}; }
`;
const text = prelude + result.toString();
if (getParser('javascript').parse(text).rootNode().hasError()) throw new Error('Instrumented JS did not parse');
writeFileSync(output, text);
writeFileSync(metadata, JSON.stringify(sites));
