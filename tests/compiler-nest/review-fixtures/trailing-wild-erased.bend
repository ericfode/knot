# A wildcard after complete constructor rows uses an erased field live.
type Flag is Data:
  Off{}
  On{}

type Tag is Type:
  Tag{-g: Flag, v: Flag}

def f(t: Tag) -> Flag:
  match t:
    case Tag{_, On{}}: On{}
    case Tag{_, Off{}}: Off{}
    case Tag{g, _}: g

def probe(a: Flag, b: Flag) -> Flag:
  f(Tag{a, b})

def main() -> Flag:
  probe(On{}, Off{})
