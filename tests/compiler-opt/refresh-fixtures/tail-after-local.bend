type Flag is Data:
  Off{}
  On{}
type RefreshPeano is Data:
  RefreshZero{}
  RefreshSucc{pred: RefreshPeano}

def last(n: RefreshPeano, x: Flag) -> Flag:
  match n:
    case RefreshZero{}: x
    case RefreshSucc{p}:
      y : Flag = x
      last(p,y)
def main() -> Flag:
  last(RefreshSucc{RefreshSucc{RefreshSucc{RefreshZero{}}}},On{})
