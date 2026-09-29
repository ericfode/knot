# A type declared after the function is no type yet: the promoted binder is a fresh name.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case +Later: Off{}

type Later is Data:
  L{}

def main() -> Flag:
  f(On{})
