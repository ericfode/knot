import Base
import ./PROOF.bend as Proof
import ./witnesses.bend as Witnesses
import ./conformance.bend as Conformance
import ./benchmark.bend as Benchmark
import ./example.bend as Example
import ./generic.bend as Generic

# Reviewed upload root: laws/proofs, model and runnable checks are in closure.
def main() -> Bool:
  Bool.and(Conformance.named(),Generic.main())
