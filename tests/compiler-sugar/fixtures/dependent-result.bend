# The core.invalid shape: -A: Type appears only in the result, instantiated by a name and an application.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Outcome<-A: Type> is Type:
  Failed{code: Flag}
  Passed{value: A}

def failed(-A: Type, code: Flag) -> Outcome<A>:
  Failed{code}

def status(-A: Type, o: Outcome<A>) -> Flag:
  match o:
    case Failed{c}: c
    case Passed{v}: Off{}

def plain(x: Flag) -> Flag:
  status(Color,failed(Color,x))

def applied(x: Flag) -> Flag:
  status(Outcome<Flag>,failed(Outcome<Flag>,x))

def passed(x: Flag) -> Flag:
  status(Flag,Passed{x})

def main() -> Flag:
  applied(On{})
