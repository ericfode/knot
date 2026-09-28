# Multi-line def parameter lists in Knot's shape (src/lex.bend:12-13,
# src/catalog.bend:150-151): a trailing comma, then a continuation indented
# to the body column, with quantity binders on both lines.
type Answer is Data:
  No{}
  Yes{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def flip(a: Answer) -> Answer:
  match a:
    case No{}: Yes{}
    case Yes{}: No{}

def gate(+a: Answer, b: Answer,
  +c: Answer) -> Answer:
  match a:
    case No{}: both(b,c)
    case Yes{}: flip(c)

def chain(a: Answer, +b: Answer,
  c: Answer, d: Answer,
  +e: Answer) -> Answer:
  gate(a,both(b,e),both(flip(c),both(d,b)))

def main() -> Answer:
  chain(No{},Yes{},No{},Yes{},Yes{})
