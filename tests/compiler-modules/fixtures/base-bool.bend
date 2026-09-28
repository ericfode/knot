import Base

type Light is Type:
  Dark{}
  Lit{}

def bit(x: Light) -> Bool:
  match x:
    case Dark{}: False{}
    case Lit{}: True{}

def see(x: Bool) -> Light:
  match x:
    case False{}: Dark{}
    case True{}: Lit{}

def differ(a: Light, b: Light) -> Light:
  see(Bool.xor(bit(a), bit(b)))

def main() -> Light:
  see(Bool.and(Bool.not(False{}), Bool.or(False{}, True{})))
