type Flag is Data:
  Off{}
  On{}
type RefreshPeano is Data:
  RefreshZero{}
  RefreshSucc{pred: RefreshPeano}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}
def parity(n: RefreshPeano) -> Flag:
  match n:
    case RefreshZero{}: Off{}
    case RefreshSucc{p}:
      y : Flag = parity(p)
      flip(y)
def main() -> Flag:
  parity(RefreshSucc{RefreshSucc{RefreshZero{}}})
