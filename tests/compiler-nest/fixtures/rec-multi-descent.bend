# Structural recursion over two scrutinees; the first argument shrinks, the second is free.
type Flag is Data:
  Off{}
  On{}

type Digit is Data:
  D0{}
  D1{}
  D2{}
  D3{}

type N is Data:
  Z{}
  S{pred: N}

def less(a: N, b: N) -> Flag:
  match a b:
    case Z{} S{_}: On{}
    case S{x} S{y}: less(x, y)
    case _ _: Off{}

def num(d: Digit) -> N:
  match d:
    case D0{}: Z{}
    case D1{}: S{Z{}}
    case D2{}: S{S{Z{}}}
    case D3{}: S{S{S{Z{}}}}

def lt(a: Digit, b: Digit) -> Flag:
  less(num(a), num(b))

def main() -> Flag:
  lt(D1{}, D3{})
