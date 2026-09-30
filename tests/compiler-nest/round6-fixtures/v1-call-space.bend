# CALLS: f(On{}, Off{}) ;; f(Off{}, On{})
type Flag is Data:
  Off{}
  On{}

def not(a: Flag) -> Flag:
  match a:
    case On{}: Off{}
    case Off{}: On{}

def f(x: Flag, y: Flag) -> Flag:
  not (x)

def main() -> Flag:
  f(On{}, Off{})
