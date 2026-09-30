# An erased field under a nested pattern is skipped or bound, then used only in an erased field.
type Flag is Data:
  Off{}
  On{}

type Tag is Type:
  Tag{-ghost: Flag, live: Flag}

type Box is Type:
  Box{t: Tag}

def live(t: Tag) -> Flag:
  match t:
    case Tag{_, v}: v

def open(x: Box) -> Flag:
  match x:
    case Box{Tag{_, On{}}}: Off{}
    case Box{Tag{g, Off{}}}: live(Tag{g, On{}})

def probe(g: Flag, v: Flag) -> Flag:
  open(Box{Tag{g, v}})

def main() -> Flag:
  probe(On{}, Off{})
