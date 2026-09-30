type Flag is Data:
  Off{}
  On{}
type RefreshPeano is Data:
  RefreshZero{}
  RefreshSucc{pred: RefreshPeano}

def copy(n: RefreshPeano) -> RefreshPeano:
  match n:
    case RefreshZero{}: RefreshZero{}
    case RefreshSucc{p}: RefreshSucc{copy(p)}
def nonzero(n: RefreshPeano) -> Flag:
  match n:
    case RefreshZero{}: Off{}
    case RefreshSucc{p}: On{}
def main() -> Flag:
  nonzero(copy(RefreshSucc{RefreshSucc{RefreshZero{}}}))
