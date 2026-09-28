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

type OptObservation is Data:
  OptMismatch{}
  OptMatch{}
def opt_and(a: OptObservation, b: OptObservation) -> OptObservation:
  match a:
    case OptMismatch{}: OptMismatch{}
    case OptMatch{}:
      match b:
        case OptMismatch{}: OptMismatch{}
        case OptMatch{}: OptMatch{}
def opt_off(x: Flag) -> OptObservation:
  match x:
    case Off{}: OptMatch{}
    case On{}: OptMismatch{}
def opt_on(x: Flag) -> OptObservation:
  match x:
    case Off{}: OptMismatch{}
    case On{}: OptMatch{}
def opt_leaf_off(x: Tree) -> OptObservation:
  match x:
    case Leaf{v}: opt_off(v)
    case Fork{left,right}: OptMismatch{}
def opt_leaf_on(x: Tree) -> OptObservation:
  match x:
    case Leaf{v}: opt_on(v)
    case Fork{left,right}: OptMismatch{}
def opt_inner(x: Tree) -> OptObservation:
  match x:
    case Leaf{v}: OptMismatch{}
    case Fork{left,right}: opt_and(opt_leaf_off(left),opt_leaf_on(right))
def opt_exact(x: Tree) -> OptObservation:
  match x:
    case Leaf{v}: OptMismatch{}
    case Fork{left,right}: opt_and(opt_inner(left),opt_leaf_off(right))
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Leaf{Off{}})
