# List separators the seed accepts: none, a trailing comma, inner spaces, and the empty [].
import Base

type Flag is Data:
  Off{}
  On{}

def head(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: h

def second(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: head(t)

def pick(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: On{}

def bare(a: Flag, b: Flag) -> Flag:
  second([a b])

def trailing(a: Flag, b: Flag) -> Flag:
  second([a,b,])

def spaced(a: Flag, b: Flag) -> Flag:
  second([ a , b ])

def empty(a: Flag) -> Flag:
  pick(a,head([]))

def main() -> Flag:
  bare(Off{},On{})
