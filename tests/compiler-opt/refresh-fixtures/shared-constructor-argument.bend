type Flag is Data:
  Off{}
  On{}
type RefreshPair is Data:
  RefreshPair{left: Flag, right: Flag}

def project(p: RefreshPair) -> Flag:
  match p:
    case RefreshPair{left,right}: right
def use(a: RefreshPair, b: RefreshPair) -> Flag:
  project(b)
def main() -> Flag:
  +p : RefreshPair = RefreshPair{Off{},On{}}
  use(p,p)
