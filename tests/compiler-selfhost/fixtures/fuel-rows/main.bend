# A fuel dispatcher in src/parse.bend's shape: `match fuel mode:` with a
# `case 0n _` row and `case 1n+ +n K{..}` rows whose predecessor is reused.
import Base

type Level is Type:
  Starved{}
  Shallow{}
  Full{}

type Mode is Data:
  Root{}
  Twice{inner: Mode}
  Leaf{}

type Budget is Type:
  B0{}
  B1{}
  B2{}
  B3{}

type Start is Type:
  AtRoot{}
  AtTwice{}
  AtLeaf{}

def meet(a: Level, b: Level) -> Level:
  match a b:
    case Starved{} _: Starved{}
    case _ Starved{}: Starved{}
    case Full{} Full{}: Full{}
    case _ _: Shallow{}

def run(fuel: Nat, mode: Mode) -> Level:
  match fuel mode:
    case 0n _: Starved{}
    case 1n+ +n Root{}: run(n,Twice{Leaf{}})
    case 1n+ +n Twice{+inner}: meet(run(n,inner),run(n,Leaf{}))
    case 1n+ +n Leaf{}: Full{}

def budget(b: Budget) -> Nat:
  match b:
    case B0{}: 0n
    case B1{}: 1n
    case B2{}: 2n
    case B3{}: 3n

def mode(s: Start) -> Mode:
  match s:
    case AtRoot{}: Root{}
    case AtTwice{}: Twice{Twice{Leaf{}}}
    case AtLeaf{}: Leaf{}

def probe(b: Budget, s: Start) -> Level:
  run(budget(b),mode(s))

def main() -> Level:
  probe(B3{},AtRoot{})
