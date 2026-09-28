# Mutually recursive Term and Bind through Maybe and List, the shape of
# C.Term and C.Binding: built, matched and traversed with fuel.
import Base

type Term is Data:
  Var{bound: Bool}
  Let{binds: List<&2,Bind>, body: Term}

type Bind is Data:
  Bind{value: Maybe<&2,Term>}

# One dispatcher walks both types; the seed admits no mutually recursive defs.
type Work is Data:
  OnTerm{term: Term}
  OnBinds{binds: List<&2,Bind>}

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

def walk(fuel: Nat, work: Work) -> Verdict:
  match fuel work:
    case _ OnTerm{Var{True{}}}: Closed{}
    case _ OnTerm{Var{False{}}}: Open{}
    case _ OnBinds{Nil{}}: Closed{}
    case 0n _: Starved{}
    case 1n+ +n OnTerm{Let{xs,body}}: meet(walk(n,OnBinds{xs}),walk(n,OnTerm{body}))
    case 1n+ +n OnBinds{Con{Bind{None{}},rest}}: walk(n,OnBinds{rest})
    case 1n+ +n OnBinds{Con{Bind{Some{t}},rest}}: meet(walk(n,OnTerm{t}),walk(n,OnBinds{rest}))

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
  walk(budget(b),OnTerm{shape(s)})

def main() -> Verdict:
  probe(B9{},Free{})
