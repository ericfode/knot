# Structural recursion on a grandchild bound by a nested pattern.
type Flag is Data:
  Off{}
  On{}

type Digit is Data:
  D0{}
  D1{}
  D2{}
  D3{}
  D4{}
  D5{}

type N is Data:
  Z{}
  S{pred: N}

def even(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{Z{}}: Off{}
    case S{S{m}}: even(m)

def num(d: Digit) -> N:
  match d:
    case D0{}: Z{}
    case D1{}: S{Z{}}
    case D2{}: S{S{Z{}}}
    case D3{}: S{S{S{Z{}}}}
    case D4{}: S{S{S{S{Z{}}}}}
    case D5{}: S{S{S{S{S{Z{}}}}}}

def parity(d: Digit) -> Flag:
  even(num(d))

def main() -> Flag:
  parity(D4{})
