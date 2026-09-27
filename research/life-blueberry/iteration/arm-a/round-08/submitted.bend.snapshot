import Base

# A zero-extended stream; output shifts right while the input place shifts left.
def row.duplex(width: Nat, +out: U32, +cells: List<&2,U32>, +place: U32, incoming: U32, next: U32 -> List<&2,U32> -> List<&2,U32>) -> List<&2,U32>:
  match width:
    case 0n:
      next(incoming, cells)
    case 1n+p:
      bit = Maybe.default(&2, U32, List.head(&2, U32, cells), 0)
      tail = List.tail(&2, U32, cells)
      (out .&. 1 : U32) <> row.duplex(p, U32.shr(out), tail, U32.shl(place),
        (incoming .|. (bit * place : U32) : U32), next)

# v0 + 2*v1 counts vertically; w/e shift those planes one column.
# The center is included: three lives, four keeps its old center.
def row.step(+north: U32, +here: U32, +south: U32) -> U32:
  +ns = (north .^. south : U32)
  +v0 = (ns .^. here : U32)
  +v1 = ((north .&. south : U32) .|. (ns .&. here : U32) : U32)
  +w0 = U32.shl(v0)
  +e0 = U32.shr(v0)
  +w1 = U32.shl(v1)
  +e1 = U32.shr(v1)
  +one = (w0 .^. v0 .^. e0 : U32)
  +lo = ((w0 .&. v0 : U32) .|. (e0 .&. (w0 .|. v0 : U32) : U32) : U32)
  +hi = (w1 .^. v1 .^. e1 : U32)
  carry = ((w1 .&. v1 : U32) .|. (e1 .&. (w1 .|. v1 : U32) : U32) : U32)
  +two = (lo .^. hi : U32)
  +four = (carry .^. (lo .&. hi : U32) : U32)
  three = (one .&. two .&. U32.not(four) : U32)
  four = (U32.not((one .|. two : U32)) .&. four : U32)
  (three .|. (here .&. four : U32) : U32)

# Emit the old window while filling the next one.
def rows.pipe(height: Nat, +width: Nat, north: U32, +here: U32, +south: U32, cells: List<&2,U32>) -> List<&2,U32>:
  match height:
    case 0n:
      Nil{}
    case 1n+p:
      row.duplex(width, row.step(north, here, south), cells, 1, 0,
        below => rest => rows.pipe(p, width, here, south, below, rest))

# Two initial output rows are pipeline latency; two extra passes drain it.
def step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
  +columns = U32.to_nat(width)
  delayed = rows.pipe(Nat.add(U32.to_nat(height), 2n), columns, 0, 0, 0, cells)
  List.drop(&2, U32, delayed, Nat.add(columns, columns))

def evolve(turns: Nat, +width: U32, +height: U32, cells: List<&2,U32>) -> List<&2,U32>:
  match turns:
    case 0n:
      cells
    case 1n+p:
      evolve(p, width, height, step(width, height, cells))
