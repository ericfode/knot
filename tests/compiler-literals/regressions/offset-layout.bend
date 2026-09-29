import Base

# An offset's `+` ends its token. Its tail follows after a space, a newline, a comment or a
# blank line, as the seed reads it, in patterns and in expressions.
type Answer is Type:
  No{}
  Yes{}

type Size is Type:
  Empty{}
  Three{}

def size(s: Size) -> Nat:
  match s:
    case Empty{}: 0n
    case Three{}: 3n

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def newline(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+
      p: Yes{}

def comment(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+ # the tail follows
      p: Yes{}

def blank(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+

      # between
      p: Yes{}

def promoted(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+
      +p: Yes{}

def stacked(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n: No{}
    case 1n+
      1n+
      p: Yes{}

def more(p: Nat) -> Nat:
  1n+
  p

def commented(p: Nat) -> Nat:
  2n+ # two successors
  p

def dedent(p: Nat) -> Nat:
  1n+
p

def layouts(+n: Nat) -> Answer:
  both(newline(n), both(comment(n), both(blank(n), promoted(n))))

def patterns(s: Size) -> Answer:
  layouts(size(s))

def nested(s: Size) -> Answer:
  stacked(size(s))

def expressions(s: Size) -> Answer:
  answer(Nat.is_eq(more(commented(dedent(size(s)))), 7n))

def main() -> Answer:
  patterns(Three{})
