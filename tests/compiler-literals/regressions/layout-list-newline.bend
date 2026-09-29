import Base

# Inside `(..)` and `{..}` a line break, a blank line or a comment line may stand around any
# item: in calls, constructor values and patterns, parameter lists and constructor fields.
type Answer is Type:
  No{}
  Yes{}

type Probe is Data:
  Low{}
  High{}

type Couple is Type:
  Couple{
    left: Answer,
    right: Answer
  }

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def both(
  a: Answer,
  b: Answer
) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def meet(c: Couple) -> Answer:
  match c:
    case Couple{
      l,
      r
    }: both(l, r)

def word(p: Probe) -> U32:
  match p:
    case Low{}: 0
    case High{}: 2

def lists(+p: Probe,
  -q: Probe) -> Answer:
  meet(Couple{
    answer(U32.is_eq(
      word(p),
      2)),
    # a comment line between items

    answer(Nat.is_eq(1n,
      1n))
  })

def probe(+p: Probe) -> Answer:
  lists(p, Low{})

def main() -> Answer:
  probe(High{})
