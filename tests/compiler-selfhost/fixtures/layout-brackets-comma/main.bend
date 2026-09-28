# Twin of layout-brackets: a doubled comma on the list's continuation line.
import Base

type Flag is Data:
  Off{}
  On{}

type Count is Type:
  None0{}
  One1{}
  Two2{}
  Three3{}
  More{}

def bump(c: Count) -> Count:
  match c:
    case None0{}: One1{}
    case One1{}: Two2{}
    case Two2{}: Three3{}
    case Three3{}: More{}
    case More{}: More{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def raised(xs: List<&2,Flag>) -> Count:
  match xs:
    case Nil{}: None0{}
    case Con{On{},rest}: bump(raised(rest))
    case Con{Off{},rest}: raised(rest)

def spread(+a: Flag, +b: Flag) -> Count:
  raised([a,flip(a),b,
    flip(b),,a,
    b])

def main() -> Count:
  spread(On{},On{})
