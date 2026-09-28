# Twin of layout-dedent-close: the dedented `name)` line closes one call too many.
type Answer is Data:
  No{}
  Yes{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def gate(a: Answer, b: Answer, c: Answer) -> Answer:
  both(
    both(
      a,
      b),
    c))

def main() -> Answer:
  gate(Yes{},No{},Yes{})
