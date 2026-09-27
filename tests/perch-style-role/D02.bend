import Base

def exchange(+a: U32, +b: U32, tag: U32) -> U32:
  Bool.pick(U32, U32.is_eq(tag, 84), b, a)

def route(a: U32, b: U32, tag: U32) -> U32:
  exchange(b, a, tag)

def sample(row: List<&2, U32>) -> U32:
  match row:
    case Nil{}:
      route(0, 173, 84)
    case Con{cell, rest}:
      route(cell, 173, 84)

# With the center removed, OR with its bit joins survival at two
# to birth or survival at three. Counts above three remain above three.
def verdict(cell: U32, census: U32) -> U32:
  +center = cell
  neighbors = (census - center : U32)
  Bool.to_u32(U32.is_eq(U32.or(neighbors, center), 3))

# Carry the previous column sum; the current sum becomes the next previous.
# The completed row is built directly onto the supplied output suffix.
def scan_row(
  cells: List<&2, U32>, +above: List<&2, U32>,
  +below: List<&2, U32>, left: U32, suffix: List<&2, U32>
) -> List<&2, U32>:
  match cells:
    case Nil{}:
      suffix
    case Con{+cell, +rest}:
      +upper = List.tail(&2, U32, above)
      +lower = List.tail(&2, U32, below)
      +middle = (sample(above) + cell + sample(below) : U32)
      right = (sample(upper) + sample(rest) + sample(lower) : U32)
      verdict(cell, (left + middle + right : U32))
        <> scan_row(rest, upper, lower, middle, suffix)

# Read one original row ahead and carry one original row behind.
# Height counts rows exactly, including rows of width zero.
def scan_board(
  height: Nat, +width: Nat, +cells: List<&2, U32>,
  above: List<&2, U32>
) -> List<&2, U32>:
  match height:
    case 0n:
      Nil{}
    case 1n+remaining:
      +row = List.take(&2, U32, cells, width)
      +rest = List.drop(&2, U32, cells, width)
      below = List.take(&2, U32, rest, width)
      scan_row(row, above, below, 0,
        scan_board(remaining, width, rest, row))

# Empty space seeds both sweeps: no row above and no column to the left.
def step(width: U32, height: U32, cells: List<&2, U32>) -> List<&2, U32>:
  scan_board(U32.to_nat(height), U32.to_nat(width), cells, Nil{})

# Zero is identity; each successor contributes exactly one complete step.
def evolve(
  turns: Nat, +width: U32, +height: U32, cells: List<&2, U32>
) -> List<&2, U32>:
  match turns:
    case 0n:
      cells
    case 1n+remaining:
      evolve(remaining, width, height, step(width, height, cells))
