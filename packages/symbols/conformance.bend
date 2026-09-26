import Base
import ./cases.bend as C

def main() -> U32:
  Bool.to_u32(Bool.and(C.all_cases(),C.exhaustive()))
