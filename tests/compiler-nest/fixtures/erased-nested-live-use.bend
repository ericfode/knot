# A binder for an erased field, bound two constructors deep, is returned live.
type Flag is Data:
  Off{}
  On{}

type Tag is Type:
  Tag{-ghost: Flag, live: Flag}

type Box is Type:
  Box{t: Tag}

def open(x: Box) -> Flag:
  match x:
    case Box{Tag{g, v}}: g

def main() -> Flag:
  open(Box{Tag{On{}, On{}}})
