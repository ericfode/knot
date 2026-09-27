# A nested constructor pattern on an erased field would inspect it live.
type Flag is Data:
  Off{}
  On{}

type Tag is Type:
  Tag{-ghost: Flag, live: Flag}

type Box is Type:
  Box{t: Tag}

def open(x: Box) -> Flag:
  match x:
    case Box{Tag{On{}, v}}: v
    case Box{Tag{Off{}, v}}: Off{}

def main() -> Flag:
  open(Box{Tag{On{}, On{}}})
