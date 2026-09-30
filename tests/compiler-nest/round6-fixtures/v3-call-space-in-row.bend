# CALLS: f(On{}, Off{}) ;; f(Off{}, On{})
type Flag is Data:
  Off{}
  On{}

def not(a: Flag) -> Flag:
  match a:
    case On{}: Off{}
    case Off{}: On{}

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case On{} v: not (v)
    case _ _: Off{}

def main() -> Flag:
  f(On{}, Off{})
