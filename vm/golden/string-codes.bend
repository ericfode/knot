import Base

type Codes is Data:
  Stop{}
  Code{n: Nat, rest: Codes}

def codes(s: String) -> Codes:
  match s:
    case SNil{}: Stop{}
    case SCon{c,r}: Code{U32.to_nat(Char.to_u32(c)),codes(r)}

def main() -> Codes:
  codes(String.append(String.reverse("ab"),U32.show(12)))
