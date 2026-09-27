# Pinned local decision trials

These are advisory comparison runners, separate from the default Perch endpoint.
See [the trial report](../../docs/local-models-2026-09-26.md). They consume the
unchanged `docs/laya-trial/requests.json` packet; only `state` and `questions`
reach inference. Existing receipts are never overwritten at command startup.

## Preparation

The trial uses Python 3.12.13 on Apple Silicon. Dependencies, clones, model
downloads and merged weights live under ignored `.local/` directories. Runtime
and model revisions are in [pins.json](pins.json). Install the recorded inference
environments with:

```sh
UV_CACHE_DIR=.local/uv-cache uv venv --python 3.12 .local/decision-models/venv
UV_CACHE_DIR=.local/uv-cache uv pip install --python .local/decision-models/venv/bin/python -r tools/local-models/mlx-requirements.txt
UV_CACHE_DIR=.local/uv-cache uv venv --python 3.12 .local/autojev/venv
UV_CACHE_DIR=.local/uv-cache uv pip install --python .local/autojev/venv/bin/python -r tools/local-models/autojev-requirements.txt
```

Clone the public runtimes into `.local/eikos/repo`, `.local/nimble/repo` and
`.local/autojev/repo`, then check out their exact `runtime_commit` from the
manifest. Their repositories are `caiovicentino/eikos`, `bespokelabsai/nimble`
and `denis-pplx/autojev` on GitHub. Do not replace an existing clone with work in
it. The runner checks the revision and tracked diff before loading.

Use `hf download REPO --revision REVISION --local-dir DIRECTORY` with the
manifest's exact repository/revision pairs. Eikos goes in `.local/eikos/model`;
AutoJev in `.local/autojev/model` (exclude `source/*`); Nimble's adapter goes in
`.local/nimble/adapter`, and its pinned Qwen base in `.local/nimble/base`.
`hf download` uses repeated `--include` flags for multiple patterns. Required
tokenizer files include JSON, Jinja and, for Kev's snapshot resolver, TXT files.
The installed CLI is `.local/decision-models/venv/bin/hf`.

Merge Nimble using the published CPU/BF16 recipe. It verifies the adapter hash
and prompt contract, records the adapter/base identity, and refuses to replace
an existing merged folder:

```sh
.local/decision-models/venv/bin/python scripts/prepare-nimble.py
```

For AutoJev, apply the reviewed one-line dtype patch from the repository root:

```sh
git -C .local/autojev/repo apply ../../../tools/local-models/autojev-mps.patch
```

It selects BF16 on MPS, as the native loader already does on CUDA, avoiding a
roughly 104 GB FP32 weight allocation. The runner permits exactly this patch and
rejects any other tracked modification. Native PyTorch reference kernels handle
the recurrent layers; no CUDA-only acceleration packages are required. This is
a local runtime adaptation, not an upstream claim of Mac support.

Kev retains its existing isolated runtime and source pin; see
[the Kev setup report](../../docs/kev-local-2026-09-26.md). Download the exact 9B
adapter and base with:

```sh
PYTHONPATH=.local/kev/repo .local/kev/repo/.venv/bin/python scripts/kev-review.py --model kev-9b --download
```

## Inference and checks

Use new receipt paths for reruns. Run one inference process at a time:

```sh
.local/decision-models/venv/bin/python scripts/local-model-review.py --model eikos --input docs/laya-trial/requests.json --output .local/eikos-rerun.json
.local/decision-models/venv/bin/python scripts/local-model-review.py --model nimble --input docs/laya-trial/requests.json --output .local/nimble-rerun.json
.local/autojev/venv/bin/python scripts/local-model-review.py --model autojev --input docs/laya-trial/requests.json --output .local/autojev-rerun.json
PYTHONPATH=.local/kev/repo .local/kev/repo/.venv/bin/python scripts/kev-review.py --model kev-9b --input docs/laya-trial/requests.json --output .local/kev9-rerun.json
```

All runners set Hub/Transformers offline mode for inference. They never launch a
server. `--audit-only` checks native encodings without loading model weights.
The new runner flushes a receipt after every completed request; an interrupted
receipt is incomplete, and the comparison command rejects it.

```sh
MODEL_REVIEW_MODEL=eikos .local/decision-models/venv/bin/python tests/local-model-review.test.py
MODEL_REVIEW_MODEL=nimble .local/decision-models/venv/bin/python tests/local-model-review.test.py
MODEL_REVIEW_MODEL=autojev .local/autojev/venv/bin/python tests/local-model-review.test.py
MODEL_REVIEW_KEV=kev-9b PYTHONPATH=.local/kev/repo .local/kev/repo/.venv/bin/python tests/kev-review.test.py
```

The comparison command requires all 15 requests, matching input digests and all
answers. It uses the preselected family question and fixed 0.5 threshold:

```sh
.local/decision-models/venv/bin/python scripts/compare-local-models.py .local/eikos-rerun.json .local/nimble-rerun.json .local/autojev-rerun.json .local/kev9-rerun.json --output .local/model-comparison-rerun.json
```

Style summaries retain all probabilities and ordered legends. Eikos and Nimble
have no Jev confidence field; the adapter does not manufacture one. This tool is
not a drop-in Perch transport, a current style-campaign pass, or a qualification
gate. New deployment decisions need fresh independent controls.
