# CALLS: f(On{}, Off{}, On{}) ;; f(Off{}, On{}, Off{})
type Flag is Type:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def g(p: P) -> Flag:
  match p:
    case P{ On{} , y }: y
    case P { x, _ }: x

def f(a: Flag, b: Flag, c: Flag) -> Flag:
  g(P{a, b})

def main() -> Flag:
  f(On{}, Off{}, On{})
