import assert from 'node:assert/strict';
import test from 'node:test';
import { approvedPolicy, policyViolations, sha256 } from '../census.mjs';

// Literal policy controls fixed before the narrow host-boundary exception.
const file = 'src/path-host.bend';
const identity = sha256('literal host-query declaration');
const entry = {
  file, sha256: identity, imports: [], features: ['foreign'],
  declarations: [{ id: `${file}::inspect:foreign_definition`, features: ['foreign'] }],
};
const exception = { [file]: { sha256: identity, features: ['foreign'] } };
const policy = {
  ...approvedPolicy([entry]), dependency_feature_exceptions: exception,
};
const forbidden = files => policyViolations(files, policy).filter(v => v.includes('forbidden dependency feature'));

test('host foreign query needs an explicit reviewed exception', () => {
  assert.deepEqual(policyViolations([entry], approvedPolicy([entry])),
    [`${file}: forbidden dependency feature foreign`]);
});

test('only the exact source hash receives the foreign exception', () => {
  assert.deepEqual(forbidden([entry]), []);
  assert.deepEqual(forbidden([{ ...entry, sha256: sha256('different host query') }]),
    [`${file}: forbidden dependency feature foreign`]);
});

test('the host exception does not extend to another file', () => {
  const other = 'src/other-host.bend';
  assert.deepEqual(forbidden([{ ...entry, file: other }]),
    [`${other}: forbidden dependency feature foreign`]);
});

test('the host exception leaves other forbidden features in force', () => {
  assert.deepEqual(forbidden([{ ...entry, features: ['foreign', 'unsafe', 'arrays'] }]),
    [`${file}: forbidden dependency feature arrays`, `${file}: forbidden dependency feature unsafe`]);
});
