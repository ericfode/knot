type Flag is Data:
  Off{}
  On{}

type Flags is Data:
  Stop{}
  Push{head: Flag, tail: Flags}

def last(xs: Flags, d: Flag) -> Flag:
  match xs:
    case Stop{}: d
    case Push{h,t}: last(t,h)

def main() -> Flag:
  last(Push{Off{},Push{On{},Stop{}}},Off{})
