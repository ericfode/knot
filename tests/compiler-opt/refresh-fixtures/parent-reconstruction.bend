type Flag is Data:
  Off{}
  On{}
type RefreshPair is Data:
  RefreshPair{left: Flag, right: Flag}

def retained(p: RefreshPair) -> RefreshPair:
  match p:
    case RefreshPair{left,right}: p
def project(p: RefreshPair) -> Flag:
  match p:
    case RefreshPair{left,right}: right
def main() -> Flag:
  project(retained(RefreshPair{Off{},On{}}))
