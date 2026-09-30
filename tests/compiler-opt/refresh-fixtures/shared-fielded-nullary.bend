type Flag is Data:
  Off{}
  On{}
type RefreshPeano is Data:
  RefreshZero{}
  RefreshSucc{pred: RefreshPeano}

def observe(n: RefreshPeano) -> Flag:
  match n:
    case RefreshZero{}: On{}
    case RefreshSucc{p}: Off{}
def use(a: RefreshPeano, b: RefreshPeano) -> Flag:
  observe(b)
def main() -> Flag:
  +z : RefreshPeano = RefreshZero{}
  use(z,z)
