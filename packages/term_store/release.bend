# Reviewed release root: checking/publishing includes the complete laws and proofs.
import Base
import ./PROOF.bend as Proof
import ./conformance.bend as Conformance
import ./example.bend as Example
import ./benchmark.bend as Benchmark

def main() -> IO(Unit):
  Example.main()
