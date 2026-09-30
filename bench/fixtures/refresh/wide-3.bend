type Tag is Type:
  T0{}
  T1{}
  T2{}

def rotate(x: Tag) -> Tag:
  match x:
    case T0{}: T1{}
    case T1{}: T2{}
    case T2{}: T0{}

def main() -> Tag:
  rotate(T2{})
