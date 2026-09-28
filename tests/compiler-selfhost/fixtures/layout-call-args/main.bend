# Continuation lines after ( and , in call arguments, in the shape of
# src/syntax.bend:56-58: the last argument call opens a new line.
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

def flip(a: Answer) -> Answer:
  match a:
    case No{}: Yes{}
    case Yes{}: No{}

def gate(+a: Answer, +b: Answer, +c: Answer) -> Answer:
  either(both(a,b),either(
    both(flip(a),c),
    both(flip(b),flip(c))))

def main() -> Answer:
  gate(No{},Yes{},No{})
