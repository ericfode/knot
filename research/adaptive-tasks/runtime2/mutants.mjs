import assert from 'node:assert/strict';

// Pipeline construction is only type evidence; hardware observations kill these.
export const mutants=[
  {name:'skip-rc-decrement',witness:'shared-tree-release',edits:[
    ['work.w[base+2u]=work.w[base+2u]-1u; // one pending edge releases one count',
     'work.w[base+2u]=work.w[base+2u]; // omitted counted release']]},
  {name:'double-release',witness:'shared-tree-release',edits:[
    ['work.w[base+2u]=work.w[base+2u]-1u; // one pending edge releases one count',
     'work.w[base+2u]=work.w[base+2u]-2u; // release the same pending edge twice']]},
  {name:'capture-moved-twice',witness:'move-once',edits:[
    ['work.w[capture(src)]=0u; // move consumes its unique source slot',
     'work.w[capture(src)]=work.w[capture(dst)]; // copied extraction authority']]},
  {name:'accept-stale-attempt',witness:'cancel-stale-replace',edits:[
    ['if (attempt!=work.w[base] || work.w[base+1u]!=1u)',
     'if (work.w[base+1u]!=1u)']]},
  {name:'nary-completes-twice',witness:'nary-once',edits:[
    ['work.w[base+4u]+=1u; // the transition to ready completes once',
     'work.w[base+4u]+=2u; // repeated completion of the same attempt']]},
  {name:'wrap-offset-overflow',witness:'offset-no-wrap',edits:[
    ['count<=(limit-base)/stride','base+count*stride<=limit']]},
  {name:'branch-swaps-targets',witness:'case-move-yield',mode:'program',edits:[
    ['select(arg(4u),arg(3u),work.w[base+4u]==arg(2u))',
     'select(arg(3u),arg(4u),work.w[base+4u]==arg(2u))']]},
  {name:'zero-quantum-suspends',witness:'case-move-yield',mode:'program',edits:[
    ['if (step.index==0u || work.w[25]==2u || work.w[25]==3u)',
     'if (work.w[25]==2u || work.w[25]==3u)']]},
  {name:'resume-ignores-code',witness:'join-resumes-code',mode:'program',edits:[
    ['if (op==11u) { work.w[24]=work.w[22]; }',
     'if (op==11u) { work.w[24]+=1u; }']]},
  {name:'cleanup-exhaustion-terminal',witness:'cleanup-resumes-program',mode:'program',edits:[
    ['work.w[25]=select(3u,1u,work.w[21]==3u)', 'work.w[25]=3u']]},
];

export function mutate(shader,mutant) {
  let source=shader;
  for (const [anchor,replacement] of mutant.edits) {
    assert.equal(source.split(anchor).length,2,`${mutant.name}: unique mutation anchor`);
    source=source.replace(anchor,replacement);
  }
  return source;
}
