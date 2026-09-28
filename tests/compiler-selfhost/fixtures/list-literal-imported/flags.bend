# Local module for list-literal-imported: list literals in a non-entry module.
import Base

type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def pattern(+x: Flag) -> List<&2,Flag>:
  [x,flip(x),Off{}]

def empty() -> List<&2,Flag>:
  []
