import Base

# Column x occupies bit x; unpacking clips to width and threads a suffix.
def row.emit(width: Nat, +bits: U32, tail: List<&2,U32>) -> List<&2,U32>:
  match width:
    case 0n:
      tail
    case 1n+p:
      (bits .&. 1 : U32) <> row.emit(p, U32.shr(bits), tail)

# The countdown and one-hot place advance together; the row end carries.
def rows.pack(cells: List<&2,U32>, +last: Nat, left: Nat, +place: U32, bits: U32) -> List<&2,U32>:
  match cells left:
    case Nil{} _:
      Nil{}
    case cell <> tail 0n:
      (bits .|. (cell * place : U32) : U32) <> rows.pack(tail, last, last, 1, 0)
    case cell <> tail 1n+p:
      rows.pack(tail, last, p, U32.shl(place), (bits .|. (cell * place : U32) : U32))

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

# The window advances over old rows only; zero rows frame its two ends.
def rows.sweep(rest: List<&2,U32>, above: U32, +here: U32, +width: Nat) -> List<&2,U32>:
  match rest:
    case Nil{}:
      row.emit(width, row.step(above, here, 0), Nil{})
    case +below <> tail:
      row.emit(width, row.step(above, here, below), rows.sweep(tail, here, below, width))

def rows.step(rows: List<&2,U32>, width: Nat) -> List<&2,U32>:
  match rows:
    case Nil{}:
      Nil{}
    case here <> rest:
      rows.sweep(rest, 0, here, width)

def step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
  +columns = U32.to_nat(width)
  +last = Nat.sub(columns, 1n)
  rows.step(rows.pack(cells, last, last, 1, 0), columns)

def evolve(turns: Nat, +width: U32, +height: U32, cells: List<&2,U32>) -> List<&2,U32>:
  match turns:
    case 0n:
      cells
    case 1n+p:
      evolve(p, width, height, step(width, height, cells))
