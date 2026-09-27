# Local Julia-1 review trial — 2026-09-26

**Disposition: installed and executable locally; not qualified to replace the
Bend reviewer.** Julia-1 classified 4/8 of the frozen narrow defect controls
correctly, compared with Kev-4B's 6/8 and Laya's 4/8. It rejected the unchanged
style request because two option descriptions exceed its fixed 48-token limit.
Its separate full growing-prefix rule result was 3/4, versus 2/4 for both prior
models. These are small control sets, not general model rankings.

The user identified [Julia-1 by Supersonic Labs](https://supersoniclabs.ia.br/julia-1/).
That website returned HTTP 403 during this run; identity and capabilities were
verified directly from the [official model card](https://huggingface.co/SupersonicLabs/Julia-1)
and downloaded source. Julia-1 has 144,292,870 parameters and builds on
`jhu-clsp/mmBERT-small`. It scores supplied options for Noul, Choice and Score.
The separate [Julia-1 MLX port](https://github.com/zm2231/julia-mlx) provides native
Apple Silicon inference using the unchanged original checkpoint.

The upstream Hub repository was created September 23 and last updated September
26. The independent MLX model listing was created September 27 at 02:46 UTC,
which is **September 26 at 19:46 Pacific**. Those are repository timestamps, not
proof of the original model's public announcement date.

## Reproducible local runtime

- Original checkpoint: `SupersonicLabs/Julia-1` at
  `a85b127321d580d65176c89ced8273f305745d85`.
- MLX source: `zm2231/julia-mlx` at
  `afbef9ee5d08646efd9baf4ab6d7ad75b0b23b93`, package 0.2.0.
- Python 3.12.13; MLX 0.32.2; numpy 2.5.3; tokenizers 0.23.2;
  safetensors 0.8.0. Dependencies come from the pinned runtime's frozen `uv.lock`.
- FP32, mapped original vocabulary embedding, token and encoding caches disabled.
  The native allocator cache uses the runtime default. No quantization,
  finetuning, threshold fitting or prompt changes were performed.

Runtime and approximately 550.5 MiB of model weights are installed under ignored
`.local/julia/`. The [runner](../scripts/julia-review.py) loads a pinned local
snapshot with Hub access disabled. It checks the runtime commit and tracked
source before running. Fresh Apple Silicon setup:

```sh
mkdir -p .local/julia
git clone https://github.com/zm2231/julia-mlx.git .local/julia/repo
git -C .local/julia/repo checkout --detach afbef9ee5d08646efd9baf4ab6d7ad75b0b23b93
UV_CACHE_DIR="$PWD/.local/uv-cache" uv sync --project .local/julia/repo \
  --python 3.12 --frozen --no-dev
npm run review:julia -- --download
```

```sh
npm run review:julia -- --input docs/laya-trial/requests.json \
  --output .local/julia/replay.json
npm run review:julia -- --audit-only --input docs/laya-trial/requests.json \
  --output .local/julia/audit.json
.local/julia/repo/.venv/bin/python tests/julia-review.test.py
```

The frozen replay and audit both return **exit 1** because the style request is
unsupported. Their receipts still contain all completed rows and the explicit
rejection. Exit 0 on supported inputs means inference or audit completed, not
that code passed review. Existing evidence files cannot be overwritten. No
server remains running and the shared Perch provider is unchanged.

## Exact inputs and results

The same [15 frozen requests](laya-trial/requests.json) used for Laya and Kev
were passed unchanged. The native typed adapter supplies its exact input rows
to preflight; no metadata labels, expected outcomes or file paths reach it.
An independently constructed complete token sequence and marker positions must
match the native strict encoder. The loaded engine's tokenizer is checked again
before inference. Native probabilities are retained without display rounding.

All 12 code requests and both language sanity requests fit completely within
512 tokens per question, although the runner's ceiling is 2048 with a 512-token
question/options budget. The held-out filenames are historical: these cases
were already observed during Laya prompt development and are not fresh holdouts.
Source, context and oracle identities remain those of the Laya trial.

The narrow requests each ask three defect questions. Higher probabilities below
mean the model thinks the corresponding family defect is present.

| Pair | Julia clean | Julia broken | Correct at 0.5 |
| --- | ---: | ---: | ---: |
| Growing prefix, original | 0.6933 | 0.0518 | 0/2 |
| Growing prefix, previously held out | 0.0006 | 0.7308 | 2/2 |
| Invariant summary | 0.0645 | 0.1225 | 1/2 |
| Linked-list indexing | 0.0162 | 0.0445 | 1/2 |

That is four correct decisions, one false positive and three false negatives.
The original growing-prefix pair ranks backwards. All other question outputs,
including cross-family answers, remain in [raw results](julia-trial/results.json).
The preselected corresponding-family question determines each row's verdict;
an unrelated positive answer is not counted as correct detection.

For the separate full growing-prefix requirement, probability that the rule
holds is 0.9992/0.9778 on the original clean/broken pair and 0.9878/0.1063 on the
previously held-out pair. Julia catches one of the two inefficient cases and
accepts both clean cases. The high-confidence miss prevents interpreting the
3/4 result as reliable review.

Both language sanity controls fall on the expected side of 0.5 for cancellation,
but weakly: 0.5076 when threatened and 0.4337 when absent. Choice correctly selects
billing and technical at probabilities above 0.99999.

The frozen style request is rejected as a whole: each of the two highest
“Highly memetic” descriptions needs **49 tokens**, beyond the fixed 48-token
contract. No style ratings or partial style pass are claimed. The three frozen
rubrics and the separately expanded current campaign policy remain unchanged.

## Timing and verification

Measured model load was 390.6 ms. The first inference took 1907.9 ms including
initial runtime setup. The eight three-question code requests took
**10.4–128.5 ms, median 16.5 ms**; two requests took over 100 ms. This is a single
process run without a separate warm-up for every input shape. It is not a steady
state latency benchmark or a controlled speedup comparison against Kev or Laya.

Seven focused input-integrity tests passed using the real tokenizer and native
adapter: all semantic/sanity inputs retained, Boolean descriptions ordered and
preserved, style rejection, state overflow, instruction overflow, reserved-marker
rejection and empty-question rejection. The npm audit matched every inference
preflight. All eight code-file hashes and the prior independent performance
oracle still match; the deterministic oracle was **not rerun**. The MLX author's
published PyTorch parity evaluations were **not rerun** in this trial.

[Comparison](julia-trial/comparison.json) records fixed-threshold outcomes and
timings. [Provenance](julia-trial/provenance.json) pins model, tokenizer, dependency
lock, input, result and oracle hashes. The trial establishes executable local
inference and these observed failures. Further qualification requires fresh
independent controls; none of the three local trials justifies changing the
default reviewer yet.
