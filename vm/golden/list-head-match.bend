import Base

type Flag is Data:
  Off{}
  On{}

def first_on(xs: List<Flag>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{head, tail}:
      match head:
        case Off{}: False{}
        case On{}: True{}

def main() -> Bool:
  first_on(Con{On{}, Nil{}})
