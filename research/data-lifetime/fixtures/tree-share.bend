type Atom is Data:
  Nine{}
  Eleven{}
type Tree is Data:
  Tip{value: Atom}
  Fork{left: Tree, right: Tree}
def duplicate(+tree: Tree) -> Tree:
  Fork{tree,tree}
def main() -> Tree:
  duplicate(Fork{Tip{Nine{}},Tip{Eleven{}}})
