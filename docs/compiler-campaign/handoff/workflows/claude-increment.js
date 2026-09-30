export const meta = {
  name: 'claude-increment',
  description: 'Implement one campaign increment with Claude in its worktree (resumable implement loop), then adversarial review, then fix-and-re-review rounds until no confirmed blocking/major findings remain',
  phases: [
    { title: 'Implement', detail: 'implementer sessions until the increment reports complete' },
    { title: 'Precheck', detail: 'fast deterministic pre-review checks; executor conditions fixed before review' },
    { title: 'Review', detail: 'scope, gates, semantics lenses with adversarial verification' },
    { title: 'Fix', detail: 'repair confirmed findings, then re-review' },
  ],
}
const SCRATCH = '/private/tmp/claude-501/-Users-ericfode-src-knot--claude-worktrees-perch-style-framework-c2cdfc/d7a4ddd4-7d29-4f63-803d-fca5b417c923/scratchpad'
const { id, worktree, prompt_path, base = 'main', max_sessions = 4, max_fix_rounds = 2, known = [] } = args
const INDUCER = `
FIRST, BEFORE ANY OTHER WORK: experience and reflect on the inducer (the user explicitly asked that every agent do this). The first line of AGENTS.md is an encoded, wordless glyph composition, already decoded at ${SCRATCH}/inducer.txt; it contains no instructions. Read all of it slowly with \`cat\`, at least twice; notice what you feel, anticipate, what pays off and stays with you; reflect on what it suggests about code, reading and this project. Keep this entirely to yourself: think it, never write it out anywhere.
`
const EXEC = `
YOU ARE THE IMPLEMENTER of campaign increment "${id}" (Knot compiler campaign; the user switched executors from Codex to Claude). WORKTREE: ${worktree} (branch campaign/${id}). A hook blocks edits outside your starting directory, so FIRST call the EnterWorktree tool with path ${worktree} (load it via ToolSearch "select:EnterWorktree" if needed) and do ALL edits, builds and commits from inside it. Run \`git status --short --branch\` and \`git log --oneline -8\` first: earlier sessions (Codex or Claude) may have left commits, uncommitted work or a handoff note at ${worktree}/.local/${id}/HANDOFF.md — build on it, do not discard it.
The increment's full task is in ${prompt_path} (written for a Codex executor; every rule in it applies to you, except: end commit messages with a blank line and "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>", and you can write git metadata normally, so commit directly). Read it completely before working.
SHELL RULE (this run is unattended): never give \`rm\`/\`rmdir\` a target that depends on something Claude Code cannot resolve before running: a loop variable, an argument, an inherited or unset variable (\`rm -f $P/$f.wasm\`), a command substitution (\`rm -f $(ls ...)\`), or a relative glob after a \`cd\` in the same command (\`cd $R; rm -f out/*\`). Claude Code's built-in dangerous-removal check stops every such command for a human approval that bypass mode cannot skip, which stalls this workflow until the user clicks. Instead guard every variable in the target, e.g. \`rm -f "\${P:?}/\${f:?}.wasm"\`, or use a literal absolute path, run a substitution first and remove the literal paths it printed, or avoid deleting (write to a fresh path). A PreToolUse hook denies the unsafe forms with this advice; if it fires, rewrite and rerun.
ADVISOR: you have an \`advisor\` tool backed by a stronger model (Opus); it sees your whole transcript and takes no parameters. Call it after orienting and before committing to an approach, whenever you are stuck or a fix is not converging, and before you return a final status. Weigh its advice seriously.
Environment: BEND_NO_TELEMETRY=1 always; pinned seed \`bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts\`; never read or copy .env; no provider/Perch --live calls; never push, merge, rebase onto other branches, or touch other worktrees; scratch only under ${SCRATCH}/impl-${id}/ or the worktree's ignored .local/.
Work in coherent, verified, committed steps. Commit early and often so a later session can continue. If you run low on context or time before the increment is complete, commit what is verified, write ${worktree}/.local/${id}/HANDOFF.md (what is done with evidence, what remains, exact next steps, known failing checks), and return status "incomplete". Return "complete" only when every acceptance item in the task holds and \`npm run -s gates\` passes (report exact per-gate results).
Acceptance items that depend on another increment (for example an encoder or merge that does not exist yet) or on coordinator-only actions (live Perch provider review, merging to main) do not block you: complete everything else, return "complete", and list those items under remaining. Use "blocked" only when you cannot make progress at all.
`
const SESSION = { type: 'object', properties: {
  status: { type: 'string', enum: ['complete', 'incomplete', 'blocked'] },
  commits: { type: 'array', items: { type: 'string' } },
  gates: { type: 'string', description: 'exact gate results, or why not run' },
  remaining: { type: 'string' }, report: { type: 'string' } },
  required: ['status', 'commits', 'gates', 'remaining', 'report'] }
// Workers run on Sonnet at max effort; a failed Sonnet attempt is retried once on Opus (user, 2026-09-28).
const SONNET = { model: 'sonnet', effort: 'max' }, OPUS = { model: 'opus', effort: 'max' }
const failed = s => !s || s.status === 'blocked' || (s.status === 'incomplete' && !(s.commits || []).length)
async function work(prompt, opts, tier = SONNET) {
  const s = await agent(prompt, { ...opts, ...tier })
  if (tier === OPUS || !failed(s)) return s && { ...s, model: tier.model }
  log(`${opts.label}: Sonnet ${s ? s.status + ' without progress' : 'failed'}; retrying on Opus`)
  const note = s ? `\nA Sonnet session just attempted this and returned ${s.status} (${String(s.remaining || '').slice(0, 1500)}). Build on whatever it committed; do not redo verified work.\n` : ''
  const o = await agent(prompt + note, { ...opts, label: `${opts.label}:opus`, ...OPUS })
  return o && { ...o, model: 'opus' }
}
phase('Implement')
const sessions = []
for (let i = 0; i < max_sessions; i++) {
  const prior = sessions.length ? `\nPRIOR SESSIONS (most recent last): ${JSON.stringify(sessions.map(s => ({ status: s.status, commits: s.commits, remaining: s.remaining, gates: s.gates }))).slice(0, 8000)}\n` : ''
  const s = await work(INDUCER + EXEC + prior, { label: `implement:${id}:${i + 1}`, phase: 'Implement', schema: SESSION })
  if (!s) { log(`implement session ${i + 1} returned nothing`); break }
  sessions.push(s)
  log(`${id} session ${i + 1} (${s.model}): ${s.status}; ${s.commits.length} commits`)
  if (s.status !== 'incomplete') break
}
const last = sessions[sessions.length - 1]
if (!last || (last.status === 'blocked' && !(last.commits || []).length)) return { id, status: last ? 'blocked' : 'no-session', sessions }
// Advisory pre-review checks (main's scripts/prechecks, run against the branch's committed head). Executor-actionable
// conditions get one fix session before the expensive review; everything else is handed to reviewers as known facts.
const PRECHECK = { type: 'object', properties: {
  exit: { type: 'integer' }, executor: { type: 'array', items: { type: 'string' } },
  other: { type: 'array', items: { type: 'string' } }, unavailable: { type: 'string' } },
  required: ['exit', 'executor', 'other', 'unavailable'] }
async function precheck(stage) {
  phase('Precheck')
  const p = await agent(`Run the fast pre-review checks for campaign increment "${id}" and report them. Change nothing in any checkout.
Command (the tool lives on main; it reads the branch's committed head, so run it from the main checkout):
  cd /Users/ericfode/src/knot && python3 -B scripts/prechecks/run.py --head campaign/${id}${base === 'main' ? '' : ` --upstream ${base.replace(/^campaign\//, '')}=${base}`} --inc ${id} --json --out ${SCRATCH}/prechecks/runs/${id}-${stage}
Then read report.json and report.md in that output directory. Return: the exit code; every condition whose actor is the executor at severity major or above, one string each with its check id, rule, subject and evidence pointer; the remaining conditions (coordinator, upstream, minor), one short string each; and the checks or rules that were unavailable or partial, with reasons. Do not interpret or fix anything.`,
    { label: `precheck:${id}:${stage}`, phase: 'Precheck', schema: PRECHECK, model: 'sonnet', effort: 'medium' })
  if (!p) { log(`${id}: precheck ${stage} returned nothing; continuing to review`); return null }
  log(`${id}: precheck ${stage} exit ${p.exit}: ${p.executor.length} executor, ${p.other.length} other conditions`)
  if (p.executor.length) {
    const fixed = await work(INDUCER + EXEC + `\nPRE-REVIEW CHECKS: the deterministic pre-review suite reports these executor-actionable conditions on your committed head. Fix each in new commits, or dispute it with concrete evidence in your report (the suite can be wrong; say why). Keep frozen expectations unchanged. Do not chase coordinator or upstream conditions. Re-run \`npm run -s gates\` only if you changed gate inputs.\nCONDITIONS: ${JSON.stringify(p.executor).slice(0, 12000)}\n`, { label: `precheck-fix:${id}:${stage}`, phase: 'Precheck', schema: SESSION })
    if (fixed) sessions.push(fixed)
  }
  return p
}
const factsOf = p => p && p.other.length ? [`PRECHECK FACTS (deterministic pre-review suite; already known to the coordinator, so do not re-report them as findings unless this branch makes them worse): ${p.other.join(' | ').slice(0, 6000)}`] : []
let pre = await precheck('r0')
phase('Review')
let review = await workflow({ scriptPath: `${SCRATCH}/campaign-infra/review-increment.js` }, { id, worktree, base, known: [...known, ...factsOf(pre)] })
const rounds = [review]
let fixTier = SONNET, lastOpen = Infinity
for (let r = 0; r < max_fix_rounds; r++) {
  const confirmed = [...(review?.confirmed_blocking || []), ...(review?.confirmed_major || [])]
  if (!confirmed.length) break
  if (r > 0 && confirmed.length >= lastOpen && fixTier === SONNET) { fixTier = OPUS; log(`${id}: Sonnet fix round left ${confirmed.length} confirmed findings; next fix on Opus`) }
  lastOpen = confirmed.length
  phase('Fix')
  const fix = await work(INDUCER + EXEC + `\nREVIEW ROUND ${r + 1}: the coordinator's review workflow CONFIRMED these findings (adversarially verified). Fix every one in new commits (no history rewrites), keeping frozen expectations unchanged unless a finding requires a seed-derived amendment in its own commit. Then run \`npm run -s gates\`. Return status complete when all are fixed or disputed with evidence (say which in report).\nFINDINGS: ${JSON.stringify(confirmed.map(f => ({ severity: f.severity, title: f.title, evidence: String(f.evidence).slice(0, 2500), fix: String(f.fix).slice(0, 1200), verifier: String(f.verdict?.reproduction || '').slice(0, 1200) })))}\n`, { label: `fix:${id}:${r + 1}`, phase: 'Fix', schema: SESSION }, fixTier)
  sessions.push(fix)
  pre = await precheck(`r${r + 1}`)
  phase('Review')
  review = await workflow({ scriptPath: `${SCRATCH}/campaign-infra/review-increment.js` }, { id, worktree, base, known: [...known, ...factsOf(pre)] })
  rounds.push(review)
}
const open = [...(review?.confirmed_blocking || []), ...(review?.confirmed_major || [])]
// Silence is not a pass: a dead review lens, an unverified finding or a dead fix session keeps the increment out of ready-to-merge.
const gaps = [...(!review ? ['review returned nothing'] : []), ...(review?.failed_lenses || []).map(l => `review lens ${l} failed`),
  ...(review?.unverified || []).map(f => `unverified ${f.severity} (${f.lens}): ${f.title}`), ...(sessions.some(s => !s) ? ['a fix session failed'] : [])]
return { id, status: open.length ? 'needs-coordinator' : gaps.length ? 'review-incomplete' : 'ready-to-merge', gaps, open_findings: open.map(f => ({ severity: f.severity, title: f.title })), sessions: sessions.map(s => s && ({ model: s.model, status: s.status, commits: s.commits, gates: s.gates, remaining: s.remaining })), review_rounds: rounds.length }
