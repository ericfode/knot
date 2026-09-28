import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { compareReceipts } from '../gpu/observations.mjs';

// Expectations fixed from the retained 38-case receipt before harness edits.
const baseline=JSON.parse(await readFile(new URL('../receipts/gpu.json',import.meta.url),'utf8'));
const copy=()=>structuredClone(baseline);

test('the retained inventory compares with itself',()=>{
  assert.equal(compareReceipts(baseline,copy()).cases,38);
});

test('scheduling telemetry and run provenance are not semantic observations',()=>{
  const next=copy();
  next.date='2099-01-01T00:00:00.000Z';
  next.node='different host version';
  next.hashes.runner='changed harness';
  for(const item of next.cases) {
    item.stateSha256='0'.repeat(64);
    item.logicalWorkerMoves+=17;
  }
  assert.equal(compareReceipts(baseline,next).cases,38);
});

test('explicit round budgets agree with the documented legacy schedule',()=>{
  const next=copy();
  next.schema='knot-adaptive-device-receipt-v2';
  next.cases.forEach((item,i)=>{item.maxRounds=i===35?3:i===36?2:512;});
  assert.equal(compareReceipts(baseline,next).cases,38);
});

const changes={
  'finished value':r=>{r.cases[0].result.value++;},
  'exhaustion kind':r=>{r.cases[33].result={kind:'finished',value:226};},
  'exhaustion resource':r=>{r.cases[33].result.resource='rounds';},
  'case omission':r=>{r.cases.pop();},
  'case duplication':r=>{r.cases[1]=structuredClone(r.cases[0]);},
  'case order':r=>{[r.cases[0],r.cases[1]]=[r.cases[1],r.cases[0]];},
  'quantum':r=>{r.cases[0].quantum++;},
  'adaptive mode':r=>{r.cases[0].adaptive=false;},
  'capacity':r=>{r.cases[0].capacity--;},
  'round budget':r=>{r.cases[0].maxRounds=511;},
  'destination ownership':r=>{r.cases[0].allDestinationsPreserved=false;},
  'retirement':r=>{r.cases[0].allNonRootTasksRetired=false;},
  'frontier bounds':r=>{r.cases[0].frontierCapacitySuffixPreserved=false;},
  'frontier canary':r=>{r.cases[0].frontierCanaryPreserved=false;},
  'logical completion order':r=>{r.cases[0].completionOrder.left++;},
  'machine steps':r=>{r.cases[0].machineSteps++;},
  'active counts':r=>{r.cases[0].activeCounts[0]++;},
  'fixture identity':r=>{r.hashes.fixtures='f'.repeat(64);},
  'validation failure':r=>{r.validationErrors++;},
  'fallback adapter':r=>{r.adapter.isFallbackAdapter=true;},
  'host failure':r=>{r.status='HostFailure';},
};
for(const [name,change] of Object.entries(changes))test(`rejects changed ${name}`,()=>{
  const next=copy(); change(next);
  assert.throws(()=>compareReceipts(baseline,next));
});
