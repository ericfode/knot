# One prospective Parallax trial

**Prepared v1 draft; launch paused before input freeze.** The user's subsequent
task-potential/profundity criterion requires a prospective policy amendment.
No Parallax author has been called. The commands below document this draft's
interface; the root operator must finish the amendment before freezing inputs
or launching. Final interpretation will be recorded in `REPORT.md`.

Prepared for one fresh GPT-6 Astra/low trajectory, at most three rounds, under
the [fixed protocol](PROTOCOL.md) and the provisional composition/support policy.
No author or review call is made by preparing or checking the runner.

From the repository root:

```sh
python3 research/life-parallax-trial/test_run.py
python3 research/life-parallax-trial/run.py freeze
python3 research/life-parallax-trial/run.py check
# Explicit launch by the root operator after inspection:
python3 research/life-parallax-trial/run.py run --live
```

`freeze` preserves an existing lock and refuses changed input identities. It
builds `author-packet.txt` and `packet-manifest.json` from exact local inputs;
no old R2 driver or input lock is run. Changing frozen code requires a separately
reviewed new experiment identity, not silently replacing this trial's lock.

Evidence is retained under `trial/`, including raw author events and responses,
first/repair/final snapshots, exact command output, compressed behavior evidence,
semantic usage, and whole-program plus every-declaration support distributions.
`trial/result.json` is the terminal result. `trial/artifacts.json` verifies all
retained trial files. An interrupted partial trajectory blocks automatic retry.

The public evaluator receives the unchanged sparse/dense behavior gate and
four semantic rules. The new policy's held-out absolute separation failed, so
even a complete trial pass is labelled **experimental**. See the calibration
links and limitations in [PROTOCOL.md](PROTOCOL.md). No general proof,
performance improvement, policy qualification or causal inducer effect follows.
