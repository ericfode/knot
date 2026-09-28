# CALLS: f(On{}, Off{}) ;; f(Off{}, On{}) ;; f(On{}, On{})
type Flag is Type:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def g(p: P) -> Flag:
  match p:
    case P {x, y}: x

def f(a: Flag, b: Flag) -> Flag:
  g(P{a, b})

def main() -> Flag:
  f(On{}, Off{})
