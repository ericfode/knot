type Tag is Type:
  T0{}
  T1{}

def rotate(x: Tag) -> Tag:
  match x:
    case T0{}: T1{}
    case T1{}: T0{}

def main() -> Tag:
  rotate(T1{})
