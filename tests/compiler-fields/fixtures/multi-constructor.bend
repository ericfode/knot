type Flag is Data:
  Off{}
  On{}
type Choice is Type:
  Empty{}
  One{value: Flag}
  Two{left: Flag, right: Flag}
def pick(x: Choice) -> Flag:
  match x:
    case Two{a,b}:
      b
    case Empty{}:
      Off{}
    case One{v}:
      v
def main() -> Flag:
  pick(Two{Off{},On{}})
