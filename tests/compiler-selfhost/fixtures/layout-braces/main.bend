# Newlines inside {..}: a constructor split after { and , (src/lex.bend:62-63)
# and a pattern split the same way.
type Answer is Data:
  No{}
  Yes{}

type Couple is Data:
  Couple{left: Answer, right: Answer}

type Triple is Data:
  Triple{first: Answer, middle: Couple, last: Answer}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def build(a: Answer, +b: Answer, +c: Answer) -> Triple:
  Triple{a,Couple{
    b,
    c},
    both(b,c)}

def middle(t: Triple) -> Answer:
  match t:
    case Triple{
      first,
      Couple{left,right},
      last}:
      both(first,both(right,last))

def probe(a: Answer, b: Answer, c: Answer) -> Answer:
  middle(build(a,b,c))

def main() -> Answer:
  probe(Yes{},Yes{},Yes{})
