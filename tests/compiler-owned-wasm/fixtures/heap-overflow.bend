type Flag is Data:
  Off{}
  On{}
type Tree is Type:
  Leaf{value: Flag}
  Fork{left: Tree, right: Tree}
def discard(tree: Tree) -> Flag:
  On{}
def f0() -> Tree:
  Leaf{On{}}
def f1() -> Tree:
  Fork{f0(),f0()}
def f2() -> Tree:
  Fork{f1(),f1()}
def f3() -> Tree:
  Fork{f2(),f2()}
def f4() -> Tree:
  Fork{f3(),f3()}
def f5() -> Tree:
  Fork{f4(),f4()}
def f6() -> Tree:
  Fork{f5(),f5()}
def f7() -> Tree:
  Fork{f6(),f6()}
def f8() -> Tree:
  Fork{f7(),f7()}
def f9() -> Tree:
  Fork{f8(),f8()}
def f10() -> Tree:
  Fork{f9(),f9()}
def f11() -> Tree:
  Fork{f10(),f10()}
def f12() -> Tree:
  Fork{f11(),f11()}
def main() -> Flag:
  discard(f12())
