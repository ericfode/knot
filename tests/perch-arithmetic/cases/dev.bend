import Base

type Flag is Data:
  Off{}
  On{}

type Cell is Data:
  Cell{id: U32, tag: U32}

# broken: capacity - used is a count, but used can exceed capacity and wrap.
def free_slots(capacity: U32, used: U32) -> U32:
  U32.sub(capacity,used)

def reserve(capacity: U32, used: U32, wanted: U32) -> Bool:
  U32.is_le(wanted,free_slots(capacity,used))

# broken: the mask only wraps inside a power-of-two size; size 0 masks with all ones.
def slot(index: U32, size: U32) -> U32:
  U32.and(index,U32.sub(size,1))

# broken: count * 8 wraps for large counts, so the page check can pass.
def bytes_needed(count: U32) -> U32:
  U32.mul(count,8)

def fits_page(count: U32) -> Bool:
  U32.is_le(bytes_needed(count),65536)

# clean: intentional modular arithmetic.
def next_random(state: U32) -> U32:
  U32.xor(U32.mul(state,1664525),1013904223)

# clean: the subtraction is ordered by the guard.
def free_slots_guarded(+capacity: U32, +used: U32) -> U32:
  Bool.pick(U32,U32.is_lt(used,capacity),U32.sub(capacity,used),0)

# clean: the increment is bounded.
def next_id(+counter: U32) -> Maybe<&2,U32>:
  Bool.pick(Maybe<&2,U32>,U32.is_lt(counter,4294967295),Some{U32.add(counter,1)},None{})

# clean, no arithmetic: constructor only.
def on() -> Flag:
  On{}

# clean, no arithmetic: match only.
def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

# clean, no arithmetic: host boundary with a literal.
def main() -> IO(Unit):
  IO.print("hello")
