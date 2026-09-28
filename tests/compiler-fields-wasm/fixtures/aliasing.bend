type Flag is Data:
  Off{}
  On{}
type Box is Type:
  Box{value: Flag}
def first(x: Box, y: Box) -> Flag:
  match x:
    case Box{v}:
      v
def observe(a: Flag, b: Flag) -> Flag:
  first(Box{a},Box{b})
def main() -> Flag:
  observe(Off{},On{})
