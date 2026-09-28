# Twin of layout-call-args: a doubled comma on a continuation line.
type Answer is Data:
  No{}
  Yes{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def either(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: b
    case Yes{}: Yes{}

def gate(+a: Answer, +b: Answer, +c: Answer) -> Answer:
  either(both(a,b),either(
    both(a,c),,
    both(b,c)))

def main() -> Answer:
  gate(No{},Yes{},No{})
