// Content-addressed answers, never source bodies. Each published file is an
// atomic replacement so concurrent invocations observe an old or a new record.
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const hash = value => createHash('sha256').update(value).digest('hex');

export function styleEndpoint(value = 'https://api.typesafe.ai/v1/systemone') {
  let url;
  try { url = new URL(value); } catch { throw new Error('Invalid style provider endpoint'); }
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Invalid style provider endpoint');
  url.hash = '';
  // Only the digest is persisted: URLs can contain private query parameters.
  return { url: url.href, sha256: hash(url.href) };
}

export function createStyleAnswerCache(root, identity) {
  const directory = resolve(root, '.perch/cache/style-v1');
  const stats = { hits: 0, misses: 0, invalid_entries: 0, written: 0, write_failures: 0 };
  const address = (request_sha256, context) => {
    const expected = { ...identity, request_sha256, context_limits: context.limits,
      context_files: context.files.map(file => file.path) };
    return { expected, path: resolve(directory, `${hash(JSON.stringify(expected))}.json`) };
  };
  return {
    stats,
    async read(candidate, request_sha256, validate) {
      const { expected, path } = address(request_sha256, candidate.context);
      try {
        const record = JSON.parse(await readFile(path, 'utf8'));
        if (record.schema !== 1 || JSON.stringify(record.identity) !== JSON.stringify(expected)
            || record.payload_sha256 !== hash(JSON.stringify(record.payload))) throw new Error('Invalid style cache record');
        const saved = record.payload;
        if (typeof saved?.model !== 'string' || !saved.model || typeof saved.evaluated_at !== 'string'
            || saved.provenance?.state_sha256 !== candidate.state_sha256) throw new Error('Invalid style cache identity');
        const answers = validate(saved.answers);
        const { state, ...metadata } = candidate;
        stats.hits++;
        return { ...metadata, model: saved.model, elapsed_ms: saved.elapsed_ms, usage: saved.usage, answers,
          answer_origin: { kind: 'incremental-cache', evaluated_at: saved.evaluated_at,
            request_sha256, endpoint_sha256: identity.endpoint_sha256, requested_model: identity.requested_model,
            provenance: saved.provenance } };
      } catch (error) {
        stats.misses++;
        if (error.code !== 'ENOENT') stats.invalid_entries++;
        return null;
      }
    },
    async write(candidate, request_sha256, row, evaluated_at) {
      const { expected, path } = address(request_sha256, candidate.context);
      const { state, ...provenance } = candidate;
      const payload = { model: row.model, answers: row.answers, elapsed_ms: row.elapsed_ms,
        usage: row.usage, evaluated_at, provenance };
      const record = { schema: 1, identity: expected, payload_sha256: hash(JSON.stringify(payload)), payload };
      const temporary = `${path}.${randomUUID()}.tmp`;
      try {
        await mkdir(directory, { recursive: true, mode: 0o700 });
        await writeFile(temporary, JSON.stringify(record) + '\n', { flag: 'wx', mode: 0o600 });
        await rename(temporary, path);
        stats.written++;
      } catch {
        stats.write_failures++;
      } finally { await rm(temporary, { force: true }).catch(() => {}); }
    },
  };
}
