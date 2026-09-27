import Base
import ./main.bend as S
import ./types.bend as T

def display_result(r: Result<T.Error,String>) -> String:
  match r:
    case Fail{e}: "unexpected extraction error"
    case Done{slice}: slice

def extracted(pair: S.Source & Result<T.Error,String>) -> String:
  (s,r) = pair
  display_result(r)

def built(r: Result<T.Error,S.Source>) -> String:
  match r:
    case Fail{e}: "unexpected construction error"
    case Done{s}: extracted(S.Source.extract(s,T.Span{42,1,2}))

def main() -> String:
  built(S.Source.new(42,"a😀\nβ"))
