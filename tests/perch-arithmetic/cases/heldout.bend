import Base

type Point is Data:
  Point{x: U32, y: U32}

# broken: start + len wraps, so a span past the limit can pass.
def valid_span(start: U32, len: U32, limit: U32) -> Bool:
  U32.is_le(U32.add(start,len),limit)

# broken: row * width wraps into range, so an out-of-grid row can pass.
def row_offset(row: U32, width: U32) -> U32:
  U32.mul(row,width)

def in_grid(row: U32, width: U32, cells: U32) -> Bool:
  U32.is_lt(row_offset(row,width),cells)

# broken: len + align - 1 wraps near the top, and align 0 wraps the mask.
def align_up(+len: U32, +align: U32) -> U32:
  U32.and(U32.add(len,U32.sub(align,1)),U32.not(U32.sub(align,1)))

# clean: intentional hash mixing.
def hash_word(+x: U32) -> U32:
  U32.xor(x,U32.shrn(U32.mul(x,2654435761),16n))

# clean: each subtraction has its larger operand first.
def distance(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_lt(a,b),U32.sub(b,a),U32.sub(a,b))

# clean: the constant bound is explicit.
def clamp_page(i: U32) -> U32:
  U32.min(i,4095)

# clean, no arithmetic: swaps fields.
def swap(p: Point) -> Point:
  match p:
    case Point{x,y}: Point{y,x}

# clean, no arithmetic: default on empty.
def head_or(xs: List<&2,U32>, fallback: U32) -> U32:
  match xs:
    case Nil{}: fallback
    case Con{h,t}: h

# clean, no arithmetic: string append at the IO boundary.
def main() -> IO(Unit):
  IO.print(String.append("a","b"))
