type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  P{l: Flag, r: Flag}

def f(a: Flag) -> Pair:
  match a:
    case On{}: P{On{},
      Off{}}
    case Off{}: P{Off{}, Off{}}
