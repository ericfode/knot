type Flag is Data:
  Off{}
  On{}
type Pack is Type:
  Pack{-ghost: Flag, value: Flag}
def again(x: Pack) -> Pack:
  match x:
    case Pack{g,v}:
      x
def read(x: Pack) -> Flag:
  match x:
    case Pack{g,v}:
      v
def main() -> Flag:
  read(again(Pack{Off{},On{}}))
