import Base

# An expression offset is a Nat: a U32 result type refuses it at the offset.
def mismatch(t: Nat) -> U32:
  2n+t

def main() -> Nat:
  0n
