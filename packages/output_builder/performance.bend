import Base
import ./main.bend as B
import ./bytes.bend as Y
import ./conformance.bend as T

def build(n: Nat, +chunk: String, acc: B.Builder) -> B.Builder:
  match n:
    case 0n:
      acc
    case 1n+p:
      build(p,chunk,B.append(acc,chunk))

def expected(n: Nat, +chunk: String) -> String:
  match n:
    case 0n:
      ""
    case 1n+p:
      String.append(chunk,expected(p,chunk))

def uneven(n: Nat, +long: String, acc: B.Builder) -> B.Builder:
  match n:
    case 0n:
      acc
    case 1n+p:
      uneven(p,long,B.compose(acc,B.compose(B.fragment("x"),B.fragment(long))))

def bytes_build(n: Nat, result: Result<Y.Error,Y.Builder>) -> Result<Y.Error,Y.Builder>:
  match n result:
    case 0n Fail{err}:
      Fail{err}
    case 0n Done{b}:
      Done{b}
    case 1n+p Fail{err}:
      Fail{err}
    case 1n+p Done{b}:
      bytes_build(p,Y.byte(b,97))

# Census of the actual input tree: node visits, copied characters.
def add_census(a: Nat & Nat, b: Nat & Nat) -> Nat & Nat:
  (ak,an) = a
  (bk,bn) = b
  (1n+Nat.add(ak,bk),Nat.add(an,bn))

def print_census(a: Nat & Nat, b: Nat & Nat) -> IO(Unit):
  (k,chars) = a
  (mk,mchars) = b
  IO.print(Nat.show(k) ++ "," ++ Nat.show(chars) ++ "," ++ Nat.show(mk) ++ "," ++ Nat.show(mchars))

def census(t: B.Builder) -> Nat & Nat:
  match t:
    case B.Empty{}:
      (1n,0n)
    case B.Chunk{s}:
      (1n,String.length(s))
    case B.Join{a,b}:
      add_census(census(a),census(b))

def run(+n: Nat) -> IO(Unit):
  +tiny = build(n,"x",B.empty())
  +long = expected(127n,"λ")
  +mixed = uneven(n,long,B.empty())
  do IO<Unit>:
    T.assert(String.eq(B.finish(tiny),expected(n,"x")),"tiny-content")
    T.assert(String.eq(B.finish(mixed),expected(n,String.append("x",long))),"uneven-content")
    T.assert(String.eq(B.finish(build(n,"",B.empty())),""),"empty-fragments")
    T.assert(T.success(bytes_build(n,Done{Y.empty(U32.from_nat(n))}),List.replicate(U32,n,97),U32.from_nat(n),U32.from_nat(n)),"byte-tiny-content")
    print_census(census(tiny),census(mixed))
