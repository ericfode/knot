type Flag is Data:
  Off{}
  On{}

type Trit is Data:
  Zero{}
  One{}
  Two{}

def pick(a: Flag, b: Trit) -> Flag:
  match a:
    case On{}:
      match b:
        case Two{}: On{}
        case One{}: Off{}
        case Zero{}: On{}
    case Off{}: Off{}

def main() -> Flag:
  pick(On{},One{})
