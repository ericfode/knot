import Base

# Indices are 0..31; the bit at an index controls whether that index is retained.
def flag(index: U32) -> U32:
  U32.shln(1, U32.to_nat(index))

def helper(+mask: U32, indices: List<&2, U32>) -> List<&2, U32>:
  match indices:
    case Nil{}:
      Nil{}
    case Con{+index, rest}:
      +tail = helper(mask, rest)
      Bool.pick(List<&2, U32>, U32.is_eq(U32.and(mask, flag(index)), 0),
        tail, index <> tail)

def select(mask: U32, indices: List<&2, U32>) -> List<&2, U32>:
  helper(mask, indices)
