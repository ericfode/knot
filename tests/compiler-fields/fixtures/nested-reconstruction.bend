type Flag is Data:
  Off{}
  On{}
type Inner is Type:
  Inner{value: Flag}
type Outer is Type:
  Outer{inner: Inner}
def again(x: Outer) -> Outer:
  match x:
    case Outer{i}:
      match i:
        case Inner{v}:
          match v:
            case Off{}:
              x
            case On{}:
              x
def main() -> Outer:
  again(Outer{Inner{On{}}})
