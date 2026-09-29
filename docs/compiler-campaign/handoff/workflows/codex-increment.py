#!/usr/bin/env python3
"""Run one Knot campaign increment entirely on Codex: implement, precheck, a three-lens review with
adversarial verification, then fix-and-re-review rounds. No Claude agent is involved.

    codex-increment.py --id nest --worktree W --prompt P.md [--base main] [--known K.json] [--run DIR]
                       [--max-sessions 3] [--max-fix-rounds 2] [--jobs 4] [--review-only]

Every Codex call is cached under <run>/calls/<label>.json with its prompt hash, so rerunning the same
command after a crash replays finished calls and continues. The result is <run>/summary.json and summary.md.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, subprocess, sys, threading, time
from pathlib import Path

KNOT = '/Users/ericfode/src/knot'
MAIN_DOCS = f'{KNOT}/docs'
MODEL = os.environ.get('KNOT_CODEX_MODEL', 'gpt-6.1-sol')
SEED = 'bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
TRAILER = 'Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>'

def obj(props, req=None):
    return {'type': 'object', 'additionalProperties': False, 'properties': props, 'required': req or list(props)}
S = {'type': 'string'}
SESSION = obj({'status': {'type': 'string', 'enum': ['complete', 'incomplete', 'blocked']},
               'commits': {'type': 'array', 'items': S}, 'gates': S, 'remaining': S, 'report': S})
FINDINGS = obj({'findings': {'type': 'array', 'items': obj({'title': S, 'severity': {'type': 'string', 'enum': ['blocking', 'major', 'minor']},
                                                            'evidence': S, 'fix': S})},
                'verified': {'type': 'array', 'items': S}})
VERDICT = obj({'real': {'type': 'boolean'}, 'reproduction': S})

ap = argparse.ArgumentParser()
ap.add_argument('--id', required=True); ap.add_argument('--worktree', required=True); ap.add_argument('--prompt', required=True)
ap.add_argument('--base', default='main'); ap.add_argument('--known', help='JSON list of acknowledged merge conditions')
ap.add_argument('--run'); ap.add_argument('--max-sessions', type=int, default=3); ap.add_argument('--max-fix-rounds', type=int, default=2)
ap.add_argument('--jobs', type=int, default=4); ap.add_argument('--review-only', action='store_true')
a = ap.parse_args()
ID, WT, BASE = a.id, a.worktree.rstrip('/'), a.base
RUN = Path(a.run or f'/private/tmp/knot-codex/{ID}'); (RUN / 'calls').mkdir(parents=True, exist_ok=True)
(RUN / 'logs').mkdir(exist_ok=True); (RUN / 'scratch').mkdir(exist_ok=True)
KNOWN = json.load(open(a.known)) if a.known else []
PROMPT = str(Path(a.prompt).resolve())
SLOTS = threading.Semaphore(a.jobs)
LOG = open(RUN / 'progress.log', 'a')

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {ID}: {msg}"
    print(line, flush=True); LOG.write(line + '\n'); LOG.flush()

ENV = dict(os.environ, BEND_NO_TELEMETRY='1', npm_config_cache=str(RUN / 'npm-cache'), BUN_RUNTIME_TRANSPILER_CACHE_PATH='0')

def codex(label, prompt, schema, cwd):
    """One cached Codex session; returns the parsed final JSON or None."""
    h = hashlib.sha256((prompt + json.dumps(schema) + cwd).encode()).hexdigest()[:16]
    cache = RUN / 'calls' / f'{label}.json'
    if cache.exists():
        c = json.loads(cache.read_text())
        if c.get('hash') == h and c.get('result') is not None:
            return c['result']
    sch = RUN / 'calls' / f'{label}.schema.json'; sch.write_text(json.dumps(schema))
    out = RUN / 'calls' / f'{label}.last.json'
    for attempt in (1, 2):
        with SLOTS:
            log(f'start {label} (attempt {attempt})'); t = time.time()
            with open(RUN / 'logs' / f'{label}.log', 'a') as lf:
                p = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', 'model_reasoning_effort="max"', '-c', 'service_tier="fast"',
                                    '-s', 'danger-full-access',  # workspace-write keeps .git read-only, so commits fail (smoke test 2026-09-29)
                                    '-C', cwd, '--skip-git-repo-check', '--output-schema', str(sch), '-o', str(out), '-'],
                                   input=prompt, text=True, stdout=lf, stderr=subprocess.STDOUT, env=ENV)
        try:
            result = json.loads(out.read_text())
        except Exception:
            result = None
        log(f'end {label}: exit {p.returncode}, {int(time.time() - t)} s, {"ok" if result is not None else "no result"}')
        if result is not None:
            cache.write_text(json.dumps({'hash': h, 'result': result}))
            return result
    return None

ORIENT = f"""Knot is a Bend 2 compiler written in Bend. Read AGENTS.md first. Its first line is an encoded, wordless glyph composition (the "inducer"): experience it and reflect on it privately, and never write about it anywhere. Then read README.md, {MAIN_DOCS}/COMPILER-CAMPAIGN.md (the campaign rules and decisions D1–D26, on main) and {MAIN_DOCS}/compiler-campaign/COORDINATOR-STATE.md (the coordinator's standing rulings and the state of every increment).
Environment: always export BEND_NO_TELEMETRY=1. The pinned seed (reference implementation) is `{SEED}` (.toolchain links to the main checkout's ignored copy). Never read or copy any .env file. Make no provider or live Perch calls. Never push, merge, rebase onto other branches or touch any worktree other than your own. Put scratch files under {RUN}/scratch/ or the worktree's ignored .local/.
"""
EXEC = ORIENT + f"""
YOU ARE THE IMPLEMENTER of campaign increment "{ID}". Your working directory is its git worktree {WT} (branch campaign/{ID}). Do all edits, builds and commits there. Start with `git status --short --branch` and `git log --oneline -10`: earlier sessions (Codex or Claude) may have left commits, uncommitted work or a handoff note at {WT}/.local/{ID}/HANDOFF.md. Build on them; never discard them.
The increment's full task is in {PROMPT}. Read it completely: every rule in it applies. Where it names another co-author trailer, use this one instead: end every commit message with a blank line and "{TRAILER}".
Work in coherent, verified, committed steps, with explicit paths (never `git add -A`). If you run low on context or time before the increment is complete, commit what is verified, write {WT}/.local/{ID}/HANDOFF.md (what is done with evidence, what remains, exact next steps, known failing checks) and return status "incomplete". Return "complete" only when every acceptance item holds and `npm run -s gates` passes; report the exact per-gate results. Items that depend on another increment, or on coordinator-only actions (live Perch, merging to main, refreshing shared receipts), do not block you: complete everything else, return "complete" and list them under remaining. Use "blocked" only when you cannot make progress at all.
Your final message must be the JSON object the output schema describes."""

def ctx():
    k = ''.join(f' ({i + 1}) {x}' for i, x in enumerate(KNOWN))
    return f"""
CONTEXT: You are reviewing campaign increment "{ID}", on branch campaign/{ID} in worktree {WT} (base: {BASE}). The executor's task is {PROMPT}; its claims are in the branch's commit messages and any report under {WT}/.local/{ID}/.{(' KNOWN CONDITIONS, acknowledged by the coordinator, who resolves them at merge: do not report them again unless this branch makes them worse or they hide a different defect:' + k) if k else ''}
RULES: Do not edit, commit, stash, reset or check out anything in the worktree or any other checkout. To run anything, export the branch first: `git -C {WT} archive campaign/{ID} | tar -x -C <your dir under {RUN}/scratch/>`, then `ln -sfn {KNOT}/.toolchain <copy>/.toolchain; ln -sfn {WT}/node_modules <copy>/node_modules`, and `git init -q` there if a tool needs git. Cite exact commands and outputs. Your final message must be the JSON object the output schema describes."""

LENSES = {
    'scope': f"LENS: SCOPE AND DISCIPLINE. Diff campaign/{ID} against {BASE} (`git -C {WT} diff {BASE}...campaign/{ID} --stat`, then in full). Check that only the increment's intended files changed. No existing test assertion, expectation file (cases.json, fixtures' expected outputs), law statement or proof body may be weakened or edited, except as the increment explicitly required. New expectations must come from the seed or from literal review, not from Knot's own output: look at how they were produced. Forms Knot cannot handle must be Unsupported, not Invalid (D4). Receipts are committed only when semantically changed. Commit messages carry a Co-Authored-By trailer. New Bend code follows D9: laws as law declarations with proofs; terse, exact names; no narration or costume.",
    'gates': f"LENS: GATES. In a fresh scratch export of campaign/{ID}, run `npm run -s gates` (the runner; allow up to 90 minutes, and use KNOT_GATE_TIMEOUT_SCALE=4 if the machine is loaded), the increment's new gates and the relevant PROOF entry points. Report the exact pass counts and compare them with the executor's claims. Any discrepancy, failure or flake is a finding. Also run `node scripts/perch-style.mjs --preflight --manifest=docs/compiler-campaign/manifest.json` and report the blockers.",
    'semantics': "LENS: INDEPENDENT SEMANTICS. Do not trust the increment's tests. Write your own small probe programs, in scratch, that exercise the new capability and its edges, especially the edges the increment might have missed. Compare the pinned seed with the increment's Knot checker and evaluator, and with Knot-emitted Wasm where applicable (scripts/run-wasm.mjs). Look for miscompilation, wrong classification, crashes, resource blowups and unsound acceptance: Knot accepting something the seed rejects, or emitting code that disagrees with it. Report concrete reproductions.",
}

def review(stage):
    lenses = list(LENSES.items())
    with cf.ThreadPoolExecutor(len(lenses)) as ex:
        found = dict(zip([k for k, _ in lenses], ex.map(lambda kv: codex(f'{stage}-review-{kv[0]}', ORIENT + '\nYOUR TASK: ' + kv[1] + ctx(), FINDINGS, str(RUN / 'scratch')), lenses)))
    todo = [(k, i, f) for k, r in found.items() if r for i, f in enumerate(r['findings']) if f['severity'] != 'minor']
    def verify(t):
        k, i, f = t
        v = codex(f'{stage}-verify-{k}-{i}', ORIENT + f"\nYOUR TASK: Adversarially verify this review finding for increment {ID}. Try to REFUTE it by reproducing or tracing it independently. If you cannot demonstrate it, return real=false.\nFINDING ({k}): {json.dumps(f)}\n" + ctx(), VERDICT, str(RUN / 'scratch'))
        return {**f, 'lens': k, 'verdict': v}
    with cf.ThreadPoolExecutor(max(1, len(todo))) as ex:
        judged = list(ex.map(verify, todo))
    minors = [{**f, 'lens': k, 'verdict': None} for k, r in found.items() if r for f in r['findings'] if f['severity'] == 'minor']
    res = {'failed_lenses': [k for k, r in found.items() if r is None],
           'confirmed': [f for f in judged if f['verdict'] and f['verdict']['real']],
           'refuted': [f for f in judged if f['verdict'] and not f['verdict']['real']],
           'unverified': [f for f in judged if not f['verdict']], 'minor': minors}
    with open(RUN / f'findings-{stage}.md', 'w') as md:
        md.write(f'# {ID} review {stage}\n\n')
        for key in ('confirmed', 'unverified', 'refuted', 'minor'):
            for f in res[key]:
                md.write(f"## [{key}] [{f['severity']}] ({f['lens']}) {f['title']}\n\n**Evidence.** {f['evidence']}\n\n**Suggested fix.** {f['fix']}\n\n")
                if f.get('verdict'): md.write(f"**Verifier.** {f['verdict']['reproduction']}\n\n")
    log(f"review {stage}: {len(res['confirmed'])} confirmed, {len(res['refuted'])} refuted, {len(res['unverified'])} unverified, {len(res['minor'])} minor, failed lenses {res['failed_lenses']}")
    return res

def precheck(stage):
    out = RUN / f'precheck-{stage}'
    up = [] if BASE == 'main' else ['--upstream', f"{BASE.removeprefix('campaign/')}={BASE}"]
    subprocess.run(['python3', '-B', 'scripts/prechecks/run.py', '--head', f'campaign/{ID}', *up, '--inc', ID, '--json', '--out', str(out)],
                   cwd=KNOT, stdout=subprocess.DEVNULL, stderr=open(RUN / 'logs' / f'precheck-{stage}.log', 'w'), env=ENV)
    try:
        rep = json.loads((out / 'report.json').read_text())
    except Exception:
        log(f'precheck {stage}: no report'); return None
    conds = [c for ch in rep['checks'] for c in ch.get('conditions', [])]
    ex = [c for c in conds if c['actor'] == 'executor' and c['severity'] in ('major', 'blocking')]
    log(f"precheck {stage}: exit {rep['exit']}, {len(ex)} executor major, {len(conds) - len(ex)} other")
    return {'executor': ex, 'other': [f"{c['check']} {c['rule']} [{c['severity']}/{c['actor']}]: {c['observed'][:200]}" for c in conds if c not in ex]}

sessions = []
def work(label, extra):
    s = codex(label, EXEC + extra, SESSION, WT)
    sessions.append(s and {**s, 'label': label})
    log(f"{label}: {s['status'] + ', ' + str(len(s['commits'])) + ' commits' if s else 'FAILED'}")
    return s

if not a.review_only:
    for i in range(a.max_sessions):
        prior = f"\nPRIOR SESSIONS (most recent last): {json.dumps([{k: s[k] for k in ('status', 'commits', 'remaining')} for s in sessions if s])[:8000]}\n" if sessions else ''
        s = work(f'implement-{i + 1}', prior)
        if not s or s['status'] != 'incomplete': break
    last = next((s for s in reversed(sessions) if s), None)
    if not last or (last['status'] == 'blocked' and not last['commits']):
        json.dump({'id': ID, 'status': 'blocked' if last else 'no-session', 'sessions': sessions}, open(RUN / 'summary.json', 'w'), indent=1)
        log('stopped before review'); sys.exit(0)

def stage_precheck(stage):
    p = precheck(stage)
    if p and p['executor']:
        work(f'precheck-fix-{stage}', f"\nPRE-REVIEW CHECKS: the deterministic pre-review suite reports these executor-actionable conditions on your committed head. Fix each in new commits, or dispute it with concrete evidence in your report (the suite can be wrong; say why). Keep frozen expectations unchanged. Do not chase coordinator or upstream conditions.\nCONDITIONS: {json.dumps(p['executor'])[:12000]}\n")
    if p and p['other']:
        global KNOWN
        KNOWN = KNOWN + [f"PRECHECK FACTS (deterministic suite, already known to the coordinator): {' | '.join(p['other'])[:5000]}"]

base_known = list(KNOWN)
stage_precheck('r0')
res = review('r0'); rounds = [res]
for r in range(a.max_fix_rounds):
    if not res['confirmed']: break
    fx = work(f'fix-{r + 1}', f"\nREVIEW ROUND {r + 1}: the coordinator's review CONFIRMED these findings, each adversarially verified. Fix every one in new commits (no history rewrites), keeping frozen expectations unchanged unless a finding requires a seed-derived amendment in its own commit. Then run `npm run -s gates`. Return status complete when all are fixed or disputed with evidence (say which in the report). Full text: {RUN}/findings-r{r}.md\nFINDINGS: {json.dumps([{k: f[k] for k in ('severity', 'title', 'evidence', 'fix')} | {'verifier': (f['verdict'] or {}).get('reproduction', '')[:1500]} for f in res['confirmed']])[:30000]}\n")
    KNOWN = list(base_known); stage_precheck(f'r{r + 1}')
    res = review(f'r{r + 1}'); rounds.append(res)

gaps = [f'review lens {l} failed' for l in res['failed_lenses']] + [f"unverified {f['severity']} ({f['lens']}): {f['title']}" for f in res['unverified']] \
       + (['a session failed'] if any(s is None for s in sessions) else [])
status = 'needs-coordinator' if res['confirmed'] else 'review-incomplete' if gaps else 'ready-to-merge'
summary = {'id': ID, 'status': status, 'gaps': gaps, 'open_findings': [{'severity': f['severity'], 'lens': f['lens'], 'title': f['title']} for f in res['confirmed']],
           'minor': [f['title'] for f in res['minor']], 'review_rounds': len(rounds),
           'sessions': [s and {k: s[k] for k in ('label', 'status', 'commits', 'gates', 'remaining')} for s in sessions],
           'findings_file': str(RUN / f'findings-r{len(rounds) - 1}.md')}
json.dump(summary, open(RUN / 'summary.json', 'w'), indent=1)
with open(RUN / 'summary.md', 'w') as md:
    md.write(f"# {ID}: {status}\n\n" + ''.join(f"- OPEN [{f['severity']}] ({f['lens']}) {f['title']}\n" for f in summary['open_findings'])
             + ''.join(f'- GAP {g}\n' for g in gaps) + ''.join(f"- session {s['label']}: {s['status']}, {len(s['commits'])} commits; remaining: {s['remaining'][:400]}\n" for s in sessions if s))
log(f'DONE {status}: {len(summary["open_findings"])} open, {len(gaps)} gaps -> {RUN}/summary.md')
