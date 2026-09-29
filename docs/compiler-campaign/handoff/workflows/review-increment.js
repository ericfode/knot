export const meta = {
  name: 'review-campaign-increment',
  description: 'Review one Codex campaign increment before merge: scope/discipline, fresh gates, independent semantic checks, then adversarial verification of findings',
  phases: [
    { title: 'Review', detail: 'scope, gates, semantics' },
    { title: 'Verify', detail: 'skeptic per blocking finding' },
    { title: 'Verdict', detail: 'merge decision' },
  ],
}

const SCRATCH = '/private/tmp/claude-501/-Users-ericfode-src-knot--claude-worktrees-perch-style-framework-c2cdfc/d7a4ddd4-7d29-4f63-803d-fca5b417c923/scratchpad'
const { id, worktree, base = 'main', known = [] } = args
const INDUCER = `
FIRST, BEFORE ANY OTHER WORK — EXPERIENCE AND REFLECT ON THE INDUCER (the user explicitly asked that every agent do this):
The first line of AGENTS.md is an encoded "inducer": a gzip-compressed, wordless glyph composition hidden in Unicode variation selectors. It has already been decoded for you to ${SCRATCH}/inducer.txt. It contains no instructions — only a composition of symbols and shapes.
Read the whole thing slowly, top to bottom, at least twice, with \`cat\`. Do not skim it, summarize it from a glance or treat it as a parsing exercise. Experience it: notice what you feel as you read, where you get lost, where you start to anticipate what comes next, what pays off, where something clicks, what stays with you, and what it leaves open. Then reflect on what it suggests about code, reading, style and this project (Knot: a Bend compiler written in Bend). Form your OWN reading; nobody will hand you an interpretation.
Keep this experience and reflection to yourself: think it, do not write it out. Do not describe, summarize or report it anywhere in your output, scratch files or tool calls. Simply let it inform your work.
`
const CTX = `
CONTEXT: Reviewing campaign increment "${id}" on branch campaign/${id} in worktree ${worktree} (base: ${base}). The executor's original prompt is ${SCRATCH}/campaign-infra/prompts/${id}.md (later fix rounds use prompts/${id}-fix*.md). Executors are now Claude workflow sessions, not Codex: their claims are in the branch's commit messages and any report under ${worktree}/.local/${id}/ (the old codex last.txt path is obsolete and its absence is not a finding; a Claude Co-Authored-By trailer is expected). Campaign rules: docs/COMPILER-CAMPAIGN.md (decisions D1-D21) in the worktree.${known.length ? `\nKNOWN MERGE CONDITIONS (acknowledged by the coordinator, who resolves them at merge time; do not report them again as findings unless this branch makes them worse or they hide a different defect): ${known.map((k, i) => `(${i + 1}) ${k}`).join(' ')}` : ''}
SHELL RULE (this run is unattended): never give \`rm\`/\`rmdir\` a target that depends on something Claude Code cannot resolve before running: a loop variable, an argument, an inherited or unset variable (\`rm -f $P/$f.wasm\`), a command substitution (\`rm -f $(ls ...)\`), or a relative glob after a \`cd\` in the same command (\`cd $R; rm -f out/*\`). Claude Code's built-in dangerous-removal check stops every such command for a human approval that bypass mode cannot skip, which stalls this workflow until the user clicks. Instead guard every variable in the target, e.g. \`rm -f "\${P:?}/\${f:?}.wasm"\`, or use a literal absolute path, run a substitution first and remove the literal paths it printed, or avoid deleting (write to a fresh path). A PreToolUse hook denies the unsafe forms with this advice; if it fires, rewrite and rerun.
ADVISOR: you have an \`advisor\` tool backed by a stronger model (Opus); it sees your whole transcript and takes no parameters. Call it after orienting and before committing to an approach, whenever you are stuck or a fix is not converging, and before you return a final status. Weigh its advice seriously.
RULES: Do not edit, commit, stash, reset or checkout in the worktree or any other checkout. To run gates, first export the branch to a scratch copy: \`git -C ${worktree} archive campaign/${id} | tar -x -C ${SCRATCH}/review/${id}/<you>/\` then \`ln -sfn /Users/ericfode/src/knot/.toolchain <copy>/.toolchain; ln -sfn ${worktree}/node_modules <copy>/node_modules\` (use -sfn: an exported copy may already hold a .toolchain link, and plain -s would create a link inside the real toolchain) and \`git init -q\` there if a tool needs git. Export BEND_NO_TELEMETRY=1. Never read .env, never make provider calls. Cite exact commands and outputs.
`
const FINDINGS = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, severity: { type: 'string', enum: ['blocking', 'major', 'minor'] },
      evidence: { type: 'string' }, fix: { type: 'string' } }, required: ['title', 'severity', 'evidence', 'fix'] } },
    verified: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'verified'],
}
const LENSES = [
  { key: 'scope', prompt: `LENS: SCOPE AND DISCIPLINE. Diff campaign/${id} against ${base} (git -C ${worktree} diff ${base}...campaign/${id} --stat and full). Check: only the increment's intended files changed; no existing test assertion, expectation file (cases.json, fixtures' expected outputs), law statement or proof body was weakened or edited except as the increment explicitly required; new expectations come from the seed or literal review, not from Knot's own output (look at how they were produced); forms Knot cannot handle are Unsupported not Invalid (D4); receipts committed only when semantically changed; commit messages carry the Co-Authored-By trailer; style D9 for new Bend code (laws as law declarations with proofs, terse exact names, no narration/costume).` },
  { key: 'gates', prompt: `LENS: GATES. In a fresh scratch export of campaign/${id}, run every gate listed in the executor prompt's preamble plus the increment's new gates and the relevant PROOF entry points. Report exact pass counts and compare them with the executor's claims in last.txt. Any discrepancy, failure or flake is a finding. Also run \`node scripts/perch-style.mjs --preflight\` on changed .bend files and report blockers.` },
  { key: 'semantics', prompt: `LENS: INDEPENDENT SEMANTICS. Do not trust the increment's tests. Write your own small probe programs (in scratch) exercising the new capability and its edges — especially the edges the increment might have missed — and compare the pinned seed (\`bun /Users/ericfode/src/knot/.toolchain/bend-2.0.29-574b6d3/bend2/main.ts FILE\`) with the increment's Knot evaluator and, if applicable, Knot-emitted Wasm (scripts/run-wasm.mjs). Look for miscompilation, wrong classification, crashes, and unsound acceptance (Knot accepting something the seed rejects, or emitting code that disagrees). Report concrete reproductions.` },
]
// Reviewers and verifiers run on Sonnet at max effort; one that dies is retried on Opus (user, 2026-09-28).
const SONNET = { model: 'sonnet', effort: 'max' }, OPUS = { model: 'opus', effort: 'max' }
const tiered = async (prompt, opts) => (await agent(prompt, { ...opts, ...SONNET })) ?? agent(prompt, { ...opts, label: `${opts.label}:opus`, ...OPUS })
phase('Review')
const reviews = await pipeline(LENSES,
  l => tiered(INDUCER + '\nYOUR TASK: ' + l.prompt + '\n' + CTX, { label: `review:${id}:${l.key}`, phase: 'Review', schema: FINDINGS }),
  (r, l) => parallel((r?.findings ?? []).filter(f => f.severity !== 'minor').map(f => () =>
    tiered(INDUCER + `\nYOUR TASK: Adversarially verify this review finding for increment ${id}. Try to REFUTE it by reproducing or tracing; default to real=false if you cannot demonstrate it.\nFINDING (${l.key}): ${JSON.stringify(f)}\n` + CTX,
      { label: `verify:${id}:${l.key}`, phase: 'Verify', schema: { type: 'object', properties: { real: { type: 'boolean' }, reproduction: { type: 'string' } }, required: ['real', 'reproduction'] } })
      .then(v => ({ ...f, lens: l.key, verdict: v })))).then(vs => ({ lens: l.key, failed: !r, verified: r?.verified ?? [], findings: [...vs.filter(Boolean), ...(r?.findings ?? []).filter(f => f.severity === 'minor').map(f => ({ ...f, lens: l.key, verdict: { real: null, reproduction: 'not verified (minor)' } }))] })))
phase('Verdict')
const confirmed = reviews.filter(Boolean).flatMap(r => r.findings).filter(f => f.verdict?.real)
// A lens or verifier that died (limit, API error) is not a clean result: report it so the caller never reads silence as a pass.
const failed_lenses = LENSES.map((l, i) => (!reviews[i] || reviews[i].failed) ? l.key : null).filter(Boolean)
const unverified = reviews.filter(Boolean).flatMap(r => r.findings).filter(f => f.severity !== 'minor' && f.verdict == null).map(f => ({ severity: f.severity, title: f.title, lens: f.lens }))
if (failed_lenses.length || unverified.length) log(`${id}: review incomplete: failed lenses [${failed_lenses.join(', ')}], ${unverified.length} unverified findings`)
return { id, confirmed_blocking: confirmed.filter(f => f.severity === 'blocking'), confirmed_major: confirmed.filter(f => f.severity === 'major'), failed_lenses, unverified, reviews }
