import Base

# Rows end in one dead sentinel; the carried column supplies the west edge.
def pulse(
  width: Nat,
  row: List<&2, U32>, north: List<&2, U32>, south: List<&2, U32>,
  nw: U32, west: U32, sw: U32
) -> List<&2, U32>:
  match width row north south:
    case 0n _ _ _:
      Nil{}
    case 1n+remaining Con{+alive, Con{+east, r}} Con{+n, Con{+ne, nt}} Con{+s, Con{+se, st}}:
      +ring = (nw + n + ne
             + west + east
             + sw + s + se : U32)
      next = Bool.to_u32(
        U32.is_eq(ring, 3) || (U32.is_eq(ring, 2) && U32.is_eq(alive, 1))
      )
      next <> pulse(remaining, east <> r, ne <> nt, se <> st, n, alive, s)
    case _ _ _ _:
      Nil{}

# The input includes one dead bottom row; only old rows move through the window.
def sweep(
  height: Nat, +width: Nat, +cells: List<&2, U32>, north: List<&2, U32>
) -> List<&2, U32>:
  match height:
    case 0n:
      Nil{}
    case 1n+remaining:
      +center = List.take(&2, U32, cells, width)
      +rest = List.drop(&2, U32, cells, width)
      south = List.take(&2, U32, rest, width)
      List.append(&2, U32,
        pulse(width,
          List.append(&2, U32, center, [0]),
          List.append(&2, U32, north, [0]),
          List.append(&2, U32, south, [0]),
          0, 0, 0
        ),
        sweep(remaining, width, rest, center)
      )

def step(width: U32, height: U32, cells: List<&2, U32>) -> List<&2, U32>:
  +span = U32.to_nat(width)
  +dead = List.replicate(U32, span, 0)
  sweep(U32.to_nat(height), span, List.append(&2, U32, cells, dead), dead)

def evolve(
  turns: Nat, +width: U32, +height: U32, cells: List<&2, U32>
) -> List<&2, U32>:
  match turns:
    case 0n:
      cells
    case 1n+rest:
      evolve(rest, width, height, step(width, height, cells))
