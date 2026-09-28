type Flag is Data:
  Off{}
  On{}
type Value is Data:
  Value{value: Flag}
type Pair is Data:
  Pair{left: Value, right: Value}
def read(value: Value) -> Flag:
  match value:
    case Value{v}: v
def preserve(+value: Value) -> Pair:
  unused = read(value)
  Pair{Value{On{}},value}
def main() -> Pair:
  preserve(Value{Off{}})
