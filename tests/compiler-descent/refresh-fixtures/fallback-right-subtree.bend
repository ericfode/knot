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
    case Fork{a,Fork{b,c}}: drain(Fork{b,c})
    case _: On{}
def main() -> Flag:
  drain(Fork{Leaf{},Fork{Leaf{},Fork{Leaf{},Leaf{}}}})
