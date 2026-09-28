import Base

# Doubling reaches 131072 Chars in 17 appends, far past source recursion.
type Answer is Type:
  No{}
  Yes{}

type Depth is Type:
  Low{}
  High{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def steps(d: Depth) -> Nat:
  match d:
    case Low{}: 16n
    case High{}: 17n

def double(k: Nat, +t: String) -> String:
  match k:
    case 0n: t
    case 1n+p: double(p, String.append(t, t))

def length(d: Depth) -> Answer:
  answer(Nat.is_eq(String.length(double(steps(d), "x")), 131072n))

def palindrome(+t: String) -> Answer:
  answer(String.eq(t, String.reverse(t)))

def mirrored(d: Depth) -> Answer:
  palindrome(double(steps(d), "xy"))

def main() -> Answer:
  length(High{})
