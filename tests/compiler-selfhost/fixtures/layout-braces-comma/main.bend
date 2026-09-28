# Twin of layout-braces: a doubled comma in a pattern's continuation line.
type Answer is Data:
  No{}
  Yes{}

type Couple is Data:
  Couple{left: Answer, right: Answer}

def right(p: Couple) -> Answer:
  match p:
    case Couple{
      left,,
      right}:
      right

def main() -> Answer:
  right(Couple{No{},Yes{}})
