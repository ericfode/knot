# A list literal of generic Result elements, `[Done{..},Fail{..}]`, typed
# `List<&2,Result<..>>` (the shape of per-declaration results in src/check.bend).
import Base

type Flag is Data:
  Off{}
  On{}

type Tally is Type:
  Clean{}
  OneFail{}
  Failures{}

type Pick is Type:
  AllDone{}
  Mixed{}
  AllFail{}

def bump(t: Tally) -> Tally:
  match t:
    case Clean{}: OneFail{}
    case OneFail{}: Failures{}
    case Failures{}: Failures{}

def failures(xs: List<&2,Result<&2,&2,Flag,Flag>>) -> Tally:
  match xs:
    case Nil{}: Clean{}
    case Con{Fail{e},rest}: bump(failures(rest))
    case Con{Done{v},rest}: failures(rest)

def results(p: Pick) -> List<&2,Result<&2,&2,Flag,Flag>>:
  match p:
    case AllDone{}: [Done{On{}},Done{Off{}}]
    case Mixed{}: [Done{On{}},Fail{Off{}},Done{Off{}}]
    case AllFail{}: [Fail{On{}},Fail{Off{}}]

def probe(p: Pick) -> Tally:
  failures(results(p))

def main() -> Tally:
  probe(Mixed{})
