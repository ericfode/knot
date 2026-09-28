# Twin of list-generic-field: a Maybe element inside the generic field's list.
import Base

type Flag is Data:
  Off{}
  On{}

type Count is Type:
  Absent{}
  None0{}
  One1{}
  Two2{}
  More{}

type Pick is Type:
  Nothing{}
  Single{}
  Double{}

def bump(c: Count) -> Count:
  match c:
    case Absent{}: One1{}
    case None0{}: One1{}
    case One1{}: Two2{}
    case Two2{}: More{}
    case More{}: More{}

def raised(xs: List<&2,Flag>) -> Count:
  match xs:
    case Nil{}: None0{}
    case Con{On{},rest}: bump(raised(rest))
    case Con{Off{},rest}: raised(rest)

def maybe(p: Pick) -> Maybe<&2,List<&2,Flag>>:
  match p:
    case Nothing{}: None{}
    case Single{}: Some{[On{}]}
    case Double{}: Some{[On{},None{},On{}]}

def result(p: Pick) -> Result<Flag,List<&2,Flag>>:
  match p:
    case Nothing{}: Fail{Off{}}
    case Single{}: Done{[Off{}]}
    case Double{}: Done{[On{},On{}]}

def some(m: Maybe<&2,List<&2,Flag>>) -> Count:
  match m:
    case None{}: Absent{}
    case Some{xs}: raised(xs)

def done(r: Result<Flag,List<&2,Flag>>) -> Count:
  match r:
    case Fail{f}: Absent{}
    case Done{xs}: raised(xs)

def optional(p: Pick) -> Count:
  some(maybe(p))

def checked(p: Pick) -> Count:
  done(result(p))

def main() -> Count:
  optional(Double{})
