# Calibration set for the prechecks Perch rules

These are packets with expected labels for the seven advisory rules in [`.perch/rules/prechecks.yaml`](../../../.perch/rules/prechecks.yaml).

- **Status.** The set was rebuilt on 2026-09-29 and has been asked live. The runs, the per-control probabilities and the judgment are recorded in [`docs/perch-review-log.md`](../../../docs/perch-review-log.md) (2026-09-29, "a rebuilt calibration set") and in `results-2026-09-29.json`.
- **Every rule is still uncalibrated.** Each keeps `min: 80` and `gate: false`: no rule's dev gap reached the margin the re-run noise requires.
- **Stub probabilities never count.** They are not calibration, and neither is this directory's existence.

| file | contents |
|---|---|
| `specs.json` | One spec per control: rule, split, expected label, increment, commits, and either the text anchors that pick the packet or a verbatim excerpt. It also holds the documented `gaps` and the `retired` controls, each with its reason. |
| `cases.json` | The built controls, with expected label, source commits, packet path and sha256, plus the gaps and retired controls. |
| `<rule>/<split>-<id>.md` | The packets, in the packet format of `scripts/prechecks/packets/` (Claim, Evidence, Scope). |
| `results-2026-09-29.json` | Every live run of 2026-09-29, with its identities (the rules file, per-rule hashes, and the receipts' combined `rules_sha256`) and per-control probabilities. |

Rebuild with `python3 scripts/prechecks/controls.py` in a checkout that has the campaign branches. It reads git objects only and rewrites the packets and `cases.json`. A spec that does not find its packet is reported and skipped, never faked.

## Labels and splits

A label follows from reading the packet text alone, judged by the rule's question:
- **broken**: the packet itself shows the violation. Both the claim, clause or passage and the contradicting code, text or row are inside the packet.
- **clean**: the packet itself shows the property holding. The deciding evidence is in the packet, or the rule's own applicability or exemption sentences say the case holds.
- **excluded**: a candidate whose label would turn on unshown evidence, on context outside the packet, or on a judgment call. It is not a control.

Knowing which commits were accepted or flagged gives candidates, never labels.

The splits:
- **Dev** (`broken`, `clean`): the label follows the split. Dev controls tune a rule. Every rule has at least three of each label; the wiring test asserts that.
- **Held-out** (`held-out`, with `expected` either `broken` or `clean`): labelled only after the rule texts were frozen (`9b28680c`), by labellers who saw no scores, drafts or dev results.
  - Heads: no dev control used them. They come from rounds whose review started at or after 2026-09-28T12:00Z, plus two post-review tips (`vm-spec 60e80693`, `vm-core 2c1f3d70`) reserved before any search.
  - They were committed with their sha256 (`afd38d23`) before the single held-out run, and asked once.
  - A held-out cell with no high-confidence control is a documented gap with its reason. Today there are two: clause-vs-delta's held-out broken, and outcome-follows-d4's held-out broken.

## How the packets were built

The packets are the unmodified builders' output at real campaign commits (`how: builder`), selected by text anchors. The anchors pick the first built packet that contains all of them.

Where the builders' selection misses the deciding lines, the packet is instead a verbatim excerpt of line ranges at the commit (`how: manual-excerpt`; its header says so): 9 of the dev controls and 7 of the held-out ones. The excerpts mark the builders' recall limits; they test the rules, not the selection.

The candidates were found this way:
1. Read-only agents searched packet pools built from about 60 campaign heads, with accepted tips as clean candidates and confirmed-regression heads as broken candidates.
2. The replay's labelled findings were pointers only.
3. Every dev label was re-read before it was committed.
4. Pairs were preferred: the same claim broken at one head and repaired at a later one (for example drop-operands, `vm-expected.json`'s golden count, the image-size class, `vm_expectation`).

## Retired controls

Twelve controls of the first calibration set were retired, each with its reason in `specs.json`. None of them could carry its label from the packet text.
- **clause-vs-delta, all four:** the anchors matched incidental words; no violating hunk is in the packet.
- **required-laws-met, all three:** their `required_laws` list has no verbatim source.
- **kill-is-semantic held-out excerpt:** it shows no kill predicate.
- **outcome-follows-d4, two:** their stated defect is not in the packet.
- **claim-holds-against-evidence, two:** their label rested on unshown evidence.

One control was relabelled: `kill-is-semantic/broken-vm-model-07e6db73-kills`. It was clean in the first set, but its `harness_runs` credits a crashed fuel control as a kill.

## Exposures

- **From the first build:** vm-spec `5517f263` moved to dev when its passages were read to fix the P3 builder, and one held-out literals finding was printed during orientation. `5517f263` is now retired.
- **From the 2026-09-29 rebuild:**
  - The replay's held-out finding titles were printed while orienting, and one held-out claim-holds control was seeded from such a pointer (its note says so).
  - An agent's `git grep` printed nest `99053a70` contract lines, so that head was not used for clause-vs-delta or required-laws-met.
  - Two agents printed held-out head names.
  - The dev set keeps the post-cutoff vm-spec tip `63e63203` and vm-model `07e6db73` (reviewed 18:37Z), as the design did.

## Running them

From the main checkout, where the credentials are (never from a linked worktree):

```sh
node scripts/prechecks-perch-run.mjs --controls --split dev               # dry run: lists the dev controls, zero requests
node scripts/prechecks-perch-run.mjs --controls --live --split dev --rules a,b
node scripts/prechecks-perch-run.mjs --controls --live --split held-out   # once, after the rule text is frozen
```

What the runner does:
- **Staging.** It stages the controls under `.local/prechecks/packets/controls/`, which production plans skip, and removes them when it ends, even after a dry run.
- **Requests.** It asks one request per packet and never caps the controls.
- **Flagging.** A packet is flagged when its probability is strictly above its rule's floor, `max(0.5, min/100)`, as Perch reports it.
- **Separation.** A rule separates when every expected-broken control is flagged and no expected-clean one is. The report gives this per rule.

A rule that does not separate is rewritten or narrowed, never floor-raised.

**Branch versions.** To ask a branch's rules or controls, overlay the branch's `.perch/rules/prechecks.yaml`, `scripts/prechecks-perch-run.mjs` and this directory into the main checkout's working copy. Run, restore it with `git checkout` and `git clean` on those paths, and compare `git status` and `HEAD` with a snapshot. Never commit there. Record the run, with the model, probabilities and rule and input hashes, in `docs/perch-review-log.md`.

**Baseline arm.** The built-in `docs` category selects nothing on a packet, so it is not a baseline. The design's baseline arm runs `npm run lint -- <file>::<fn> --rules defect` and `--rules docs` on the code subject of a claim-holds pair, and adopts the built-in only if it separates them at least as well.
