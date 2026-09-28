type Atom is Data:
  Nine{}
  Eleven{}
type Leaf is Data:
  Leaf{value: Atom}
type Pair is Data:
  Pair{left: Leaf, right: Leaf}
type Result is Data:
  Result{leaf: Leaf, pair: Pair}
def split(pair: Pair) -> Leaf:
  match pair:
    case Pair{left,right}: left
def preserve(+pair: Pair) -> Result:
  Result{split(pair),pair}
def main() -> Result:
  +leaf: Leaf = Leaf{Nine{}}
  preserve(Pair{leaf,leaf})
