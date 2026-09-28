type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def read(x: Box) -> Flag:
  match x:
    case Box{v}:
      v
def f0() -> Flag:
  read(Box{On{}})
def f1() -> Flag:
  x = f0()
  f0()
def f2() -> Flag:
  x = f1()
  f1()
def f3() -> Flag:
  x = f2()
  f2()
def f4() -> Flag:
  x = f3()
  f3()
def f5() -> Flag:
  x = f4()
  f4()
def f6() -> Flag:
  x = f5()
  f5()
def f7() -> Flag:
  x = f6()
  f6()
def f8() -> Flag:
  x = f7()
  f7()
def f9() -> Flag:
  x = f8()
  f8()
def f10() -> Flag:
  x = f9()
  f9()
def f11() -> Flag:
  x = f10()
  f10()
def f12() -> Flag:
  x = f11()
  f11()
def f13() -> Flag:
  x = f12()
  f12()
def f14() -> Flag:
  x = f13()
  f13()
def main() -> Flag:
  f14()
