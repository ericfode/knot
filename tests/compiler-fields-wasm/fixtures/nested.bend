type Flag is Data:
  Off{}
  On{}
type Inner is Type:
  Inner{left: Flag, right: Flag}
type Outer is Type:
  Outer{inner: Inner}
def read(x: Outer) -> Flag:
  match x:
    case Outer{i}:
      match i:
        case Inner{a,b}:
          b
def build(a: Flag, b: Flag) -> Outer:
  Outer{Inner{a,b}}
def observe(a: Flag, b: Flag) -> Flag:
  read(build(a,b))
def main() -> Flag:
  observe(Off{},On{})
