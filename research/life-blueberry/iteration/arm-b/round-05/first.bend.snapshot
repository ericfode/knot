import Base

# Bit x holds column x; packing and unpacking preserve row order.
def pack(cells: List<&2, U32>) -> U32:
  match cells:
    case Nil{}:
      0
    case Con{cell, rest}:
      (cell .|. U32.shl(pack(rest)) : U32)

def unpack(width: Nat, +row: U32) -> List<&2, U32>:
  match width:
    case 0n:
      Nil{}
    case 1n+rest:
      (row .&. 1 : U32) <> unpack(rest, U32.shr(row))

# These are lane-wise boolean circuits: each bit position is independent.
def carry3(+a: U32, +b: U32, +c: U32) -> U32:
  ab = (a .&. b : U32)
  ac = (a .&. c : U32)
  bc = (b .&. c : U32)
  (ab .|. ac .|. bc : U32)

def one4(+a: U32, +b: U32, +c: U32, +d: U32) -> U32:
  odd = (a .^. b .^. c .^. d : U32)
  pairs = U32.or(U32.and(a, b), U32.and(c, d))
  U32.and(odd, U32.not(pairs))

# Carry the three low bits; exactly one high bit means two or three neighbors.
def pulse(+north: U32, +center: U32, +south: U32) -> U32:
  +nw = U32.shl(north)
  +ne = U32.shr(north)
  +cw = U32.shl(center)
  +ce = U32.shr(center)
  +sw = U32.shl(south)
  +se = U32.shr(south)
  +n0 = (nw .^. north .^. ne : U32)
  +c0 = (cw .^. ce : U32)
  +s0 = (sw .^. south .^. se : U32)
  n1 = carry3(nw, north, ne)
  c1 = (cw .&. ce : U32)
  s1 = carry3(sw, south, se)
  odd = (n0 .^. c0 .^. s0 : U32)
  two = one4(n1, c1, s1, carry3(n0, c0, s0))
  U32.and(two, U32.or(odd, center))

# Only old row words advance through north, center and south.
def sweep(
  height: Nat, +width: Nat, +cells: List<&2, U32>, north: U32
) -> List<&2, U32>:
  match height:
    case 0n:
      Nil{}
    case 1n+remaining:
      +center = pack(List.take(&2, U32, cells, width))
      +rest = List.drop(&2, U32, cells, width)
      south = pack(List.take(&2, U32, rest, width))
      List.append(&2, U32,
        unpack(width, pulse(north, center, south)),
        sweep(remaining, width, rest, center)
      )

def step(width: U32, height: U32, cells: List<&2, U32>) -> List<&2, U32>:
  sweep(U32.to_nat(height), U32.to_nat(width), cells, 0)

def evolve(
  turns: Nat, +width: U32, +height: U32, cells: List<&2, U32>
) -> List<&2, U32>:
  match turns:
    case 0n:
      cells
    case 1n+rest:
      evolve(rest, width, height, step(width, height, cells))
