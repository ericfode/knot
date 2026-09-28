type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
type Row is Data:
  End{}
  Row{a: Peano, b: Peano, c: Peano, d: Peano, e: Peano, f: Peano, g: Peano, h: Peano, tail: Row}
def double(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: Succ{Succ{double(p)}}
def build(n: Peano) -> Row:
  match n:
    case Zero{}: End{}
    case Succ{p}:
      +z : Peano = Zero{}
      Row{z,z,z,z,z,z,z,z,build(p)}
def last(x: Row) -> Flag:
  match x:
    case End{}: On{}
    case Row{a,b,c,d,e,f,g,h,tail}: last(tail)
def main() -> Flag:
  last(build(double(double(double(Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}})))))
