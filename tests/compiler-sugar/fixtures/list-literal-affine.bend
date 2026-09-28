# An affine List<&1,..> literal of Type values: the D.concat shape, and a list of pairs.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Part is Type:
  Bad{code: Flag}
  Good{color: Color}

def color(p: Part) -> Color:
  match p:
    case Bad{e}: Red{}
    case Good{c}: c

def settle(parts: List<&1,Part>) -> Color:
  match parts:
    case Nil{}: Red{}
    case Con{p,tail}: color(p)

def part(f: Flag, c: Color) -> Part:
  match f:
    case Off{}: Bad{Off{}}
    case On{}: Good{c}

def right(p: Flag & Color) -> Color:
  (f,c) = p
  c

def pairs(ps: List<&1,Flag & Color>) -> Color:
  match ps:
    case Nil{}: Red{}
    case Con{p,tail}: right(p)

def parts(f: Flag, c: Color) -> Color:
  settle([part(f,c),Good{Blue{}}])

def paired(f: Flag, c: Color) -> Color:
  pairs([(f,c),(On{},Red{})])

def main() -> Color:
  parts(On{},Blue{})
