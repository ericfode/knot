# Calibration set for the prechecks Perch rules

Packets with expected labels for the seven advisory rules in
[`.perch/rules/prechecks.yaml`](../../../.perch/rules/prechecks.yaml). They exist for the coordinator's **live**
calibration run; nothing here has been asked of a model. A stub probability is never calibration, and neither is this
directory's existence: the rules stay `gate: false` until the live run separates the packets and adjudicated production
findings accumulate ([perch-maintenance.md](../../../docs/perch-maintenance.md), step 8).

| file | contents |
|---|---|
| `specs.json` | one spec per control: rule, split, increment, commits, and the text anchors (or verbatim excerpt) that pick the packet |
| `cases.json` | the built controls with expected label, source commits, packet path and sha256, plus the documented gaps |
| `<rule>/<split>-<id>.md` | the packets, in the packet format of `scripts/prechecks/packets/` (Claim, Evidence, Scope) |

Rebuild with `python3 scripts/prechecks/controls.py` in a checkout that has the campaign branches; it reads git objects
only and rewrites this directory. A spec that does not find its packet is reported and skipped, never faked.

## Splits and labels

- **broken** (dev): a packet whose claim the evidence contradicts. Expected: the rule flags it (probability of violation
  at or above the floor, 0.8).
- **clean** (dev): the same claim after the repair, or a claim known to hold. Expected: below the floor.
- **held-out**: packets from rounds whose review started at or after 2026-09-28T12:00Z. They are built from the
  design's control table (which names the commit and the defective passage), not from a finding's evidence, and no rule
  or builder was changed because of one, so they must not be used to tune a rule. Two exposures are disclosed:
  - vm-spec `5517f263` (the design's only held-out P3 instance) **moved to dev** (`broken`): its `check-spec.py` and
    SPEC lines were read to make the P3 builder attach the frozen expectation code that names the same cause
    (DESIGN 1.4, rule 3). The P6 held-out excerpt (vm-model `19cf7d8f`) was cut from the function the design table names;
    no builder or rule changed because of it.
  - While orienting, one finding of a held-out round was printed (literals, run `wf_0158b883-c9d`, scope lens, review
    started 2026-09-28T17:48Z: laws recorded as open D21 obligations). No rule, builder or control was derived from it,
    and no control uses that round; it is recorded so that replay treats the instance as exposed.

The label follows the split (`broken` and `held-out` expect a flag, `clean` expects none), and the wiring test
`scripts/check-prechecks-rule-wiring.mjs` asserts that. Every rule has a broken control. Splits with no control are listed
under `gaps` in `cases.json` with the reason (no history provides them, or the only candidates are known from evidence
that must stay unread until replay).

## How the packets were built

Most are the builders' own output at the commit, selected by text anchors from the design's control table
(`how: builder`). Two are excerpts of verbatim line ranges (`how: manual-excerpt`; the header says so): the section 6 and
section 9 passages of vm-spec `d2fe0f20`, whose defect the term selector does not reach, and vm-model `19cf7d8f`'s
`inspection_runs`, which the kill selector does not reach. Both are recall limits of the builders, recorded here rather
than hidden: the controls test the rules, not the selection.

## Running them

From the main checkout, where the credentials are (never from a linked worktree):

```sh
node scripts/prechecks-perch-run.mjs --controls          # dry run: lists every control, zero requests
node scripts/prechecks-perch-run.mjs --controls --live   # one request per packet, recorded under .perch/usage/
```

The report lists each packet's probability of violation and whether the set separates: every broken and held-out packet at
or above the floor and every clean packet below it. A rule that does not separate is rewritten or narrowed, never
floor-raised. Record the run (model, probabilities, rule and input hashes) in `docs/perch-review-log.md`.

The built-in `docs` category selects nothing on a packet, so it is not a baseline; the design's baseline arm runs
`npm run lint -- <file>::<fn> --rules defect` and `--rules docs` on the code subject of a P1 pair and adopts the built-in
only if it separates them at least as well.
