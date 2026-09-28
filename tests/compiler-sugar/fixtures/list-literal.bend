# Base List literals as Knot spells them: call elements, a singleton, a constructor field.
import Base

type Flag is Data:
  Off{}
  On{}

type Batch is Type:
  Ready{items: List<&2,Flag>}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def either(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: On{}
    case Off{}: b

def any(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: either(h,any(t))

def unpack(b: Batch) -> Flag:
  match b:
    case Ready{items}: any(items)

def calls(a: Flag, b: Flag) -> Flag:
  any([invert(a),invert(b),Off{}])

def single(a: Flag) -> Flag:
  unpack(Ready{[a]})

def main() -> Flag:
  calls(On{},Off{})
