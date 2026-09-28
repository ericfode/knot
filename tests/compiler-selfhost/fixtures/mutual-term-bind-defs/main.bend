# Twin of mutual-term-bind: two mutually recursive defs instead of one dispatcher.
import Base

type Term is Data:
  Var{bound: Bool}
  Let{binds: List<&2,Bind>, body: Term}

type Bind is Data:
  Bind{value: Maybe<&2,Term>}

type Verdict is Type:
  Starved{}
  Closed{}
  Open{}

type Budget is Type:
  B2{}
  B9{}

type Shape is Type:
  Leaf{}
  Holes{}
  Nested{}
  Free{}

def meet(a: Verdict, b: Verdict) -> Verdict:
  match a:
    case Starved{}: Starved{}
    case Closed{}: b
    case Open{}:
      match b:
        case Starved{}: Starved{}
        case Closed{}: Open{}
        case Open{}: Open{}

def binds(fuel: Nat, xs: List<&2,Bind>) -> Verdict:
  match fuel xs:
    case _ Nil{}: Closed{}
    case 0n Con{x,rest}: Starved{}
    case 1n+ +n Con{Bind{None{}},rest}: binds(n,rest)
    case 1n+ +n Con{Bind{Some{t}},rest}: meet(term(n,t),binds(n,rest))

def term(fuel: Nat, t: Term) -> Verdict:
  match fuel t:
    case _ Var{True{}}: Closed{}
    case _ Var{False{}}: Open{}
    case 0n Let{xs,body}: Starved{}
    case 1n+ +n Let{xs,body}: meet(binds(n,xs),term(n,body))

def shape(s: Shape) -> Term:
  match s:
    case Leaf{}: Var{True{}}
    case Holes{}: Let{Con{Bind{None{}},Con{Bind{Some{Var{True{}}}},Nil{}}},Var{True{}}}
    case Nested{}: Let{Con{Bind{Some{Let{Nil{},Var{True{}}}}},Nil{}},Let{Nil{},Var{True{}}}}
    case Free{}: Let{Con{Bind{Some{Var{False{}}}},Nil{}},Var{True{}}}

def budget(b: Budget) -> Nat:
  match b:
    case B2{}: 2n
    case B9{}: 9n

def probe(b: Budget, s: Shape) -> Verdict:
  term(budget(b),shape(s))

def main() -> Verdict:
  probe(B9{},Free{})
