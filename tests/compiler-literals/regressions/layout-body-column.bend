import Base

# The seed checks no body column: an arm body may start left of its `case`, even in column 0,
# and a let's next line may stand in any column. A match in a dedented body still takes only
# the cases right of the enclosing `case`.
type Answer is Type:
  No{}
  Yes{}

type Probe is Data:
  Low{}
  High{}

def size(p: Probe) -> Nat:
  match p:
    case Low{}: 0n
    case High{}: 3n

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def own_line(n: Nat) -> Answer:
  match n:
    case 0n:
  No{}
    case 1n+p: Yes{}

def tail_line(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+
p: Yes{}

def column_zero(n: Nat) -> Answer:
  match n:
    case 0n:
No{}
    case 1n+p:
Yes{}

def let_chain(n: Nat) -> Answer:
  match n:
    case 0n:
  a : Answer = No{}
      b : Answer = a
  b
    case 1n+p:
      c : Answer = Yes{}
    c

def inner(n: Nat, m: Nat) -> Answer:
  match n:
    case 0n:
  match m:
      case 0n: No{}
      case 1n+q: Yes{}
    case 1n+p: Yes{}

def bodies(+p: Probe) -> Answer:
  both(own_line(size(p)), both(tail_line(size(p)), both(column_zero(size(p)), both(let_chain(size(p)), inner(size(p), size(p))))))

def main() -> Answer:
  bodies(High{})
