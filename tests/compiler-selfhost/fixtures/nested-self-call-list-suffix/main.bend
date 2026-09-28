# Twin of nested-self-call-list: the inner self-call passes a Tree where its suffix is a list.
import Base

type Tree is Data:
  Blank{}
  Chunk{values: List<&2,U32>}
  Join{left: Tree, right: Tree}

type Digit is Type:
  D0{}
  D1{}
  D2{}
  D3{}
  Other{}

type Pos is Type:
  P0{}
  P1{}
  P2{}
  P3{}
  P4{}

def emit(tree: Tree, suffix: List<&2,U32>) -> List<&2,U32>:
  match tree:
    case Blank{}:
      suffix
    case Chunk{values}:
      List.append(&2,U32,values,suffix)
    case Join{left,right}:
      emit(left,emit(right,Blank{}))

def small(zero: Bool, one: Bool, two: Bool, three: Bool) -> Digit:
  match zero:
    case True{}: D0{}
    case False{}:
      match one:
        case True{}: D1{}
        case False{}:
          match two:
            case True{}: D2{}
            case False{}:
              match three:
                case True{}: D3{}
                case False{}: Other{}

def digit(+x: U32) -> Digit:
  small(U32.is_eq(x,0),U32.is_eq(x,1),U32.is_eq(x,2),U32.is_eq(x,3))

def nth(xs: List<&2,U32>, p: Pos) -> Digit:
  match xs:
    case Nil{}: Other{}
    case Con{h,t}:
      match p:
        case P0{}: digit(h)
        case P1{}: nth(t,P0{})
        case P2{}: nth(t,P1{})
        case P3{}: nth(t,P2{})
        case P4{}: nth(t,P3{})

def sample() -> Tree:
  Join{Join{Chunk{Con{1,Con{2,Nil{}}}},Blank{}},Chunk{Con{0,Nil{}}}}

def at(p: Pos) -> Digit:
  nth(emit(sample(),Con{3,Nil{}}),p)

def main() -> Digit:
  at(P3{})
