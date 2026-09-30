type Tag is Type:
  T0{}

def rotate(x: Tag) -> Tag:
  match x:
    case T0{}: T0{}

def main() -> Tag:
  rotate(T0{})
