# Twin of layout-comments: a trailing comment swallows the closing brace.
type Answer is Data:
  No{}
  Yes{}

type Couple is Data:
  Couple{left: Answer, right: Answer}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def flip(a: Answer) -> Answer:
  match a:
    case No{}: Yes{}
    case Yes{}: No{}

def pack(a: Answer, b: Answer) -> Couple:
  Couple{
    # the left field keeps its argument

    a,
    # the right field inverts it
    flip(b) # }

def meet(p: Couple) -> Answer:
  match p:
    case Couple{left,right}: both(left,right)

def gate(a: Answer, b: Answer) -> Answer:
  meet(pack(a,b))

def main() -> Answer:
  gate(Yes{},No{})
