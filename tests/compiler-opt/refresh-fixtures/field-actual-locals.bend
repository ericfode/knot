type Flag is Data:
  Off{}
  On{}
type RefreshPair is Data:
  RefreshPair{left: Flag, right: Flag}

def local(x: Flag) -> Flag:
  copy : Flag = x
  copy
def project(p: RefreshPair) -> Flag:
  match p:
    case RefreshPair{left,right}: right
def main() -> Flag:
  project(RefreshPair{local(Off{}),local(On{})})
