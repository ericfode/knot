# Twin of list-lambda-body: the lambda body is a flag where a list is expected.
import Base

type Flag is Data:
  Off{}
  On{}

type Count is Type:
  None0{}
  One1{}
  Two2{}
  More{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def bump(c: Count) -> Count:
  match c:
    case None0{}: One1{}
    case One1{}: Two2{}
    case Two2{}: More{}
    case More{}: More{}

def raised(xs: List<&2,Flag>) -> Count:
  match xs:
    case Nil{}: None0{}
    case Con{On{},rest}: bump(raised(rest))
    case Con{Off{},rest}: raised(rest)

def expand(x: Flag, f: Flag -> List<&2,Flag>) -> List<&2,Flag>:
  f(x)

def spread(x: Flag) -> Count:
  raised(expand(x,+y => [y,flip(y),y]))

def single(x: Flag) -> Count:
  raised(expand(x,y => y))

def main() -> Count:
  spread(On{})
