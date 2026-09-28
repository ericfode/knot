# A list literal of list literals: the element type reaches every inner [..] and [].
import Base

type Flag is Data:
  Off{}
  On{}

def head(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: h

def row(xss: List<&2,List<&2,Flag>>) -> List<&2,Flag>:
  match xss:
    case Nil{}: Nil{}
    case Con{h,t}: h

def later(xss: List<&2,List<&2,Flag>>) -> Flag:
  match xss:
    case Nil{}: Off{}
    case Con{h,t}: head(row(t))

def grid(a: Flag, b: Flag) -> Flag:
  later([[a],[b],[]])

def gap(a: Flag, b: Flag) -> Flag:
  later([[a],[],[b]])

def main() -> Flag:
  grid(Off{},On{})
