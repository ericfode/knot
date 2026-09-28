# Twin of rose-tree: a child list is given a single tree.
import Base

type Rose is Data:
  Rose{label: Bool, kids: List<&2,Rose>}

type Count is Type:
  Starved{}
  None0{}
  One1{}
  Two2{}
  More{}

type Budget is Type:
  B1{}
  B3{}
  B9{}

type Shape is Type:
  Bare{}
  Fan{}
  Deep{}

def bump(c: Count) -> Count:
  match c:
    case Starved{}: Starved{}
    case None0{}: One1{}
    case One1{}: Two2{}
    case Two2{}: More{}
    case More{}: More{}

def plus(a: Count, b: Count) -> Count:
  match a:
    case Starved{}: Starved{}
    case None0{}: b
    case One1{}: bump(b)
    case Two2{}: bump(bump(b))
    case More{}:
      match b:
        case Starved{}: Starved{}
        case None0{}: More{}
        case One1{}: More{}
        case Two2{}: More{}
        case More{}: More{}

def marked(fuel: Nat, forest: List<&2,Rose>) -> Count:
  match fuel forest:
    case _ Nil{}: None0{}
    case 0n Con{tree,rest}: Starved{}
    case 1n+ +n Con{Rose{True{},kids},rest}: bump(plus(marked(n,kids),marked(n,rest)))
    case 1n+ +n Con{Rose{False{},kids},rest}: plus(marked(n,kids),marked(n,rest))

def leaf(label: Bool) -> Rose:
  Rose{label,Nil{}}

def tree(s: Shape) -> Rose:
  match s:
    case Bare{}: leaf(False{})
    case Fan{}: Rose{False{},leaf(True{})}
    case Deep{}: Rose{True{},Con{Rose{False{},Con{Rose{True{},Nil{}},Nil{}}},Nil{}}}

def budget(b: Budget) -> Nat:
  match b:
    case B1{}: 1n
    case B3{}: 3n
    case B9{}: 9n

def probe(b: Budget, s: Shape) -> Count:
  marked(budget(b),Con{tree(s),Nil{}})

def main() -> Count:
  probe(B9{},Fan{})
