# Without Base, `""` against the book's own String spells its own SNil.
type Answer is Type:
  No{}
  Yes{}

type Char is Data:
  Chr{}

type String is Data:
  SNil{}
  SCon{head: Char, tail: String}

def empty() -> String:
  ""

def is_empty(s: String) -> Answer:
  match s:
    case SNil{}: Yes{}
    case SCon{h, t}: No{}

def main() -> Answer:
  is_empty(empty())
