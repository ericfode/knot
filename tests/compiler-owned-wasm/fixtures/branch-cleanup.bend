type Flag is Data:
  Off{}
  On{}
type Value is Data:
  Value{value: Flag}
def read(value: Value) -> Flag:
  match value:
    case Value{v}: v
def choose(flag: Flag, +value: Value) -> Flag:
  match flag:
    case Off{}: read(value)
    case On{}: On{}
def observe(flag: Flag) -> Flag:
  choose(flag,Value{Off{}})
def main() -> Flag:
  observe(On{})
