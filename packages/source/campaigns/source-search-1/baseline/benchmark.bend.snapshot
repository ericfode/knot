import Base
import ./main.bend as S
import ./types.bend as T
import ./observations.bend as O

def corpus(n: Nat, acc: String) -> String:
  match n:
    case 0n: acc
    case 1n+p: corpus(p,SCon{'x',SCon{'\n',acc}})

def checked_location(+i: U32, ok: Bool, pair: S.Source & Result<T.Error,T.Location>) -> S.Source & Bool:
  (s,r) = pair
  (s,Bool.and(ok,O.locs_eq(r,Done{T.Location{(i / 2 : U32),(i % 2 : U32)}})))

def expected_char(eof: Bool, even: Bool) -> Result<T.Error,Char>:
  match eof even:
    case True{} _: Fail{T.Bounds{}}
    case False{} True{}: Done{'x'}
    case False{} False{}: Done{'\n'}

def checked_char(+i: U32, n: U32, ok: Bool, pair: S.Source & Result<T.Error,Char>) -> S.Source & Bool:
  (s,r) = pair
  checked_location(i,Bool.and(ok,O.chars_eq(r,expected_char(U32.is_eq(i,n),U32.is_eq((i % 2 : U32),0)))),S.Source.locate(s,i))

def scan(fuel: Nat, +i: U32, +n: U32, pair: S.Source & Bool) -> S.Source & Bool:
  match fuel:
    case 0n: pair
    case 1n+p:
      (s,ok) = pair
      scan(p,(i + 1 : U32),n,checked_char(i,n,ok,S.Source.get(s,i)))

def finish(pair: S.Source & Bool) -> Bool:
  (s,ok) = pair
  ok

def built(+n: U32, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: finish(scan(U32.to_nat((n + 1 : U32)),0,n,(s,True{})))

def workload(+pairs: Nat) -> U32:
  Bool.to_u32(built((U32.from_nat(pairs) * 2 : U32),S.Source.new(7,corpus(pairs,""))))
