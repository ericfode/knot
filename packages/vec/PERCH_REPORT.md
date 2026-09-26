# Vec live Perch audit — 2026-09-26

**No production finding was reported.** 13 Bend files and the current law packet received live `jev-1.13.0` checks. A missed-control defect in the dedicated rule was repaired without changing Bend semantics, accepted laws, or its 80% floor. All 13 uploaded files still match `0xd684886d10b431b9dce6c3b2d1ef1980`; nothing was republished.

Perch 0.3.5 requested `jev-latest`, resolved to `jev-1.13.0`: **25 invocations, 25 completed provider responses, 114 rule/file checks**. No zero-coverage, error, rate-limit retry, or partial request was counted. Commands used the root `npm run lint -- <path> --rules <names> --json` wrapper. Credentials were never read, copied or printed by the audit script.

## Coverage and receipts

Each Bend row received all six rules: `bend-fuel-completeness`, `bend-machine-arithmetic`, `bend-borrow-lifetime`, `bend-ordered-f32`, `bend-effect-boundary`, `bend-device-stack`. No findings at their current 80% floors. Source hashes below are 12-character prefixes; full hashes, raw scores, model IDs and root-wrapper receipt paths are in [summary.json](receipts/perch_audit_2026_09_26/summary.json), [index.json](receipts/perch_audit_2026_09_26/index.json), and each linked receipt.

| Source | SHA-256 prefix | Checks | Receipt |
| --- | --- | --- | --- |
| LAWS.bend | `bf5cc273eeeb` | 6 | [886610f4](receipts/perch_audit_2026_09_26/886610f4-7810-440b-a7d3-55207481e605.json) |
| PROOF.bend | `09a438b139bf` | 6 | [6b1a0bfd](receipts/perch_audit_2026_09_26/6b1a0bfd-1601-4f2e-b535-6afd462086ed.json) |
| benchmark.bend | `77a93e08e2e1` | 6 | [806c6e28](receipts/perch_audit_2026_09_26/806c6e28-01d9-4ba8-9684-007c3e6cb0c4.json) |
| conformance.bend | `eb2d7eebaa79` | 6 | [9e5f21e8](receipts/perch_audit_2026_09_26/9e5f21e8-82eb-4acc-b1b9-5dfd194db55d.json) |
| example.bend | `7079c1ae8a55` | 6 | [7288941e](receipts/perch_audit_2026_09_26/7288941e-9255-43cd-bc08-8db1f65b3b86.json) |
| generic.bend | `adf3a1fd8e09` | 6 | [72d1ed94](receipts/perch_audit_2026_09_26/72d1ed94-9a9c-4714-9d2a-ede372e08ab2.json) |
| main.bend | `baddf475d1ff` | 6 | [fbff7b48](receipts/perch_audit_2026_09_26/fbff7b48-7450-4827-ab6e-f4df113523a1.json) |
| model.bend | `4fb68671f7cb` | 6 | [c14ec95a](receipts/perch_audit_2026_09_26/c14ec95a-8344-439d-aca3-d05eab6cc3e1.json) |
| observations.bend | `d31a1cc102a0` | 6 | [4839c92e](receipts/perch_audit_2026_09_26/4839c92e-bcf7-4a82-b1ad-cee934b79b42.json) |
| release.bend | `974e90fd2020` | 6 | [609ec654](receipts/perch_audit_2026_09_26/609ec654-b658-43cd-9958-d851fa7c9dca.json) |
| trace.bend | `9378a64a7edf` | 6 | [49cae266](receipts/perch_audit_2026_09_26/49cae266-e722-4c0e-9688-44ac467d74bf.json) |
| witnesses.bend | `e432b1b51097` | 6 | [0b449a78](receipts/perch_audit_2026_09_26/0b449a78-a9f7-43ce-a255-c27e0d607394.json) |
| tests/remote_consumer.bend | `546305f607b6` | 6 | [029ca26c](receipts/perch_audit_2026_09_26/029ca26c-c342-47d1-921f-5039747e3989.json) |

The real [LAW_REVIEW.md](LAW_REVIEW.md) received all eight shared `law-*` rules plus `vec-logical-state-observation`. The final updated packet checked 9/9 rules in one live response with no findings: [74653924](receipts/perch_audit_2026_09_26/74653924-b4a5-4d28-bd15-843e2487673e.json), source SHA-256 `f0ca169fc459739d7c50d2c2e2bdc5ef1717c68dc7f1ddc8420a95876e984f4d`. Earlier packet/rule iterations remain in [refinement.json](receipts/perch_audit_2026_09_26/refinement.json).

Included even the small proof witnesses, examples and release/remote wrappers. Excluded only `tests/affine_negative.bend` and `tests/element_negative.bend` (intentional compiler-rejection fixtures), `tests/generated/**` (deliberately broken semantic mutants and duplicate copies), and `build/**` (generated outputs, probes and cache copies). Host scripts and other Markdown are outside the requested Bend-source checks. The negative fixtures retain exact deterministic kind/quantity diagnostic gates.

## Dedicated-rule controls and adjudication

The original multi-condition rule missed both broken controls. The revision asks directly whether the current validation accepts pop with stale logical length, while allowing a disclosed historical defect that current checks reject. **Floor remains 0.80; `gate: false` remains.** Before/after rule text is retained as [v1](receipts/perch_audit_2026_09_26/rule-v1.yaml) and [v2](receipts/perch_audit_2026_09_26/rule-v2.yaml). The Source package’s independently calibrated 70% floor was respected and not changed.

| Control | Expected | Before P(broken) | After P(broken) | Outcome |
| --- | --- | --- | --- | --- |
| [clean](tests/perch/clean/LAW_REVIEW.md) | clean | 0.12 | 0.09 | correctly unflagged |
| [broken](tests/perch/broken/LAW_REVIEW.md) | broken | 0.53 | 0.91 | miss → detected |
| [heldout](tests/perch/heldout/LAW_REVIEW.md) | clean | 0.24 | 0.09 | correctly unflagged |
| [heldout_broken](tests/perch/heldout_broken/LAW_REVIEW.md) | broken | 0.60 | 0.93 | miss → detected |
| [heldout_after_refinement](tests/perch/heldout_after_refinement/LAW_REVIEW.md) | broken | not used before revision | 0.90 | detected, fresh held-out |

All three reported findings were **confirmed in intentional broken controls**: each explicitly accepts a cleared final slot while logical length remains unchanged. These are three distinct inputs exhibiting the same defect family, not three package bugs. No reported production false-positive, duplicate or unresolved finding occurred. The earlier two misses remain recorded; the fresh final control was authored after the wording change and was not used to tune it. Detailed per-finding judgments and receipt links are in summary.json.

Deterministic corroboration: the unchanged original proof still passes; the stale-pop implementation mutant first type-checks, then fails `LAWS.pop_length` and the unchanged `push_pop` runtime assertion. This validates the control label independently of Perch. [deterministic.json](receipts/perch_audit_2026_09_26/deterministic.json) records those runs. `npm run lint:verify` also passed offline wrapper/rule-wiring tests; it is not included in live response counts.

Below-floor signals were reviewed without treating them as findings. `bend-machine-arithmetic` assigns 0.54–0.71 across these files, including 0.71 to the release wrapper that performs no index arithmetic. No concrete violation is localized by these scalar answers. Public arithmetic is checked before decrement/subtraction/increment; planning has 24 doublings under the 2^24 policy ceiling. Benchmark checksums intentionally use modular U32 arithmetic. The independent list model and fixed benchmark/conformance domains do not claim arbitrary host-sized Nat coverage. Existing boundary laws and typed mutations support leaving correct code unchanged. These raw scores are weak signals, not evidence of additional defects.

## Changes and remaining limits

Changed only the package-owned advisory rule and documentation of live-evidence availability; added two bounded controls, a reproducible audit driver and receipts/report. No Bend implementation, model, theorem, proof or conformance source changed. The deterministic manifest verifies every uploaded file hash. Historical `RELEASE.json` and release-era Perch receipt remain intact; their document/rule hashes describe the earlier release review, while this report and summary.json record the current audit.

Maintenance note for the coordinator: the broad rule’s two missed controls were prevented by asking one direct stale-length acceptance question; raising the floor was not used. The root maintenance log was left untouched to respect package ownership.

The control sample is small and manually constructed; it supports preliminary advisory use, not an accuracy estimate or mandatory gate. Perch has no Bend AST/call graph and whole-file success is not a proof. No general all-length refinement or GPU validation is added. Existing proof/runtime/publication evidence remains separate.
