# Twin of layout-def-header: a doubled comma on the header's continuation line.
type Answer is Data:
  No{}
  Yes{}

def gate(+a: Answer, b: Answer,
  c: Answer,,
  d: Answer) -> Answer:
  match a:
    case No{}: b
    case Yes{}: c

def main() -> Answer:
  gate(No{},Yes{},No{},No{})
