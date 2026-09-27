type Flag is Data:
  Off{}
  On{}
type Inner is Type:
  Inner{value: Flag}
type Outer is Type:
  Outer{inner: Inner}
def open(x: Outer) -> Flag:
  match x:
    case Outer{Inner{v}}:
      v
def main() -> Flag:
  open(Outer{Inner{On{}}})
