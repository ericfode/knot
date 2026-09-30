type Flag is Data:
  Off{}
  On{}
type RefreshPair is Data:
  RefreshPair{left: Flag, right: Flag}

def project(p: RefreshPair) -> Flag:
  match p:
    case RefreshPair{left,right}: left
def main() -> Flag:
  project(RefreshPair{On{},Off{}})
