import Base

# Cell streams continue as zero beyond their finite edge.
def front(xs: List<&2, U32>) -> U32:
  match xs:
    case Nil{}:
      0
    case Con{head, _}:
      head

# The horizontal stencil carries its west cell and borrows its east cell.
def halo(row: List<&2, U32>, west: U32) -> List<&2, U32>:
  match row:
    case Nil{}:
      Nil{}
    case Con{+center, +rest}:
      east = front(rest)
      (west + center + east : U32) <> halo(rest, center)

# Three horizontal stencils make a square; removing its center makes a ring.
def pulse(
  row: List<&2, U32>,
  +north: List<&2, U32>, +center: List<&2, U32>, +south: List<&2, U32>
) -> List<&2, U32>:
  match row:
    case Nil{}:
      Nil{}
    case Con{+alive, rest}:
      +ring = (front(north)
             + front(center)
             + front(south) - alive : U32)
      next = Bool.to_u32(
        U32.is_eq(ring, 3) || (U32.is_eq(ring, 2) && U32.is_eq(alive, 1))
      )
      next <> pulse(
        rest,
        List.tail(&2, U32, north),
        List.tail(&2, U32, center),
        List.tail(&2, U32, south)
      )

# Each row consumes one width; its old center becomes the next north.
def sweep(
  height: Nat, +width: Nat, +cells: List<&2, U32>, north: List<&2, U32>
) -> List<&2, U32>:
  match height:
    case 0n:
      Nil{}
    case 1n+remaining:
      +row = List.take(&2, U32, cells, width)
      +rest = List.drop(&2, U32, cells, width)
      +center = halo(row, 0)
      south = halo(List.take(&2, U32, rest, width), 0)
      List.append(&2, U32,
        pulse(row, north, center, south),
        sweep(remaining, width, rest, center)
      )

def step(width: U32, height: U32, cells: List<&2, U32>) -> List<&2, U32>:
  sweep(U32.to_nat(height), U32.to_nat(width), cells, Nil{})

def evolve(
  turns: Nat, +width: U32, +height: U32, cells: List<&2, U32>
) -> List<&2, U32>:
  match turns:
    case 0n:
      cells
    case 1n+rest:
      evolve(rest, width, height, step(width, height, cells))
