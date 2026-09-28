type Flag is Data:
  Off{}
  On{}

type Flags is Data:
  Stop{}
  Push{head: Flag, tail: Flags}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def flip_all(xs: Flags) -> Flags:
  match xs:
    case Stop{}: Stop{}
    case Push{h,t}: Push{flip(h),flip_all(t)}

def main() -> Flags:
  flip_all(Push{On{},Push{Off{},Stop{}}})
