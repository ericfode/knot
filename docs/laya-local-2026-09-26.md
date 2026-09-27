# Local Laya review trial — 2026-09-26

**Disposition: installed and executable; not qualified to replace the current
Bend reviewer.** The user requested a local System One model, identified Laya,
and explicitly allowed replacing Perch itself. This trial uses Laya's native
Python interface, not an LLM generating JSON and not a Perch HTTP shim.

The English checkpoint runs on this Mac's MPS GPU. It separates two simple
language controls but does not reliably distinguish these clean and inefficient
Bend implementations. No source, accepted rule, style target, or default provider
was changed to improve a model result.

## Runtime and command

- Laya 0.3.20, `convaiinnovations/laya`, immutable Hub revision
  `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (English ModernBERT checkpoint).
- Python 3.12.13, torch 2.14.0, transformers 5.17.0, tokenizers 0.23.2.
- Dependencies and weights live under ignored `.local/perch-laya/`; the exact
  installed dependency set is [requirements.txt](../tools/laya/requirements.txt).
- [laya-review.py](../scripts/laya-review.py) consumes a JSON array of requests
  with `id`, `state`, and `questions`. Other fields are evidence metadata and
  never reach the model. It retains probabilities and exact input-encoding audits.
- No server runs, no cloud inference occurs, and no TypeSafe key is needed.
  Exit 0 means inference/audit completed, **not** that the code passed review.
  An unsupported input returns exit 1 and an explicit `unsupported-input` row.
  Existing output files are never overwritten.

Setup on a fresh checkout:

```sh
UV_CACHE_DIR="$PWD/.local/uv-cache" uv venv --python 3.12 .local/perch-laya/venv
UV_CACHE_DIR="$PWD/.local/uv-cache" uv pip sync \
  --python .local/perch-laya/venv/bin/python tools/laya/requirements.txt
npm run review:laya -- --download
```

The download command fetches only the pinned English checkpoint, approximately
846 MB of weights. Normal runs load its local snapshot with Hub access disabled.
Setup is already complete in this checkout.

```sh
# Native inference on the frozen requests; the style row is rejected explicitly.
npm run review:laya -- --input docs/laya-trial/requests.json \
  --output .local/perch-laya/replay.json

# Encoding audit without loading model weights or executing inference.
npm run review:laya -- --audit-only --input docs/laya-trial/requests.json \
  --output .local/perch-laya/audit.json

HF_HUB_OFFLINE=1 .local/perch-laya/venv/bin/python tests/laya-review.test.py
```

Use `--device cpu` where MPS is unavailable. The report records the actual device
after inference, including an upstream fallback. The default sequence ceiling is
2048; `--max-tokens` may select up to the encoder's 8192-token architectural limit.
That is an input limit, not an accuracy claim for longer contexts.

## Preserving the input

Laya 0.3.20's native `build_sequence` clips each option description to 48 tokens,
shares a default 192-token budget between instructions and options, and fills
the remaining default 512-token sequence with state. Increasing only the context
length does not remove the other clipping.

The runner computes the head budget needed for the whole question, using Laya's
supported `head_max_len` override. It compares the actual native token sequence
and option-marker positions against an independently constructed uncut sequence.
It rejects any difference, oversized option, or literal mask token that the
library would rewrite. It never truncates or summarizes code to obtain a result.
The same audit is checked against the loaded Agent's tokenizer before inference.

Semantic source was parsed with Knot's existing Bend parser and explicit helper
context. Paths and the generic cohort text were removed from model state, so
`clean`, `baseline`, and held-out filenames cannot supply the answer. Exact
source and context identities are retained in [provenance](laya-trial/provenance.json).
The frozen [requests](laya-trial/requests.json) retain the actual model inputs.

All 12 semantic requests fit completely in **512 tokens per question**, and all
eight narrow-question requests also match the default native encoding. Thus these
failures do not result from the context-length override or silent clipping.
The first, full-rule formulation moves the complete requirement from Perch's long
true/false options into instructions, with short answer options. It retains the
requirement's wording; its model/prompt identity is still distinct from Jev's.

## Observed results

First, the existing growing-prefix requirement was asked of four code controls.
Laya assigned probability that the requirement **holds** of 0.8145/0.8211 to the
clean/broken original pair, and 0.7542/0.7745 to the clean/broken held-out pair.
Both inefficient implementations were accepted more strongly than their clean
counterparts. See [the first raw results](laya-trial/full-rule.json).

Second, three shorter native Noul questions asked directly about growing-prefix
copying, repeated invariant work, and sequential linked-list indexing. Each was
asked on eight controls; the table shows the corresponding defect question for
each pair. Higher means the model thinks the defect is present.

| Code pair | Clean | Inefficient |
| --- | ---: | ---: |
| Growing prefix, original | 0.8888 | 0.8999 |
| Growing prefix, held-out formulation | 0.8646 | 0.6591 |
| Invariant summary | 0.8146 | 0.7704 |
| Linked-list indexing | 0.9291 | 0.9414 |

At the ordinary 0.5 yes/no split all eight receive a positive defect answer:
4/8 correct, with all four clean examples flagged. Two pairs rank backwards;
the other two have only 0.0111 and 0.0123 gaps. This is an observed failure on a
small code sample, not an estimate of general Laya accuracy. No threshold was
tuned, no finetuning was performed, and no alternate checkpoint was tested.
The narrow wording is an experimental detector, not a newly accepted replacement
for the full rules. See [all distributions and timings](laya-trial/native-narrow.json).

The held-out filenames come from the earlier independent performance campaign.
Their inputs were already observed in the first formulation before this second
formulation; they are **not a fresh holdout for the prompt change**. The other
two families were added after the narrow questions were fixed.

The first narrow request took 711.6 ms; subsequent three-question requests took
69.9–117.6 ms. These are measured warm-process inference times for these small
inputs, excluding model loading. They do not establish a production throughput
or end-to-end speedup against Jev.

Two natural-language sanity controls behaved as expected: explicit cancellation
threat 0.7946, absence of a threat 0.2224; the corresponding Choice questions
selected billing and technical at 0.9674 and 0.9424. The model is returning
state-dependent judgments rather than a constant or stub.

The unchanged style questions were audited without inference. The two highest
“Highly memetic” level descriptions need **56 and 55 tokens**, beyond the fixed
48-token option cap. The request is rejected. **No style ratings or style pass
are claimed**, and the existing rubric/targets were not shortened.
See [sanity results and style rejection](laya-trial/sanity-and-style.json) and
[all input audits](laya-trial/input-audit.json).

Laya warns that the checkpoint's `choice:11+` calibration temperature is clamped
from 0.10058 to 0.5. These trials use Noul and a three-option Choice, so that
bucket was not exercised. The warning is recorded here rather than suppressed.

## Verification and remaining boundary

Eight focused tests passed using the actual pinned tokenizer and sequence
builder: complete small input, dynamic instruction budget, oversized option,
clipped object/list state, mask rewriting, empty questions, all semantic inputs,
and the unchanged style rejection. The installed runtime executed 14 inference
requests across the two code trials and the two language sanity checks.

All eight code-file hashes match the existing independent
[performance-control receipts](../tests/perch-performance/evidence/controls.json).
Those receipts establish behavior and work-count labels; they were verified by
hash, **not rerun** in this tooling experiment. Model-file hashes, source hashes,
oracle identity, and context limits are recorded in provenance. No compiler,
law, quantity, GPU execution, or performance gate was weakened.

The existing shared Perch and style commands still use their original provider.
The native Laya runner remains opt-in experimental tooling. Reconsider promotion
only with a different checkpoint or code-domain training and independent fresh
controls; further prompt changes on these same examples would be development,
not new validation.

Sources: [Laya upstream](https://github.com/NandhaKishorM/laya),
[checkpoint](https://huggingface.co/convaiinnovations/laya/tree/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851),
[TypeSafe wire contract](https://docs.typesafe.ai/api). The installed 0.3.20
source and recorded checkpoint, rather than moving upstream `main`, define this
experiment's runtime behavior.
