import Base

# A missing front is the supplied outside value, at either list depth.
def front(-A: Data, xs: List<&2, A>, outside: A) -> A:
  match xs:
    case Nil{}:
      outside
    case Con{head, _}:
      head

# The horizontal stencil carries its west cell and borrows its east cell.
def halo(row: List<&2, U32>, west: U32) -> List<&2, U32>:
  match row:
    case Nil{}:
      Nil{}
    case Con{+center, +east}:
      (west + center + front(U32, east, 0) : U32) <> halo(east, center)

# Three horizontal stencils make a square; removing its center makes a ring.
def pulse(
  row: List<&2, U32>,
  +north: List<&2, U32>, +center: List<&2, U32>, +south: List<&2, U32>
) -> List<&2, U32>:
  match row:
    case Nil{}:
      Nil{}
    case Con{+alive, rest}:
      +ring = (front(U32, north, 0)
             + front(U32, center, 0)
             + front(U32, south, 0) - alive : U32)
      next = Bool.to_u32(
        U32.is_eq(ring, 3) || (U32.is_eq(ring, 2) && U32.is_eq(alive, 1))
      )
      next <> pulse(
        rest,
        List.tail(&2, U32, north),
        List.tail(&2, U32, center),
        List.tail(&2, U32, south)
      )

def strips(height: Nat, +width: Nat, +cells: List<&2, U32>) ->
  List<&2, List<&2, U32>>:
  match height:
    case 0n:
      Nil{}
    case 1n+rest:
      List.take(&2, U32, cells, width) <> strips(rest, width, List.drop(&2, U32, cells, width))

# Only old rows enter the stencil; each center becomes the next row's north.
def sweep(rows: List<&2, List<&2, U32>>, north: List<&2, U32>) -> List<&2, U32>:
  match rows:
    case Nil{}:
      Nil{}
    case Con{+row, +rest}:
      +center = halo(row, 0)
      south = halo(front(List<&2, U32>, rest, Nil{}), 0)
      List.append(&2, U32,
        pulse(row, north, center, south),
        sweep(rest, center)
      )

def step(width: U32, height: U32, cells: List<&2, U32>) -> List<&2, U32>:
  sweep(strips(U32.to_nat(height), U32.to_nat(width), cells), Nil{})

def evolve(
  turns: Nat, +width: U32, +height: U32, cells: List<&2, U32>
) -> List<&2, U32>:
  match turns:
    case 0n:
      cells
    case 1n+rest:
      evolve(rest, width, height, step(width, height, cells))
