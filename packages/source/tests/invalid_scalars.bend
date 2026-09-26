import Base
import ../main.bend as S
import ../types.bend as T
import ../observations.bend as O

# Native can construct these malformed Char values. JS's Char constructor
# throws before Source receives them; this is a native-only input partition.
def main() -> U32:
  Bool.to_u32(Bool.and(O.rejected(T.InvalidScalar{},S.Source.new(7,SCon{Chr{55296},""})),Bool.and(O.rejected(T.InvalidScalar{},S.Source.new(7,SCon{Chr{57343},""})),O.rejected(T.InvalidScalar{},S.Source.new(7,SCon{Chr{1114112},""})))))
