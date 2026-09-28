# Twin of list-literal-imported: the entry's list mixes a flag list into flags.
import Base
import ./flags.bend as F

type Count is Type:
  None0{}
  One1{}
  Two2{}
  Three3{}
  More{}

type Pick is Type:
  WithOff{}
  WithOn{}
  Blank{}

def bump(c: Count) -> Count:
  match c:
    case None0{}: One1{}
    case One1{}: Two2{}
    case Two2{}: Three3{}
    case Three3{}: More{}
    case More{}: More{}

def raised(xs: List<&2,F.Flag>) -> Count:
  match xs:
    case Nil{}: None0{}
    case Con{F.On{},rest}: bump(raised(rest))
    case Con{F.Off{},rest}: raised(rest)

def length(xs: List<&2,F.Flag>) -> Count:
  match xs:
    case Nil{}: None0{}
    case Con{x,rest}: bump(length(rest))

def source(p: Pick) -> List<&2,F.Flag>:
  match p:
    case WithOff{}: F.pattern(F.Off{})
    case WithOn{}: F.pattern(F.On{})
    case Blank{}: [F.Off{},F.empty()]

def ons(p: Pick) -> Count:
  raised(source(p))

def size(p: Pick) -> Count:
  length(source(p))

def main() -> Count:
  size(WithOn{})
