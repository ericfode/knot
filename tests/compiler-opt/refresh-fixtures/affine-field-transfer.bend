type Flag is Data:
  Off{}
  On{}
type RefreshPair is Type:
  RefreshPair{left: Flag, right: Flag}

def retained(p: RefreshPair) -> RefreshPair:
  match p:
    case RefreshPair{left,right}: RefreshPair{left,right}
def project(p: RefreshPair) -> Flag:
  match p:
    case RefreshPair{left,right}: right
def main() -> Flag:
  project(retained(RefreshPair{Off{},On{}}))
