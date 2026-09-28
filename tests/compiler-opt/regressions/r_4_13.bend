type T is Data:
  A{}
  B{}
def f0(+x: T) -> T:
  A{}
def g(+y: T) -> T:
  match y:
    case A{}: A{}
    case B{}:
      u0 : T = B{}
      u1 : T = B{}
      u2 : T = B{}
      u3 : T = B{}
      u4 : T = B{}
      u5 : T = B{}
      u6 : T = B{}
      u7 : T = B{}
      u8 : T = B{}
      u9 : T = B{}
      u10 : T = B{}
      u11 : T = B{}
      u12 : T = B{}
      A{}
def f1(+x: T) -> T:
  g(f0(x))
def f2(+x: T) -> T:
  g(f1(x))
def f3(+x: T) -> T:
  g(f2(x))
def f4(+x: T) -> T:
  g(f3(x))
def main() -> T:
  f4(B{})
