# matrix.bend's own row shape over an 11-constructor node type.
type Flag is Data:
  Off{}
  On{}

type Node is Type:
  Var{}
  Prom{}
  Ctor{t: Flag, args: NL}
  Call{}
  Seq{nodes: NL}
  Arm{a: Flag, p: Node, b: Node}
  Match{}
  Alias{}
  Lit{}
  Lam{}
  App{}

type NL is Type:
  NNil{}
  NCon{h: Node, t: NL}

def ctors(rows: NL) -> Flag:
  match rows:
    case NNil{}: Off{}
    case NCon{Arm{a, Seq{NCon{Ctor{t, args}, rest}}, b}, tail}: On{}
    case NCon{head, tail}: Off{}

def main() -> Flag:
  ctors(NCon{Arm{On{}, Seq{NCon{Ctor{Off{}, NNil{}}, NNil{}}}, Var{}}, NNil{}})
