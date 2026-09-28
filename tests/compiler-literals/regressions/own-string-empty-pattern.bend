# Without Base, `""` spells this book's own SNil.
type Answer is Type:
  No{}
  Yes{}

type Char is Data:
  Chr{}

type String is Data:
  SNil{}
  SCon{head: Char, tail: String}

def empty(s: String) -> Answer:
  match s:
    case "": Yes{}
    case _: No{}

def main() -> Answer:
  empty(SNil{})
