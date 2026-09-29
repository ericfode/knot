import Base

# A line break may follow `case`, `match` or a let's `=`, and may precede the `:` that closes
# a case pattern or a match scrutinee: the seed reads a term after skipping line breaks.
type Answer is Type:
  No{}
  Yes{}

type Probe is Data:
  Low{}
  High{}

def flag(p: Probe) -> Bool:
  match p:
    case Low{}: False{}
    case High{}: True{}

def count(p: Probe) -> Nat:
  match p:
    case Low{}: 0n
    case High{}: 1n

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def after_case(b: Bool) -> Answer:
  match b:
    case
      False{}: No{}
    case True{}
      : Yes{}

def after_match(b: Bool) -> Answer:
  match
    b
    :
    case False{}: No{}
    case True{}: Yes{}

def after_promotion(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case
      +p: Yes{}

def after_equals(+p: Probe) -> Answer:
  a : Answer =
    after_case(flag(p))
  c =
    after_match(flag(p))
  +d : Nat =

    1n
  both(a, both(c, after_promotion(Nat.mul(d, Nat.mul(d, count(p))))))

def terms(+p: Probe) -> Answer:
  both(after_equals(p), after_case(flag(p)))

def main() -> Answer:
  terms(High{})
