import Base
import ../../main.bend as S
import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as V

def state_equal(a: S.Search, b: S.Search) -> Bool:
  match a b:
    case S.Found{x} S.Found{y}: U32.is_eq(x,y)
    case S.BadIndex{} S.BadIndex{}: True{}
    case S.Searching{a,b} S.Searching{c,d}: Bool.and(U32.is_eq(a,c),U32.is_eq(b,d))
    case _ _: False{}

def content(xs: List<U32>) -> Bool:
  match xs:
    case Con{a,Con{b,Nil{}}}: Bool.and(U32.is_eq(a,0),U32.is_eq(b,9))
    case _: False{}

def preserved(ok: Bool, pair: V.Vec<U32> & List<U32>) -> Bool:
  (v,xs) = pair
  Bool.and(ok,content(xs))

def observed(expected: S.Search, pair: V.Vec<U32> & S.Search) -> Bool:
  (v,actual) = pair
  preserved(state_equal(expected,actual),V.Vec.to_list(U32,v))

def ready(fuel: Nat, input: S.Search, expected: S.Search, pair: V.Vec<U32> & Result<V.Error,Unit>) -> Bool:
  (v,r) = pair
  observed(expected,S.search(fuel,7,(v,input)))

def first(fuel: Nat, input: S.Search, expected: S.Search, pair: V.Vec<U32> & Result<V.Error,Unit>) -> Bool:
  (v,r) = pair
  ready(fuel,input,expected,V.Vec.push(U32,v,9))

def probe(fuel: Nat, input: S.Search, expected: S.Search) -> Bool:
  first(fuel,input,expected,V.Vec.push(U32,V.Vec.new(U32),0))

def main() -> U32:
  Bool.to_u32(Bool.and(probe(0n,S.Found{1},S.Found{1}),Bool.and(probe(3n,S.Found{1},S.Found{1}),Bool.and(probe(0n,S.BadIndex{},S.BadIndex{}),Bool.and(probe(3n,S.BadIndex{},S.BadIndex{}),Bool.and(probe(0n,S.Searching{0,2},S.BadIndex{}),Bool.and(probe(1n,S.Searching{0,2},S.BadIndex{}),Bool.and(probe(1n,S.Searching{0,1},S.Found{0}),Bool.and(probe(2n,S.Searching{0,2},S.Found{0}),probe(3n,S.Searching{0,4},S.BadIndex{}))))))))))
