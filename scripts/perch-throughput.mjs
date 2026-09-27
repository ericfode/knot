// Bounded work with stable result order. A failure stops admission and drains
// already-started work before callers release snapshots, meters or resources.
export const DEFAULT_PERCH_JOBS = 16;
export const MAX_PERCH_JOBS = 256;

export function perchConcurrency(value = DEFAULT_PERCH_JOBS) {
  const jobs = Number(value);
  if (!Number.isInteger(jobs) || jobs < 1 || jobs > MAX_PERCH_JOBS) {
    throw new Error(`Perch concurrency must be 1..${MAX_PERCH_JOBS}`);
  }
  return jobs;
}

export async function runWorkers(jobs, next, work) {
  perchConcurrency(jobs);
  let failed = false, failure;
  async function worker() {
    while (!failed) {
      try {
        const item = next();
        if (item === undefined) return;
        await work(item);
      } catch (error) { if (!failed) failure = error; failed = true; }
    }
  }
  await Promise.all(Array.from({ length: jobs }, worker));
  if (failed) throw failure;
}

export async function mapConcurrent(items, jobs, work) {
  let cursor = 0;
  const results = new Array(items.length);
  await runWorkers(Math.min(perchConcurrency(jobs), Math.max(1, items.length)),
    () => cursor < items.length ? cursor++ : undefined,
    async index => { results[index] = await work(items[index], index); });
  return results;
}

export async function drainAll(promises) {
  const settled = await Promise.allSettled(promises);
  const failed = settled.find(result => result.status === 'rejected');
  if (failed) throw failed.reason;
  return settled.map(result => result.value);
}

export function limitConcurrent(work, jobs) {
  perchConcurrency(jobs);
  let active = 0;
  const waiting = [];
  return async (...args) => {
    if (active >= jobs) await new Promise(resolve => waiting.push(resolve));
    else active++;
    try { return await work(...args); }
    finally {
      const next = waiting.shift();
      if (next) next();
      else active--;
    }
  };
}

// Preserve the scan's two-entirely-failed-cohorts cutoff in admission order.
// A slow success cannot be overtaken by fast failures to abort a healthy cohort.
export function failureCohorts(width) {
  perchConcurrency(width);
  const pending = new Map();
  let cursor = 0, size = 0, allFailed = true, consecutive = 0;
  return (index, failed) => {
    pending.set(index, failed);
    while (pending.has(cursor)) {
      allFailed &&= pending.get(cursor);
      pending.delete(cursor++);
      if (++size === width) {
        consecutive = allFailed ? consecutive + 1 : 0;
        size = 0; allFailed = true;
        if (consecutive >= 2) return true;
      }
    }
    return false;
  };
}

// Token estimates are pure for a given string. Cache exact text, never object
// identity: request state can acquire additional metadata after construction.
export function memoizeTextCount(count, { characters = 4_000_000, entries = 4096 } = {}) {
  const cache = new Map();
  let retained = 0;
  return text => {
    if (cache.has(text)) {
      const result = cache.get(text);
      cache.delete(text); cache.set(text, result);
      return result;
    }
    const result = count(text);
    if (text.length <= characters && entries > 0) {
      while (cache.size && (cache.size >= entries || retained + text.length > characters)) {
        const oldest = cache.keys().next().value;
        retained -= oldest.length; cache.delete(oldest);
      }
      cache.set(text, result); retained += text.length;
    }
    return result;
  };
}
