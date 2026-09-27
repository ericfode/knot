# Criticality policy smoke check

The user requested Galaxy brain for critical functions, laws and proofs, and
authorized a separate Perch value to identify them. The binary criticality
question and the three style scores share one request. Critical or uncertain
classification selects big-brain level 5 with at least 60% probability mass;
truncated context cannot select the lower bar. Missing classifications fail.

## Expectations recorded before the provider run

| Declaration | Expected criticality | Reason |
| --- | --- | --- |
| `src/check.bend::run` | Critical | Main recursive checker controls typing and ownership acceptance, including fuel rejection. |
| `src/check-LAWS.bend::repeated_affine_level` | Critical | States rejection of repeated use of an affine binding, a defining ownership boundary. |
| `src/check-PROOF.bend::L.repeated_affine_level` | Critical | Discharges that same obligation; its short reflexivity proof does not reduce the obligation's importance. |
| `src/diagnostic.bend::location` | Noncritical | Formats source positions; the shown operation does not decide program acceptance or establish a core invariant. |

These are bounded operational controls, not an accuracy estimate or a claim of
human calibration. No Bend source is changed. The proof's short normalization
step does not by itself demonstrate the reframing required for Galaxy brain.
No scores will be retried or criteria changed to obtain a pass.

## Deterministic checks

`npm run lint:verify` passes 31 offline tests and the eight-law wiring gate.
Tests cover functions, law declarations, local law definitions and imported proof
fills; level 4 fails the critical gate and level 5 passes it. They also cover
uncertain/truncated classifications, probability boundaries, missing answers,
receipt reuse and campaign assessment. Fixed test scores are not calibration.

## Provider result

The [retained receipt](smoke.json.gz) completed four requests with four responses
from `jev-1.13.0` (`jev-latest` requested). Source and context hashes remained
current. The command exited 3 because none of the four declarations met all
three applicable style targets.

| Declaration | Critical probability | Classification | Big-brain target / mass | Delight mass | Memetic mass |
| --- | ---: | --- | ---: | ---: | ---: |
| `src/check.bend::run` | 1.00 | Critical | 5 / 0.00 | 0.820 | 0.596 |
| `src/check-LAWS.bend::repeated_affine_level` | 0.92 | Critical | 5 / 0.00 | 0.576 | 0.200 |
| `src/check-PROOF.bend::L.repeated_affine_level` | 0.80 | Critical | 5 / 0.00 | 0.050 | 0.020 |
| `src/diagnostic.bend::location` | 0.02 | Noncritical | 3 / 0.70 | 0.360 | 0.000 |

Masses are normalized and rounded here; the receipt retains full distributions.
Delight and memetic masses use levels 3 and higher. The checker function has
truncated helper context; the other three do not. This limitation remains
visible and cannot lower its requirement. Classification agreed with all four
recorded expectations, but the sample does not establish classifier accuracy.

All three critical declarations failed the Galaxy-brain requirement. This is
the observed new gate behavior, not a compiler or proof defect and not a reason
to weaken a contract, obscure a reflexivity proof, or lower the grade. Existing
project scores cannot certify the new policy. Further human calibration needs
fresh held-out examples; no source improvement or broad compliance is claimed.
