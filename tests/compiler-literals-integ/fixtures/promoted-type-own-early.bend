# The type may be the scrutinee's own, declared before the function.
type Early is Data:
  E0{}
  E1{}

type Flag is Data:
  Off{}
  On{}

def f(x: Early) -> Flag:
  match x:
    case E0{}: On{}
    case +Early: Off{}

def main() -> Flag:
  f(E1{})
