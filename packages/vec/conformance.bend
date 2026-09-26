import Base
import ./trace.bend as T
import ./model.bend as M

def empty() -> Bool:
  T.trace(0,[M.Get{0},M.Set{0,9},M.Swap{0,7},M.Pop{},M.Reserve{0},M.Slice{0,0},M.Push{8},M.Reserve{1}])

def growth_values() -> Bool:
  T.trace(17,[M.Push{11},M.Push{23},M.Push{37},M.Push{49},M.Push{61},M.Reserve{17},M.Get{0},M.Get{4},M.Slice{0,5}])

def logical_bounds() -> Bool:
  T.trace(17,[M.Push{11},M.Push{23},M.Push{37},M.Reserve{17},M.Get{3},M.Get{32},M.Set{31,9},M.Swap{4294967295,8},M.Get{4294967295},M.Get{0}])

def updates() -> Bool:
  T.trace(8,[M.Push{11},M.Push{23},M.Push{37},M.Set{1,99},M.Get{1},M.Get{0},M.Get{2},M.Swap{1,7},M.Get{1},M.Swap{0,5},M.Slice{0,3}])

def push_pop() -> Bool:
  T.trace(8,[M.Push{11},M.Push{23},M.Push{37},M.Pop{},M.Push{49},M.Pop{},M.Pop{},M.Get{0},M.Pop{},M.Pop{},M.Push{61},M.Get{0}])

def ranges() -> Bool:
  T.trace(8,[M.Push{11},M.Push{23},M.Push{37},M.Push{49},M.Push{61},M.Slice{1,4},M.Slice{5,5},M.Slice{0,0},M.Slice{0,6},M.Slice{4,3},M.Slice{4294967295,0},M.Slice{0,5}])

def limits() -> Bool:
  T.trace(3,[M.Reserve{4294967295},M.Push{11},M.Push{23},M.Push{37},M.Push{49},M.Reserve{4},M.Reserve{3},M.Pop{},M.Push{61},M.Get{2}])

def selected(m: Maybe<&2,M.Op>) -> M.Op:
  match m:
    case None{}: M.Pop{}
    case Some{x}: x

def alphabet() -> List<&2,M.Op>:
  [M.Push{7},M.Push{19},M.Pop{},M.Get{0},M.Get{1},M.Get{3},M.Get{4294967295},M.Set{0,31},M.Swap{1,43},M.Reserve{0},M.Reserve{3},M.Reserve{4},M.Reserve{4294967295},M.Slice{0,0},M.Slice{0,2},M.Slice{1,0}]

def decode(n: Nat, +code: U32) -> List<&2,M.Op>:
  match n:
    case 0n: Nil{}
    case 1n+p:
      Con{selected(List.get(&2,M.Op,alphabet(),U32.to_nat(U32.and(code,15)))),decode(p,U32.div(code,16))}

def exhaustive(n: Nat, +code: U32) -> Bool:
  match n:
    case 0n: True{}
    case 1n+p:
      +ops = decode(3n,code)
      Bool.and(T.trace(0,ops),Bool.and(T.trace(3,ops),Bool.and(T.trace(17,ops),exhaustive(p,U32.add(code,1)))))

def named() -> Bool:
  Bool.and(empty(),Bool.and(growth_values(),Bool.and(logical_bounds(),Bool.and(updates(),Bool.and(push_pop(),Bool.and(ranges(),limits()))))))

def main() -> Bool:
  Bool.and(named(),exhaustive(4096n,0))
