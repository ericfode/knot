type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
type Tree is Data:
  Leaf{}
  Fork{left: Tree, right: Tree}
def drain(t: Tree) -> Flag:
  match t:
    case Fork{Fork{a,b},c}:
      copy : Tree = Fork{a,b}
      drain(copy)
    case _: On{}
def main() -> Flag:
  drain(Fork{Fork{Leaf{},Leaf{}},Leaf{}})
