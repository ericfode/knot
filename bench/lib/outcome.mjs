// A process failure is not a source-language rejection. Require the exit and
// diagnostic to agree; retain the complete process record in the caller.
export function outcome(record) {
  if (record.error === 'ETIMEDOUT') return { classification: 'Exhausted', phase: 'host', code: 'timeout' };
  if (record.error || record.signal) return { classification: 'HostFailure', phase: 'process', code: record.error || record.signal };
  const classes = { 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure' };
  const diagnostic = record.stderr || record.stdout;
  if (record.exit === 0) return { classification: 'Success' };
  const [classification, phase, code] = diagnostic.split(/\t|\n/);
  if (classes[record.exit] === classification && phase && code) return { classification, phase, code };
  return { classification: 'HostFailure', phase: 'process', code: `unclassified-exit-${record.exit}` };
}

export function assertSameOutcome(a, b, name) {
  if (JSON.stringify(outcome(a)) !== JSON.stringify(outcome(b))) throw new Error(`${name}: compiler lanes disagree on classification`);
}
