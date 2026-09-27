import Base

# Column x occupies bit x. Both directions clip to width;
# unpacking threads the remaining board as its suffix.
def row.pack(width: Nat, cells: List<&2,U32>) -> U32:
  match width:
    case 0n:
      0
    case 1n+p:
      match cells:
        case Nil{}:
          0
        case bit <> tail:
          (bit .|. U32.shl(row.pack(p, tail)) : U32)

def row.unpack(width: Nat, +bits: U32, tail: List<&2,U32>) -> List<&2,U32>:
  match width:
    case 0n:
      tail
    case 1n+p:
      (bits .&. 1 : U32) <> row.unpack(p, U32.shr(bits), tail)

def rows.pack(height: Nat, +width: Nat, +cells: List<&2,U32>) -> List<&2,U32>:
  match height:
    case 0n:
      Nil{}
    case 1n+p:
      row.pack(width, cells) <> rows.pack(p, width, List.drop(&2, U32, cells, width))

def rows.unpack(rows: List<&2,U32>, +width: Nat) -> List<&2,U32>:
  match rows:
    case Nil{}:
      Nil{}
    case bits <> rest:
      row.unpack(width, bits, rows.unpack(rest, width))

# A lane-wise full adder: each column's count is odd + 2*pairs.
def tally(+a: U32, +b: U32, +c: U32) -> U32 & U32:
  +parity = (a .^. b : U32)
  carry = ((a .&. b : U32) .|. (parity .&. c : U32) : U32)
  ((parity .^. c : U32), carry)

def halo(+bits: U32) -> U32 & U32:
  tally(U32.shl(bits), bits, U32.shr(bits))

# The census includes the center: total 3 lives; total 4 needs a live center.
# Counts lie in 0..9, so three low planes distinguish both selected totals.
def census.rule(low: U32 & U32, high: U32 & U32, here: U32) -> U32:
  (+ones, +low_carry) = low
  (+high_ones, high_carry) = high
  +twos = (low_carry .^. high_ones : U32)
  +fours = (high_carry .^. (low_carry .&. high_ones : U32) : U32)
  three = (ones .&. twos .&. U32.not(fours) : U32)
  four = (U32.not((ones .|. twos : U32)) .&. fours : U32)
  (three .|. (here .&. four : U32) : U32)

def census.spread(vertical: U32 & U32, here: U32) -> U32:
  (odd, pairs) = vertical
  census.rule(halo(odd), halo(pairs), here)

def row.step(above: U32, +here: U32, below: U32) -> U32:
  census.spread(tally(above, here, below), here)

# The window advances over old rows only; zero rows frame its two ends.
def rows.sweep(rest: List<&2,U32>, above: U32, +here: U32) -> List<&2,U32>:
  match rest:
    case Nil{}:
      [row.step(above, here, 0)]
    case +below <> tail:
      row.step(above, here, below) <> rows.sweep(tail, here, below)

def rows.step(rows: List<&2,U32>) -> List<&2,U32>:
  match rows:
    case Nil{}:
      Nil{}
    case here <> rest:
      rows.sweep(rest, 0, here)

def step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
  +columns = U32.to_nat(width)
  rows.unpack(rows.step(rows.pack(U32.to_nat(height), columns, cells)), columns)

def evolve(turns: Nat, +width: U32, +height: U32, cells: List<&2,U32>) -> List<&2,U32>:
  match turns:
    case 0n:
      cells
    case 1n+p:
      evolve(p, width, height, step(width, height, cells))
