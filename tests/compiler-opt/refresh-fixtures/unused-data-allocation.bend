type Flag is Data:
  Off{}
  On{}
type RefreshPair is Data:
  RefreshPair{left: Flag, right: Flag}

def main() -> Flag:
  +unused : RefreshPair = RefreshPair{On{},Off{}}
  On{}
