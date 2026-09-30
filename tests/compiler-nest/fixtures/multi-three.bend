# Three scrutinees with wildcards; the result names the first agreeing pair.
type Flag is Data:
  Off{}
  On{}

type Agree is Data:
  AB{}
  AC{}
  BC{}
  Split{}

def major(a: Flag, b: Flag, c: Flag) -> Agree:
  match a b c:
    case On{} On{} _: AB{}
    case On{} _ On{}: AC{}
    case _ On{} On{}: BC{}
    case _ _ _: Split{}

def main() -> Agree:
  major(Off{}, On{}, On{})
