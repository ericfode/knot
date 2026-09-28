type Flag is Data:
  Off{}
  On{}
type Tree is Type:
  Leaf{value: Flag}
  Fork{left: Tree, right: Tree}
def mirror(tree: Tree) -> Tree:
  match tree:
    case Leaf{value}: Leaf{value}
    case Fork{left,right}: Fork{mirror(right),mirror(left)}
def main() -> Tree:
  mirror(Fork{Leaf{Off{}},Fork{Leaf{On{}},Leaf{Off{}}}})

type CObservation is Data:
  CNo{}
  CYes{}
def c_all(a: CObservation, b: CObservation) -> CObservation:
  match a:
    case CNo{}: CNo{}
    case CYes{}: b
def c_literal_0(value: Flag) -> CObservation:
  match value:
    case Off{}:
      CYes{}
    case On{}:
      CNo{}
def c_literal_1(value: Tree) -> CObservation:
  match value:
    case Leaf{f0}:
      c_all(c_literal_0(f0),CYes{})
    case Fork{f0,f1}:
      CNo{}
def c_literal_2(value: Flag) -> CObservation:
  match value:
    case Off{}:
      CNo{}
    case On{}:
      CYes{}
def c_literal_3(value: Tree) -> CObservation:
  match value:
    case Leaf{f0}:
      c_all(c_literal_2(f0),CYes{})
    case Fork{f0,f1}:
      CNo{}
def c_literal_4(value: Tree) -> CObservation:
  match value:
    case Leaf{f0}:
      CNo{}
    case Fork{f0,f1}:
      c_all(c_literal_1(f0),c_all(c_literal_3(f1),CYes{}))
def c_literal_5(value: Tree) -> CObservation:
  match value:
    case Leaf{f0}:
      CNo{}
    case Fork{f0,f1}:
      c_all(c_literal_4(f0),c_all(c_literal_1(f1),CYes{}))
def c_observe() -> CObservation:
  c_literal_5(main())
