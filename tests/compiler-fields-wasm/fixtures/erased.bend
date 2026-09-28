type Flag is Data:
  Off{}
  On{}
type Pack is Type:
  Empty{}
  Ghost{-ghost: Flag}
  Pack{-ghost: Flag, left: Flag, -phantom: Flag, +right: Flag}
def read(x: Pack) -> Flag:
  match x:
    case Empty{}:
      Off{}
    case Ghost{g}:
      On{}
    case Pack{g,a,p,b}:
      b
def empty() -> Flag:
  read(Empty{})
def ghost() -> Flag:
  read(Ghost{Off{}})
def observe(a: Flag, b: Flag) -> Flag:
  read(Pack{On{},a,Off{},b})
def main() -> Flag:
  read(Pack{later(),Off{},On{},On{}})
def later() -> Flag:
  Off{}
