type Flag is Data:
  Off{}
  On{}
type Choice is Type:
  One{value: Flag}
  Empty{}
def read(x: Choice) -> Flag:
  match x:
    case One{v}:
      v
def main() -> Flag:
  read(One{On{}})
