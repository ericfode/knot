type Flag is Data:
  Off{}
  On{}
type Pack is Type:
  Pack{-ghost: Flag, left: Flag, -phantom: Flag, +right: Flag}
def read(x: Pack) -> Flag:
  match x:
    case Pack{a,b,c,d}:
      d
def main() -> Flag:
  read(Pack{Off{},Off{},On{},On{}})
