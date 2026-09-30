type Flag is Data:
  Off{}
  On{}

type N is Data:
  Z{}
  S{pred: N}

def f(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}:
      match p:
        case Z{}: On{}
        case S{r}: On{}

def main() -> Flag:
  f(S{Z{}})
