# The spelling is by constructor, not by type name: here the type is T.
type Answer is Type:
  No{}
  Yes{}

type Ch is Data:
  C{}

type T is Data:
  SNil{}
  SCon{head: Ch, tail: T}

def empty(s: T) -> Answer:
  match s:
    case "": Yes{}
    case _: No{}

def main() -> Answer:
  empty(SNil{})
