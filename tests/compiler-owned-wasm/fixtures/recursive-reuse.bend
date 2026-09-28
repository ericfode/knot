type Flag is Data:
  Off{}
  On{}
type Count is Data:
  Zero{}
  Succ{pred: Count}
type Box is Type:
  Box{value: Flag}
def read(box: Box) -> Flag:
  match box:
    case Box{v}: v
def loop(count: Count) -> Flag:
  match count:
    case Zero{}: read(Box{On{}})
    case Succ{p}:
      unused = read(Box{Off{}})
      loop(p)
def input() -> Count:
  Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
def f0() -> Flag:
  loop(input())
def f1() -> Flag:
  unused = f0()
  f0()
def f2() -> Flag:
  unused = f1()
  f1()
def f3() -> Flag:
  unused = f2()
  f2()
def f4() -> Flag:
  unused = f3()
  f3()
def f5() -> Flag:
  unused = f4()
  f4()
def f6() -> Flag:
  unused = f5()
  f5()
def f7() -> Flag:
  unused = f6()
  f6()
def f8() -> Flag:
  unused = f7()
  f7()
def f9() -> Flag:
  unused = f8()
  f8()
def main() -> Flag:
  f9()
