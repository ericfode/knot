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
def f5(+x: T) -> T:
  g(f4(x))
def f6(+x: T) -> T:
  g(f5(x))
def f7(+x: T) -> T:
  g(f6(x))
def f8(+x: T) -> T:
  g(f7(x))
def f9(+x: T) -> T:
  g(f8(x))
def f10(+x: T) -> T:
  g(f9(x))
def f11(+x: T) -> T:
  g(f10(x))
def f12(+x: T) -> T:
  g(f11(x))
def f13(+x: T) -> T:
  g(f12(x))
def f14(+x: T) -> T:
  g(f13(x))
def f15(+x: T) -> T:
  g(f14(x))
def f16(+x: T) -> T:
  g(f15(x))
def f17(+x: T) -> T:
  g(f16(x))
def f18(+x: T) -> T:
  g(f17(x))
def f19(+x: T) -> T:
  g(f18(x))
def f20(+x: T) -> T:
  g(f19(x))
def main() -> T:
  f20(B{})
