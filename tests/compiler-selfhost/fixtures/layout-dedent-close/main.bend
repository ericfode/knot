# A dedented `name)` line closing a call whose earlier argument spans lines
# (src/driver.bend:33-37), and a bare dedented `)`.
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

def gate(a: Answer, b: Answer, c: Answer) -> Answer:
  both(
    either(
      flip(a),
      b),
    c)

def bare(a: Answer, b: Answer) -> Answer:
  either(
    flip(a),
    b
  )

def main() -> Answer:
  gate(Yes{},No{},Yes{})
