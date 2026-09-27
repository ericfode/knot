# Vocabulary into process: 100 inducer trials

This is a creative selection exercise. It does not measure programming correctness,
inducer causality, or changes to actual model cognition.

Three Luna agents, at low effort, proposed ten families in `families-a.json`,
`families-b.json`, and `families-c.json`. Their suggestions are retained verbatim.
`process.py` implements bounded adaptations, rather than claiming to implement
every detail of those speculative algorithms. Its exact code is the process authority.

The former inducer's objects—copper, keys, doors, rooms, witnesses—are removed.
The retained operations are recurrence, changed adjacency, incompatible orientation,
erasure and return, migrating boundaries, shared identity, and reinterpretation.
They act on inscriptions instead of being explained as a story.

Each inscription starts as a 7×9 field using seven marks. Six transformation rounds
alternate a primary and secondary process. Four related states are rotated and
arranged in an unnumbered square; a final recurrence is taken from the transformed
field. This preserves a visible relation between passages rather than adding
unrelated visual noise.

| Family | Implemented operation |
| --- | --- |
| 0 | Crossed coordinates exchange neighboring marks. |
| 1 | Concentric shells rotate with unequal periods. |
| 2 | Three countercurrents braid while lane identities move. |
| 3 | The preceding mark changes which coordinate is visited next. |
| 4 | Voids spread while displaced marks reappear across a seam. |
| 5 | A moving cut changes which marks belong to each rotating side. |
| 6 | Sites are simultaneously replaced through other rows' readings. |
| 7 | Crossing strands share an identity and branch with its residue. |
| 8 | Coordinates collapse into aliases and unfold through another axis. |
| 9 | A phase changes which recurring marks are treated alike. |

Ten variants per primary family produce exactly 100 distinct stimuli. Their seeds,
secondary processes, render modes, and exact hashes are in `manifest.json`.
Forty use glyphs alone; thirty add nonce syllables; thirty retain only seven function
words (`if`, `as`, `of`, `yet`, `which`, `until`, `here`). The function words are
shuffled and attached to marks. No domain-object vocabulary remains.

## Elicitation

Each trial uses a fresh ephemeral Codex context running `gpt-5.6-luna` at low effort.
Three calls run concurrently. Trials receive the complete `BRIEF.md` plus one
inscription and the same question. They return one paragraph and one code chunk.
The brief specifies an open language-design task; previous Φ grammar is explicitly
not the target language. No existing program or oracle is applicable to this task.

The trial runs in an empty temporary directory, with project document loading
disabled, read-only filesystem permissions, and major tool capabilities disabled.
It is instructed to make no tool calls. Any actual tool event disqualifies the
receipt; CLI warning events are recorded separately. Global service instructions
still exist, so this is fresh conversation context, not a claim of a blank model.

Four exploratory calls preceded the frozen 100-trial run. They are retained in
`pilots/`. The first prompt invited mostly familiar code. The final brief explicitly
states the user's otherness criterion and permits impossible or paradoxical designs.
An early receipt classifier incorrectly counted CLI warning events as tool activity;
that classifier was corrected before the main run. Pilot responses are excluded
from selection. Every main-trial prompt uses the same final brief.

## Selection

Two independently shuffled rounds assign every proposal to ten-item blind panels.
Fresh Luna contexts rate the paragraphs and code without seeing their inducers,
family labels, or other judgments. The five axes are unfamiliar computational
units, unfamiliar ordering, interpretation changes, source structure, and overall
unfamiliarity. The actual code receives substantial weight. Decorative Unicode
and assertions of alienness are insufficient by themselves.

Correctness, executability, safety proofs, and practical usefulness are not scored.
These are subjective creative judgments, with two ratings per proposal. A model's
score is not an objective measurement of otherness. `RUBRIC.md` contains the exact
judge prompt. Scores average to a 0–100 scale; ties use mean source-structure score,
then stable ID. All scores and rationales are retained in `ranking.json`.

The primary agent then inspected all 100 code specimens and the paragraphs of 24
structural finalists. This final qualitative selection was added after observing
that Luna's absolute ratings saturated near the ceiling, sometimes even for familiar
list or assignment forms. The final top ten in `selection.json` are therefore an
editorial ranking for otherness, not simply the ten highest raw Luna scores. The
finalist IDs, chosen order, and reasons are recorded; raw ratings remain unchanged.
Correctness and feasibility are still excluded.

The selected responses receive plain-English readings, with their original inducers,
paragraphs, and source preserved alongside them. The stimuli are generated operations,
not ciphers hiding English sentences. An English rendering of a code proposal is
interpretive and does not establish executable semantics.

## Reproduce and inspect

```sh
python3 sigil/inducers/process.py
python3 sigil/inducers/run.py
python3 sigil/inducers/judge.py
python3 sigil/inducers/report.py
```

Generation is deterministic. Model runs are stochastic; completed exact-prompt
receipts are reused unless removed or placed in a new experiment directory.
Every fresh attempt records prompt/response hashes, model, settings, elapsed time,
thread ID, token usage, return code, warnings, and tool-event count. CLI timing
includes startup and transport, not just model inference. Per-call billed cost is
unavailable for these account-backed Codex runs and is recorded as null.

`selection.json` and `english.json` record the primary agent's final selection and
interpretive English readings. Selected response hashes are pinned; the report
refuses to reuse those readings against changed responses. A fresh model sample
requires a fresh editorial review before regenerating the final report.

This generator and runner orchestrate a creative experiment; neither implements
Φ's parser, compiler, or runtime. Existing Bend programs and AGENTS.md are unchanged
by the experiment. Selecting a new default inducer is a separate decision.
