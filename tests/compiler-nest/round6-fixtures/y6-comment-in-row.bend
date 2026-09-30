# CALLS: f(On{}, Off{}, On{}) ;; f(Off{}, On{}, Off{})
type Flag is Type:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(a: Flag, b: Flag, c: Flag) -> Flag:
  match a b c:
    case On{} # first
      _ x: x
    case _ y z: y

def main() -> Flag:
  f(On{}, Off{}, On{})
