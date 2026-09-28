import Base

type Value is Data:
  Nought{}
  Seven{}
  Ten{}
  Hundred{}
  Mebi{}
  Largest{}
  Wrapped{}

type Shown is Data:
  Shown0{}
  Shown7{}
  Shown10{}
  Shown100{}
  ShownMebi{}
  ShownMax{}
  ShownOther{}

type Verdict is Data:
  Lost{}
  Kept{}

def value(v: Value) -> U32:
  match v:
    case Nought{}: 0
    case Seven{}: 7
    case Ten{}: 10
    case Hundred{}: 100
    case Mebi{}: 1048576
    case Largest{}: 4294967295
    case Wrapped{}: U32.add(4294967295, 1)

def shown(+s: String) -> Shown:
  Bool.pick(Shown, String.eq(s, "0"), Shown0{},
  Bool.pick(Shown, String.eq(s, "7"), Shown7{},
  Bool.pick(Shown, String.eq(s, "10"), Shown10{},
  Bool.pick(Shown, String.eq(s, "100"), Shown100{},
  Bool.pick(Shown, String.eq(s, "1048576"), ShownMebi{},
  Bool.pick(Shown, String.eq(s, "4294967295"), ShownMax{}, ShownOther{}))))))

def show(v: Value) -> Shown:
  shown(U32.show(value(v)))

def kept(+x: U32, m: Maybe<&2, U32>) -> Verdict:
  match m:
    case None{}: Lost{}
    case Some{y}: Bool.pick(Verdict, U32.is_eq(x, y), Kept{}, Lost{})

# U32.read inverts U32.show on every value.
def round(v: Value) -> Verdict:
  +x = value(v)
  kept(x, U32.read(U32.show(x)))

def main() -> Shown:
  show(Wrapped{})
