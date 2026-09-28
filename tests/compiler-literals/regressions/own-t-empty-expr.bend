# Without Base, `""` against T spells T's own SNil.
type Answer is Type:
  No{}
  Yes{}

type Ch is Data:
  C{}

type T is Data:
  SNil{}
  SCon{head: Ch, tail: T}

def empty() -> T:
  ""

def is_empty(s: T) -> Answer:
  match s:
    case SNil{}: Yes{}
    case SCon{h, t}: No{}

def main() -> Answer:
  is_empty(empty())
