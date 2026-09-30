# CALLS: f(On{}, Off{}) ;; f(Off{}, On{}) ;; f(On{}, On{})
type Flag is Type:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case On {} On {}: On{}
    case _ _: Off{}

def main() -> Flag:
  f(On{}, Off{})
