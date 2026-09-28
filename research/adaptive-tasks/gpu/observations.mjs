import assert from 'node:assert/strict';

const CASES=38;
const ignoredCaseFields=['stateSha256','logicalWorkerMoves'];

function observation(receipt) {
  assert.equal(receipt.status,'pass','receipt did not pass');
  assert.equal(receipt.adapter.backend,'metal','receipt is not a Metal device run');
  assert.equal(receipt.adapter.isFallbackAdapter,false,'fallback is not hardware evidence');
  assert.equal(receipt.cases.length,CASES,'case inventory changed');
  assert(!receipt.schema||receipt.schema==='knot-adaptive-device-receipt-v2','unknown receipt schema');
  assert.equal(receipt.shaderCompilationErrors,0,'shader compilation failed');
  assert.equal(receipt.validationErrors,0,'device validation failed');
  assert.equal(receipt.unsupportedOpcodeRejected,true);
  assert.equal(receipt.invalidIntegerRejected,true);
  const cases=receipt.cases.map((item,index)=>{
    const result=structuredClone(item);
    // The original 38-case receipt predates maxRounds. Its only overrides
    // are the zero-quantum and short serial-frame controls at indices 35/36.
    if(result.maxRounds===undefined) {
      assert(!receipt.schema,'round budget missing from versioned receipt');
      if(index===35) {
        assert.equal(item.name,'ordered'); assert.equal(item.quantum,0);
      }
      if(index===36) {
        assert.equal(item.name,'serial_frames'); assert.equal(item.rounds,2);
      }
      result.maxRounds=index===35?3:index===36?2:512;
    }
    assert(Number.isInteger(result.maxRounds)&&result.maxRounds>0&&result.maxRounds<=512);
    for(const field of ignoredCaseFields)delete result[field];
    return result;
  });
  return {fixtureSha256:receipt.hashes.fixtures,cases,dispatches:receipt.dispatches,
    shaderCompilationErrors:receipt.shaderCompilationErrors,validationErrors:receipt.validationErrors,
    unsupportedOpcodeRejected:receipt.unsupportedOpcodeRejected,
    invalidIntegerRejected:receipt.invalidIntegerRejected,performanceClaim:receipt.performanceClaim};
}

// This compares independently obtained observations; it does not execute a model.
export function compareReceipts(baseline,current) {
  assert.deepEqual(observation(current),observation(baseline),'semantic device observations changed');
  return {cases:CASES,ignoredCaseFields};
}
