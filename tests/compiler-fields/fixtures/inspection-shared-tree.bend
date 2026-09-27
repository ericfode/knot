type Tree is Data:
  Leaf{}
  Fork{left: Tree, right: Tree}
def twice(+x: Tree) -> Tree:
  Fork{x,x}
def main() -> Tree:
  twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(twice(Leaf{}))))))))))))))))))))))))
